import subprocess
from pathlib import Path
from datetime import datetime
from config import get_output_dir
from utils.metadata import get_media_metadata
from utils.log_config import logger, log_subprocess, log_cmd
from utils.ffmpeg_utils import FFMPEG_PATH

def concat_videos(input_files: list, output_name: str = None, output_format: str = "mp4", resize_mode: str = "pad", output_width: int = 0, output_height: int = 0, output_fps: int = 0) -> dict:
    if not input_files:
        return {"success": False, "error": "没有输入文件 / No input files", "cmd": []}
    
    valid_files = []
    for f in input_files:
        if isinstance(f, dict):
            path = f.get("name")
        elif hasattr(f, 'name'):
            path = f.name
        else:
            path = f
        if path and Path(path).exists():
            result = get_media_metadata(path)
            if result["success"]:
                valid_files.append(Path(path).as_posix())
            else:
                return {"success": False, "error": f"文件无效或损坏: {path}\nInvalid or corrupted file", "cmd": []}
    
    if not valid_files:
        return {"success": False, "error": "没有有效文件 / No valid files", "cmd": []}
    
    output_dir = get_output_dir()
    if not output_name:
        first_chars = ""
        for fp in valid_files:
            stem = Path(fp).stem
            if stem:
                first_chars += stem[0]
        file_count = len(valid_files)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{first_chars}-concat{file_count}-{timestamp}"
    
    output_path = output_dir / f"{output_name}.{output_format}"
    
    first_result = get_media_metadata(valid_files[0])
    first_video = first_result.get("video", {})
    first_width = first_video.get("width", 0)
    first_height = first_video.get("height", 0)
    first_fps = first_video.get("fps", 0)
    
    target_width = output_width if output_width > 0 else first_width
    target_height = output_height if output_height > 0 else first_height
    target_fps = output_fps if output_fps > 0 else first_fps
    
    video_dims = []
    for fp in valid_files:
        result = get_media_metadata(fp)
        if result["success"]:
            video_info = result.get("video", {})
            w = video_info.get("width", 0)
            h = video_info.get("height", 0)
            video_dims.append((w, h))
        else:
            video_dims.append((0, 0))
    
    need_resize = resize_mode != "none" and (len(set(video_dims)) > 1 or (output_width > 0 and output_height > 0))
    
    if need_resize:
        filter_parts = []
        for i, (w, h) in enumerate(video_dims):
            if w == 0 or h == 0:
                filter_parts.append(f"[{i}:v]null,setsar=1,fps={target_fps}[v{i}]")
            elif resize_mode == "pad":
                filter_parts.append(f"[{i}:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps={target_fps}[v{i}]")
            elif resize_mode == "crop":
                filter_parts.append(f"[{i}:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},setsar=1,fps={target_fps}[v{i}]")
            else:
                filter_parts.append(f"[{i}:v]null,setsar=1,fps={target_fps}[v{i}]")
        
        filter_complex = ";".join(filter_parts) + ";"
        concat_inputs = "".join([f"[v{i}][{i}:a]" for i in range(len(valid_files))])
        filter_complex += f"{concat_inputs}concat=n={len(valid_files)}:v=1:a=1[outv][outa]"
        
        input_args = []
        for fp in valid_files:
            input_args.extend(["-i", fp])
        
        cmd = [
            FFMPEG_PATH, "-y",
        ] + input_args + [
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            output_path.as_posix()
        ]
    else:
        filter_parts = []
        for i in range(len(valid_files)):
            filter_parts.append(f"[{i}:v]setsar=1,fps={target_fps}[v{i}]")
        
        filter_complex = ";".join(filter_parts) + ";"
        concat_inputs = "".join([f"[v{i}][{i}:a]" for i in range(len(valid_files))])
        filter_complex += f"{concat_inputs}concat=n={len(valid_files)}:v=1:a=1[outv][outa]"
        
        input_args = []
        for fp in valid_files:
            input_args.extend(["-i", fp])
        
        cmd = [
            FFMPEG_PATH, "-y",
        ] + input_args + [
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            output_path.as_posix()
        ]
    
    logger.info(f"开始拼接视频: {len(valid_files)}个文件")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"视频拼接成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "cmd": cmd,
    }

def concat_audios(input_files: list, output_name: str = None, output_format: str = "aac", output_bitrate: int = 0, output_channels: int = 0) -> dict:
    if not input_files:
        return {"success": False, "error": "没有输入文件 / No input files", "cmd": []}
    
    valid_files = []
    for f in input_files:
        if isinstance(f, dict):
            path = f.get("name")
        elif hasattr(f, 'name'):
            path = f.name
        else:
            path = f
        if path and Path(path).exists():
            result = get_media_metadata(path)
            if result["success"]:
                valid_files.append(Path(path).as_posix())
            else:
                return {"success": False, "error": f"文件无效或损坏: {path}\nInvalid or corrupted file", "cmd": []}
    
    if not valid_files:
        return {"success": False, "error": "没有有效文件 / No valid files", "cmd": []}
    
    output_dir = get_output_dir()
    if not output_name:
        first_chars = ""
        for fp in valid_files:
            stem = Path(fp).stem
            if stem:
                first_chars += stem[0]
        file_count = len(valid_files)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{first_chars}-concat{file_count}-{timestamp}"
    
    output_path = output_dir / f"{output_name}.{output_format}"
    
    list_file = output_dir / "concat_audio_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for file_path in valid_files:
            f.write(f"file '{file_path}'\n")
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file.as_posix(),
    ]
    
    if output_channels > 0:
        cmd.extend(["-ac", str(output_channels)])
    
    if output_format == "mp3":
        if output_bitrate > 0:
            cmd.extend(["-b:a", f"{output_bitrate}k"])
        else:
            cmd.extend(["-q:a", "2"])
        cmd.extend(["-c:a", "libmp3lame"])
    elif output_format == "aac":
        if output_bitrate > 0:
            cmd.extend(["-b:a", f"{output_bitrate}k"])
        else:
            cmd.extend(["-b:a", "192k"])
        cmd.extend(["-c:a", "aac"])
    else:
        cmd.extend(["-c:a", "copy"])
    
    cmd.append(output_path.as_posix())
    
    logger.info(f"开始拼接音频: {len(valid_files)}个文件")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    list_file.unlink(missing_ok=True)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"音频拼接成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "cmd": cmd,
    }
