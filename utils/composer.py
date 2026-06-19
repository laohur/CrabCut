import subprocess
from pathlib import Path
from datetime import datetime
from utils.log_config import logger, log_cmd, log_subprocess
from utils.metadata import get_media_metadata
from utils.ffmpeg_utils import FFMPEG_PATH

def get_output_dir():
    from utils.converter import get_output_dir as base_get_output_dir
    return base_get_output_dir()

SUBTITLE_FONTS = {
    "default": "Sans",
    "arial": "Arial",
    "simhei": "SimHei",
    "simsun": "SimSun",
    "microsoftyahei": "Microsoft YaHei",
    "notosanscjk": "Noto Sans CJK SC",
}

def compose_video(
    video_path: str,
    audio_path: str = None,
    audio_volume: float = 1.0,
    video_volume: float = 1.0,
    subtitle_path: str = None,
    subtitle_embed: str = "hard",
    subtitle_font: str = "Sans",
    subtitle_font_size: int = 24,
    subtitle_color: str = "white",
    subtitle_bg_color: str = "black",
    subtitle_bg_opacity: float = 0.5,
    subtitle_outline: int = 2,
    subtitle_outline_color: str = "black",
    subtitle_margin_v: int = 20,
    watermark_path: str = None,
    watermark_position: str = "bottom_right",
    watermark_opacity: float = 0.7,
    text_watermark: str = None,
    text_font_size: int = 24,
    text_color: str = "white",
    output_format: str = "mp4"
) -> dict:
    if not video_path or not Path(video_path).exists():
        return {"success": False, "error": "视频文件不存在 / Video file not found"}
    
    video_path = Path(video_path)
    output_dir = get_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{video_path.stem}_composed-{timestamp}.{output_format}"
    
    video_result = get_media_metadata(video_path.as_posix())
    video_duration = video_result.get("duration", 0) if video_result.get("success") else 0
    has_video_audio = "audio" in video_result if video_result.get("success") else False
    
    input_files = ["-i", video_path.as_posix()]
    input_count = 1
    
    filter_parts = []
    audio_inputs = []
    
    if audio_path and Path(audio_path).exists():
        audio_path = Path(audio_path)
        audio_result = get_media_metadata(audio_path.as_posix())
        audio_duration = audio_result.get("duration", 0) if audio_result.get("success") else 0
        
        if audio_duration < video_duration:
            input_files.extend(["-stream_loop", "-1"])
        input_files.extend(["-i", audio_path.as_posix()])
        input_count += 1
        audio_inputs.append(str(input_count - 1))
    
    video_filter = "[0:v]"
    filter_label = "v0"
    
    has_hard_subtitle = False
    if subtitle_path and Path(subtitle_path).exists() and subtitle_embed == "hard":
        subtitle_path = Path(subtitle_path)
        subtitle_escaped = subtitle_path.as_posix().replace(":", "\\:").replace("'", "\\'")
        
        force_style_parts = []
        if subtitle_font:
            force_style_parts.append(f"FontName={subtitle_font}")
        if subtitle_font_size:
            force_style_parts.append(f"FontSize={subtitle_font_size}")
        if subtitle_color:
            color_hex = subtitle_color.lstrip('#')
            force_style_parts.append(f"PrimaryColour=&H{color_hex}&")
        if subtitle_outline:
            force_style_parts.append(f"Outline={subtitle_outline}")
        if subtitle_outline_color:
            outline_hex = subtitle_outline_color.lstrip('#')
            force_style_parts.append(f"OutlineColour=&H{outline_hex}&")
        if subtitle_margin_v:
            force_style_parts.append(f"MarginV={subtitle_margin_v}")
        
        if subtitle_bg_color and subtitle_bg_opacity > 0:
            bg_hex = subtitle_bg_color.lstrip('#')
            bg_alpha = int((1 - subtitle_bg_opacity) * 255)
            force_style_parts.append(f"BackColour=&H{bg_alpha:02x}{bg_hex}&")
            force_style_parts.append("BorderStyle=4")
        
        force_style = ",".join(force_style_parts)
        
        if force_style:
            filter_parts.append(f"[{filter_label}]subtitles='{subtitle_escaped}':force_style='{force_style}'[v_sub]")
        else:
            filter_parts.append(f"[{filter_label}]subtitles='{subtitle_escaped}'[v_sub]")
        filter_label = "v_sub"
        has_hard_subtitle = True
    
    if watermark_path and Path(watermark_path).exists():
        watermark_path = Path(watermark_path)
        input_files.extend(["-i", watermark_path.as_posix()])
        input_count += 1
        wm_idx = input_count - 1
        
        position_map = {
            "top_left": "10:10",
            "top_right": "W-w-10:10",
            "bottom_left": "10:H-h-10",
            "bottom_right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2",
        }
        overlay_pos = position_map.get(watermark_position, "W-w-10:H-h-10")
        
        filter_parts.append(f"[{wm_idx}:v]format=rgba,colorchannelmixer=aa={watermark_opacity}[wm]")
        filter_parts.append(f"[{filter_label}][wm]overlay={overlay_pos}[v_wm]")
        filter_label = "v_wm"
    elif text_watermark:
        position_map = {
            "top_left": "x=10:y=10",
            "top_right": "x=W-tw-10:y=10",
            "bottom_left": "x=10:y=H-th-10",
            "bottom_right": "x=W-tw-10:y=H-th-10",
            "center": "x=(W-tw)/2:y=(H-th)/2",
        }
        pos_params = position_map.get(watermark_position, "x=W-tw-10:y=H-th-10")
        alpha = format(watermark_opacity, ".2f")
        text_escaped = text_watermark.replace("'", "\\'").replace(":", "\\:")
        draw_text = f"drawtext=text='{text_escaped}':fontsize={text_font_size}:fontcolor={text_color}@{alpha}:{pos_params}"
        filter_parts.append(f"[{filter_label}]{draw_text}[v_wm]")
        filter_label = "v_wm"
    
    if filter_parts:
        filter_parts[-1] = filter_parts[-1].replace(f"[{filter_label}]", "[vout]")
        filter_complex = ";".join(filter_parts)
    else:
        filter_complex = None
    
    audio_filter_parts = []
    
    if audio_path and Path(audio_path).exists() and has_video_audio:
        audio_filter_parts.append(f"[0:a]volume={video_volume}[vaudio]")
        audio_filter_parts.append(f"[1:a]volume={audio_volume}[aaudio]")
        audio_filter_parts.append("[vaudio][aaudio]amix=inputs=2:duration=first:dropout_transition=2[aout]")
    elif audio_path and Path(audio_path).exists():
        audio_filter_parts.append(f"[1:a]volume={audio_volume}[aout]")
    elif has_video_audio:
        audio_filter_parts.append(f"[0:a]volume={video_volume}[aout]")
    
    if filter_complex and audio_filter_parts:
        filter_complex = filter_complex + ";" + ";".join(audio_filter_parts)
    elif audio_filter_parts:
        filter_complex = ";".join(audio_filter_parts)
    
    cmd = [FFMPEG_PATH, "-y"]
    cmd.extend(input_files)
    
    if filter_complex:
        cmd.extend(["-filter_complex", filter_complex])
    
    if filter_parts:
        cmd.extend(["-map", "[vout]"])
    else:
        cmd.extend(["-map", "0:v"])
    
    if audio_filter_parts:
        cmd.extend(["-map", "[aout]"])
    elif has_video_audio:
        cmd.extend(["-map", "0:a"])
    
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
    ])
    
    has_soft_subtitle = False
    if subtitle_path and Path(subtitle_path).exists() and subtitle_embed == "soft":
        subtitle_path = Path(subtitle_path)
        cmd.extend(["-i", subtitle_path.as_posix()])
        cmd.extend(["-c:s", "mov_text"])
        cmd.extend(["-map", f"{input_count}:s"])
        has_soft_subtitle = True
    
    if audio_path and Path(audio_path).exists():
        cmd.append("-shortest")
    
    cmd.append(output_path.as_posix())
    
    logger.info(f"开始合成视频: {video_path.as_posix()}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"视频合成成功: {output_path.as_posix()}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "video_duration": video_duration,
        "subtitle_embed": subtitle_embed if subtitle_path else None,
        "cmd": cmd,
    }

__all__ = ["compose_video", "SUBTITLE_FONTS"]
