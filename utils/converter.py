import subprocess
from pathlib import Path
from config import get_output_dir
from utils.log_config import logger, log_subprocess, log_cmd
from utils.ffmpeg_utils import FFMPEG_PATH

VIDEO_FORMATS = {
    "mp4": "mp4",
    "avi": "avi",
    "mkv": "mkv",
    "webm": "webm",
    "mov": "mov",
    "flv": "flv",
}

AUDIO_FORMATS = {
    "aac": "aac",
    "mp3": "mp3",
    "wav": "wav",
    "flac": "flac",
    "ogg": "ogg",
    "m4a": "m4a",
}

def get_atempo_filter(speed: float) -> str:
    if speed == 1.0:
        return ""
    
    atempo_filters = []
    remaining_speed = speed
    
    while remaining_speed > 2.0:
        atempo_filters.append("atempo=2.0")
        remaining_speed /= 2.0
    
    while remaining_speed < 0.5:
        atempo_filters.append("atempo=0.5")
        remaining_speed /= 0.5
    
    if remaining_speed != 1.0:
        atempo_filters.append(f"atempo={remaining_speed}")
    
    return ",".join(atempo_filters)

def convert_media(input_path: str, output_format: str, quality: str = "medium", fps: int = 0, audio_bitrate: int = 0, audio_channels: int = 0, speed: float = 1.0, volume: float = 1.0) -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    output_dir = get_output_dir()
    input_path = Path(input_path)
    input_name = input_path.stem
    output_path = output_dir / f"{input_name}.{output_format}"
    
    quality_map = {
        "high": ["-crf", "18"],
        "medium": ["-crf", "23"],
        "low": ["-crf", "28"],
    }
    
    cmd = [FFMPEG_PATH, "-y", "-i", input_path.as_posix()]
    
    filter_parts = []
    
    if output_format in VIDEO_FORMATS:
        if speed != 1.0:
            filter_parts.append(f"setpts={1/speed}*PTS")
        if fps > 0:
            filter_parts.append(f"fps={fps}")
        
        if filter_parts:
            cmd.extend(["-vf", ",".join(filter_parts)])
        
        cmd.extend(["-c:v", "libx264", "-preset", "medium"])
        cmd.extend(quality_map.get(quality, ["-crf", "23"]))
        
        audio_filters = []
        if speed != 1.0:
            atempo = get_atempo_filter(speed)
            if atempo:
                audio_filters.append(atempo)
        if volume != 1.0:
            audio_filters.append(f"volume={volume}")
        
        if audio_filters:
            cmd.extend(["-af", ",".join(audio_filters)])
        
        if audio_channels > 0:
            cmd.extend(["-ac", str(audio_channels)])
        cmd.extend(["-c:a", "aac"])
        if audio_bitrate > 0:
            cmd.extend(["-b:a", f"{audio_bitrate}k"])
        else:
            cmd.extend(["-b:a", "128k"])
            
    elif output_format in AUDIO_FORMATS:
        cmd.extend(["-vn"])
        
        audio_filters = []
        if speed != 1.0:
            atempo = get_atempo_filter(speed)
            if atempo:
                audio_filters.append(atempo)
        if volume != 1.0:
            audio_filters.append(f"volume={volume}")
        
        if audio_filters:
            cmd.extend(["-af", ",".join(audio_filters)])
        
        if audio_channels > 0:
            cmd.extend(["-ac", str(audio_channels)])
        if output_format == "mp3":
            cmd.extend(["-c:a", "libmp3lame"])
            if audio_bitrate > 0:
                cmd.extend(["-b:a", f"{audio_bitrate}k"])
            else:
                cmd.extend(["-b:a", "192k"])
        elif output_format == "wav":
            cmd.extend(["-c:a", "pcm_s16le"])
        elif output_format == "flac":
            cmd.extend(["-c:a", "flac"])
        elif output_format == "aac":
            cmd.extend(["-c:a", "aac"])
            if audio_bitrate > 0:
                cmd.extend(["-b:a", f"{audio_bitrate}k"])
            else:
                cmd.extend(["-b:a", "192k"])
        elif output_format == "ogg":
            cmd.extend(["-c:a", "libvorbis"])
            if audio_bitrate > 0:
                cmd.extend(["-b:a", f"{audio_bitrate}k"])
            else:
                cmd.extend(["-b:a", "192k"])
        elif output_format == "m4a":
            cmd.extend(["-c:a", "aac"])
            if audio_bitrate > 0:
                cmd.extend(["-b:a", f"{audio_bitrate}k"])
            else:
                cmd.extend(["-b:a", "192k"])
    
    cmd.append(output_path.as_posix())
    
    logger.info(f"开始转换: {input_path} -> {output_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"转换成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "input_path": input_path.as_posix(),
        "output_format": output_format,
        "cmd": cmd,
    }

