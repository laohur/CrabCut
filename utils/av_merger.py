import subprocess
from pathlib import Path
from datetime import datetime
from utils.log_config import logger, log_cmd, log_subprocess
from utils.metadata import get_media_metadata
from utils.ffmpeg_utils import FFMPEG_PATH

def get_output_dir():
    from utils.converter import get_output_dir as base_get_output_dir
    return base_get_output_dir()

def merge_audio_video(video_path: str, audio_path: str, output_format: str = "mp4", audio_volume: float = 1.0, video_volume: float = 0.0) -> dict:
    if not video_path or not Path(video_path).exists():
        return {"success": False, "error": "视频文件不存在 / Video file not found"}
    if not audio_path or not Path(audio_path).exists():
        return {"success": False, "error": "音频文件不存在 / Audio file not found"}
    
    output_dir = get_output_dir()
    video_path = Path(video_path)
    audio_path = Path(audio_path)
    video_name = video_path.stem
    audio_name = audio_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{video_name}_{audio_name}_merged-{timestamp}.{output_format}"
    
    video_result = get_media_metadata(video_path.as_posix())
    video_duration = video_result.get("duration", 0) if video_result.get("success") else 0
    
    audio_result = get_media_metadata(audio_path.as_posix())
    audio_duration = audio_result.get("duration", 0) if audio_result.get("success") else 0
    
    filter_parts = []
    
    if video_volume <= 0:
        filter_parts.append("[0:a]volume=0[vaudio]")
    else:
        filter_parts.append(f"[0:a]volume={video_volume}[vaudio]")
    
    filter_parts.append(f"[1:a]volume={audio_volume}[aaudio]")
    
    filter_parts.append("[vaudio][aaudio]amix=inputs=2:duration=first:dropout_transition=2[aout]")
    
    filter_complex = ";".join(filter_parts)
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path.as_posix(),
        "-i", audio_path.as_posix(),
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path.as_posix()
    ]
    
    logger.info(f"开始合并音视频: {video_path} + {audio_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"音视频合并成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "video_duration": video_duration,
        "audio_duration": audio_duration,
        "cmd": cmd,
    }

def replace_audio(video_path: str, audio_path: str, output_format: str = "mp4") -> dict:
    if not video_path or not Path(video_path).exists():
        return {"success": False, "error": "视频文件不存在 / Video file not found"}
    if not audio_path or not Path(audio_path).exists():
        return {"success": False, "error": "音频文件不存在 / Audio file not found"}
    
    output_dir = get_output_dir()
    video_path = Path(video_path)
    audio_path = Path(audio_path)
    video_name = video_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{video_name}_replaced-{timestamp}.{output_format}"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path.as_posix(),
        "-i", audio_path.as_posix(),
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path.as_posix()
    ]
    
    logger.info(f"开始替换音频: {video_path} -> {audio_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"音频替换成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "cmd": cmd,
    }

def add_background_music(video_path: str, audio_path: str, output_format: str = "mp4", audio_volume: float = 0.5, loop_audio: bool = True) -> dict:
    if not video_path or not Path(video_path).exists():
        return {"success": False, "error": "视频文件不存在 / Video file not found"}
    if not audio_path or not Path(audio_path).exists():
        return {"success": False, "error": "音频文件不存在 / Audio file not found"}
    
    output_dir = get_output_dir()
    video_path = Path(video_path)
    audio_path = Path(audio_path)
    video_name = video_path.stem
    audio_name = audio_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{video_name}_bgm-{timestamp}.{output_format}"
    
    video_result = get_media_metadata(video_path.as_posix())
    video_duration = video_result.get("duration", 0) if video_result.get("success") else 0
    
    audio_result = get_media_metadata(audio_path.as_posix())
    audio_duration = audio_result.get("duration", 0) if audio_result.get("success") else 0
    
    audio_input = ["-i", audio_path.as_posix()]
    if loop_audio and audio_duration < video_duration:
        audio_input = ["-stream_loop", "-1", "-i", audio_path.as_posix()]
    
    filter_complex = f"[1:a]volume={audio_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path.as_posix(),
        *audio_input,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path.as_posix()
    ]
    
    logger.info(f"开始添加背景音乐: {video_path} + {audio_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"背景音乐添加成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "video_duration": video_duration,
        "audio_duration": audio_duration,
        "cmd": cmd,
    }

__all__ = ["merge_audio_video", "replace_audio", "add_background_music"]
