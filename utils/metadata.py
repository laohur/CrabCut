import subprocess
import json
from pathlib import Path
from utils.log_config import logger, log_subprocess, log_cmd
from utils.ffmpeg_utils import FFPROBE_PATH

def get_media_metadata(file_path: str) -> dict:
    if not file_path or not Path(file_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    file_path = Path(file_path)
    cmd = [
        FFPROBE_PATH,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path.as_posix()
    ]
    
    logger.info(f"获取媒体元数据: {file_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffprobe error: {result.stderr}"}
    
    data = json.loads(result.stdout)
    
    format_info = data.get("format", {})
    streams = data.get("streams", [])
    
    metadata = {
        "success": True,
        "filename": format_info.get("filename", ""),
        "format": format_info.get("format_long_name", format_info.get("format_name", "")),
        "duration": float(format_info.get("duration", 0)),
        "size": int(format_info.get("size", 0)),
        "bit_rate": int(format_info.get("bit_rate", 0)),
    }
    
    video_stream = None
    audio_stream = None
    
    for stream in streams:
        codec_type = stream.get("codec_type", "")
        if codec_type == "video" and not video_stream:
            video_stream = stream
        elif codec_type == "audio" and not audio_stream:
            audio_stream = stream
    
    if video_stream:
        metadata["video"] = {
            "codec": video_stream.get("codec_name", ""),
            "codec_long": video_stream.get("codec_long_name", ""),
            "width": video_stream.get("width", 0),
            "height": video_stream.get("height", 0),
            "fps": eval(video_stream.get("r_frame_rate", "0/1")) if "/" in video_stream.get("r_frame_rate", "0") else 0,
            "aspect_ratio": video_stream.get("display_aspect_ratio", ""),
        }
    
    if audio_stream:
        metadata["audio"] = {
            "codec": audio_stream.get("codec_name", ""),
            "codec_long": audio_stream.get("codec_long_name", ""),
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": audio_stream.get("channels", 0),
            "channel_layout": audio_stream.get("channel_layout", ""),
            "bitrate": int(audio_stream.get("bit_rate", 0)),
        }
    
    tags = format_info.get("tags", {})
    if tags:
        metadata["tags"] = tags
    
    return metadata

def format_duration(seconds: float) -> str:
    if not seconds:
        return "0:00:00"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"

def format_size(bytes_size: int) -> str:
    if not bytes_size:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"

def format_bitrate(bitrate: int) -> str:
    if not bitrate:
        return "0 bps"
    if bitrate >= 1000000:
        return f"{bitrate / 1000000:.2f} Mbps"
    elif bitrate >= 1000:
        return f"{bitrate / 1000:.2f} Kbps"
    return f"{bitrate} bps"