def images_to_video(image_paths: list, output_format: str = "mp4", fps: int = 1, duration: int = 2, width: int = 1280, height: int = 720, resize_mode: str = "pad") -> dict:
    if not image_paths:
        return {"success": False, "error": "没有选择图片 / No images selected"}
    
    output_dir = get_output_dir()
    
    if resize_mode == "pad":
        scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    else:
        scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
    
    import uuid
    from datetime import datetime
    temp_dir = output_dir / f"temp_clips_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(exist_ok=True)
    
    valid_clips = []
    first_chars = ""
    
    try:
        for i, img_path in enumerate(image_paths):
            clip_path = temp_dir / f"clip_{i:04d}.ts"
            cmd = [
                FFMPEG_PATH, "-y", "-loop", "1", "-t", str(duration),
                "-i", Path(img_path).as_posix(),
                "-vf", f"fps={fps},{scale_filter},format=yuv420p",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-f", "mpegts", clip_path.as_posix()
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and clip_path.exists():
                valid_clips.append(clip_path.as_posix())
                stem = Path(img_path).stem
                if stem:
                    first_chars += stem[0]
                logger.debug(f"图片处理成功: {img_path}")
            else:
                logger.warning(f"跳过无效图片: {img_path}")
        
        if not valid_clips:
            return {"success": False, "error": "没有有效的图片 / No valid images"}
        
        file_count = len(valid_clips)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{first_chars}-img2video{file_count}-{timestamp}"
        output_path = output_dir / f"{output_name}.{output_format}"
        
        concat_file = temp_dir / "concat_list.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for clip_path in valid_clips:
                f.write(f"file '{clip_path}'\n")
        
        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file.as_posix(),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            output_path.as_posix()
        ]
        
        logger.info(f"开始合并视频: {len(valid_clips)}张有效图片")
        log_cmd(cmd)
        result = subprocess.run(cmd, capture_output=True, text=True)
        log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
        
        if result.returncode != 0:
            return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
        
        logger.success(f"视频生成成功: {output_path}")
        return {
            "success": True,
            "output_path": output_path.as_posix(),
            "image_count": len(valid_clips),
            "cmd": cmd,
        }
    finally:
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

def video_to_images(input_path: str, fps: int = 1, format: str = "png") -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    base_dir = get_output_dir()
    input_path = Path(input_path)
    input_name = input_path.stem
    output_dir = base_dir / f"{input_name}_frames"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / f"%04d.{format}"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", input_path.as_posix(),
        "-vf", f"fps={fps}",
        output_pattern.as_posix()
    ]
    
    logger.info(f"开始提取图片: {input_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    image_files = sorted(output_dir.glob(f"*.{format}"))
    logger.success(f"提取成功: {len(image_files)}张图片")
    
    return {
        "success": True,
        "output_dir": output_dir.as_posix(),
        "image_count": len(image_files),
        "image_paths": [f.as_posix() for f in image_files[:10]],
        "cmd": cmd,
    }
