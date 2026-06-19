import json
import tempfile
from pathlib import Path
from config import get_output_dir
from utils.log_config import logger, log_cmd
from utils.ffmpeg_utils import FFMPEG_PATH, FFPROBE_PATH
from utils.asr import asr_single_file, asr_faster_whisper, ALL_ASR_MODELS, load_json_result
import subprocess


def auto_cut_speaking(
    file_path: str,
    asr_model: str = "whisper-large-v3-turbo",
    use_punc: bool = True,
    padding: float = 0.1,
    merge_gap: float = 1.0,
    language: str = "auto",
) -> dict:
    if not file_path or not Path(file_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}

    file_path = Path(file_path)

    logger.info(f"开始口播自动剪切: {file_path.name}, ASR={asr_model}, padding={padding}s")

    original_duration = _get_duration(str(file_path))

    model_info = ALL_ASR_MODELS.get(asr_model, {})
    engine = model_info.get("engine", "whisper")

    if engine == "whisper":
        asr_result = asr_faster_whisper(
            str(file_path),
            model_size=model_info.get("size", "base"),
            language=language if language != "auto" else None,
        )
    else:
        asr_config = ALL_ASR_MODELS.get(asr_model, ALL_ASR_MODELS["sensevoice"])
        punc_model = asr_config.get("punc") if use_punc else None
        asr_result = asr_single_file(
            str(file_path),
            asr_model=asr_config["asr"],
            vad_model=asr_config.get("vad"),
            punc_model=punc_model,
            language=language if language != "auto" else "auto",
        )

    if not asr_result["success"]:
        return {"success": False, "error": f"ASR 失败: {asr_result.get('error')}"}

    segments = asr_result.get("segments", [])
    if not segments:
        return {"success": False, "error": "ASR 结果为空，无口播片段 / No speech segments found"}

    merged = []
    for seg in segments:
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        if merged and start - merged[-1][1] < merge_gap:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    cut_ranges = []
    for i, (start, end) in enumerate(merged):
        padded_start = start - padding if i > 0 else start
        padded_end = end + padding if i < len(merged) - 1 else end
        padded_start = max(0.0, padded_start)
        cut_ranges.append((padded_start, padded_end))

    cut_total = sum(end - start for start, end in cut_ranges)
    if original_duration > 0 and cut_total / original_duration > 0.95:
        logger.info(f"口播片段覆盖 {cut_total/original_duration*100:.0f}%，无需剪切")
        return {
            "success": True,
            "output": str(file_path),
            "segments": segments,
            "cut_ranges": cut_ranges,
            "original_duration": original_duration,
            "output_duration": original_duration,
            "no_cut_needed": True,
            "from_cache": False,
        }

    logger.info(f"口播片段: {len(cut_ranges)} 段, 合并前 {len(segments)} 段")

    output_dir = get_output_dir()
    output_path = output_dir / f"{file_path.stem}-auto_cut{file_path.suffix}"

    if output_path.exists():
        logger.info(f"输出文件已存在，直接返回: {output_path}")
        output_duration = _get_duration(str(output_path))
        return {
            "success": True,
            "output": str(output_path),
            "segments": segments,
            "cut_ranges": cut_ranges,
            "original_duration": original_duration,
            "output_duration": output_duration,
            "from_cache": True,
        }

    is_video = file_path.suffix.lower() in [".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"]

    temp_dir = Path(tempfile.mkdtemp(prefix="auto_cut_"))
    segment_files = []

    for i, (start, end) in enumerate(cut_ranges):
        seg_path = temp_dir / f"seg_{i:04d}{file_path.suffix}"
        if is_video:
            cmd = [
                FFMPEG_PATH, "-y",
                "-ss", f"{start:.3f}",
                "-to", f"{end:.3f}",
                "-i", str(file_path),
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                "-avoid_negative_ts", "make_zero",
                str(seg_path),
            ]
        else:
            cmd = [
                FFMPEG_PATH, "-y",
                "-i", str(file_path),
                "-ss", f"{start:.3f}",
                "-to", f"{end:.3f}",
                "-c", "copy",
                str(seg_path),
            ]
        log_cmd(cmd)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            logger.error(f"FFmpeg 切段失败 seg[{i}]: {r.stderr[-300:]}")
            continue
        segment_files.append(seg_path)

    if not segment_files:
        return {"success": False, "error": "所有片段剪切失败 / All segments failed"}

    concat_list = temp_dir / "concat.txt"
    concat_lines = [f"file '{seg}'" for seg in segment_files]
    concat_list.write_text("\n".join(concat_lines), encoding="utf-8")

    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
    ]
    if is_video:
        cmd += ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac"]
    else:
        cmd += ["-c", "copy"]
    cmd.append(str(output_path))
    log_cmd(cmd)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg 合并失败: {result.stderr[-500:]}")
        return {"success": False, "error": f"FFmpeg 合并失败: {result.stderr[-200:]}"}

    for seg in segment_files:
        try:
            seg.unlink()
        except Exception:
            pass
    try:
        concat_list.unlink()
        temp_dir.rmdir()
    except Exception:
        pass

    logger.success(f"口播自动剪切完成: {output_path.name}, {len(cut_ranges)} 段")

    output_duration = _get_duration(str(output_path))

    return {
        "success": True,
        "output": str(output_path),
        "segments": segments,
        "cut_ranges": cut_ranges,
        "original_duration": original_duration,
        "output_duration": output_duration,
        "from_cache": False,
    }


def generate_subtitle_files(
    file_path: str,
    segments: list,
    output_formats: list = None,
) -> dict:
    if output_formats is None:
        output_formats = ["srt", "json", "txt"]

    file_path = Path(file_path)
    output_dir = get_output_dir()
    output_stem = f"{file_path.stem}-auto_cut-asr"
    output_files = []

    if "srt" in output_formats:
        srt_path = output_dir / f"{output_stem}.srt"
        srt_lines = []
        for i, seg in enumerate(segments, 1):
            start_sec = seg.get("start", 0)
            end_sec = seg.get("end", 0)
            start_ts = _sec_to_srt_ts(start_sec)
            end_ts = _sec_to_srt_ts(end_sec)
            text = seg.get("text", "")
            srt_lines.append(f"{i}\n{start_ts} --> {end_ts}\n{text}\n")
        srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
        output_files.append(str(srt_path))
        logger.info(f"输出 SRT: {srt_path.name}")

    if "json" in output_formats:
        json_path = output_dir / f"{output_stem}.json"
        json_segments = []
        for i, seg in enumerate(segments, 1):
            json_segments.append({
                "index": i,
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", ""),
            })
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"segments": json_segments}, f, ensure_ascii=False, indent=2)
        output_files.append(str(json_path))
        logger.info(f"输出 JSON: {json_path.name}")

    if "txt" in output_formats:
        txt_path = output_dir / f"{output_stem}.txt"
        txt_lines = [seg.get("text", "") for seg in segments]
        txt_path.write_text("\n".join(txt_lines), encoding="utf-8")
        output_files.append(str(txt_path))
        logger.info(f"输出 TXT: {txt_path.name}")

    return {"success": True, "output_files": output_files}


def _sec_to_srt_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _get_duration(file_path: str) -> float:
    try:
        cmd = [
            FFPROBE_PATH, "-v", "quiet",
            "-show_entries", "stream=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        durations = [float(line.strip()) for line in r.stdout.strip().splitlines() if line.strip()]
        return max(durations) if durations else 0.0
    except Exception:
        return 0.0
