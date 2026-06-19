import subprocess
from pathlib import Path
from config import get_output_dir
from utils.log_config import logger, log_subprocess, log_cmd
from utils.ffmpeg_utils import FFMPEG_PATH

def crop_video(input_path: str, start_time: float, end_time: float, x: int = 0, y: int = 0, width: int = 0, height: int = 0) -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    output_dir = get_output_dir()
    input_path = Path(input_path)
    input_name = input_path.stem
    output_path = output_dir / f"{input_name}_cropped.mp4"
    
    cmd = [FFMPEG_PATH, "-y", "-i", input_path.as_posix()]
    
    if start_time > 0:
        cmd.extend(["-ss", str(start_time)])
    
    if end_time > 0:
        cmd.extend(["-to", str(end_time)])
    
    filter_parts = []
    if width > 0 and height > 0:
        filter_parts.append(f"crop={width}:{height}:{x}:{y}")
    
    if filter_parts:
        cmd.extend(["-vf", ",".join(filter_parts)])
    
    cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac"])
    cmd.append(output_path.as_posix())
    
    logger.info(f"开始裁剪视频: {input_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}"}
    
    logger.success(f"视频裁剪成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
    }

def get_video_frame(input_path: str, time: float) -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    output_dir = get_output_dir()
    frame_path = output_dir / "preview_frame.png"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", str(time),
        "-i", Path(input_path).as_posix(),
        "-vframes", "1",
        frame_path.as_posix()
    ]
    
    logger.info(f"获取视频帧: {input_path} @ {time}s")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}"}
    
    return {
        "success": True,
        "frame_path": frame_path.as_posix(),
    }

def trim_video(input_path: str, start_time: float, end_time: float) -> dict:
    return crop_video(input_path, start_time, end_time)

def crop_image(input_path: str, x: int, y: int, width: int, height: int) -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    output_dir = get_output_dir()
    input_path = Path(input_path)
    input_name = input_path.stem
    ext = input_path.suffix
    output_path = output_dir / f"{input_name}_cropped{ext}"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", input_path.as_posix(),
        "-vf", f"crop={width}:{height}:{x}:{y}",
        output_path.as_posix()
    ]
    
    logger.info(f"开始裁剪图片: {input_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}"}
    
    logger.success(f"图片裁剪成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
    }
