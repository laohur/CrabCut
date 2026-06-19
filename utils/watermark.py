import subprocess
import tempfile
import os
from pathlib import Path
from utils.log_config import logger, log_cmd, log_subprocess
from utils.ffmpeg_utils import FFMPEG_PATH

def get_output_dir():
    from utils.converter import get_output_dir as base_get_output_dir
    return base_get_output_dir()

def add_image_watermark(
    input_path: str,
    watermark_path: str,
    position: str = "bottom_right",
    opacity: float = 0.7,
    scale: float = 0.2,
    output_path: str = None
) -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "输入文件不存在 / Input file not found"}
    if not watermark_path or not Path(watermark_path).exists():
        return {"success": False, "error": "水印文件不存在 / Watermark file not found"}
    
    input_path = Path(input_path)
    watermark_path = Path(watermark_path)
    output_dir = get_output_dir()
    
    if output_path:
        output_path = Path(output_path)
    else:
        output_path = output_dir / f"{input_path.stem}_watermarked.mp4"
    
    position_map = {
        "top_left": "10:10",
        "top_right": "W-w-10:10",
        "bottom_left": "10:H-h-10",
        "bottom_right": "W-w-10:H-h-10",
        "center": "(W-w)/2:(H-h)/2",
    }
    overlay_pos = position_map.get(position, "W-w-10:H-h-10")
    
    filter_complex = f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[wm];[0:v][wm]overlay={overlay_pos}"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", input_path.as_posix(),
        "-i", watermark_path.as_posix(),
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path.as_posix()
    ]
    
    logger.info(f"添加图片水印: {input_path.as_posix()}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"水印添加成功: {output_path.as_posix()}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "cmd": cmd,
    }

def add_text_watermark(
    input_path: str,
    text: str,
    position: str = "bottom_right",
    font_size: int = 24,
    font_color: str = "white",
    opacity: float = 0.7,
    output_path: str = None
) -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "输入文件不存在 / Input file not found"}
    if not text:
        return {"success": False, "error": "水印文字不能为空 / Watermark text cannot be empty"}
    
    input_path = Path(input_path)
    output_dir = get_output_dir()
    
    if output_path:
        output_path = Path(output_path)
    else:
        output_path = output_dir / f"{input_path.stem}_textwm.mp4"
    
    position_map = {
        "top_left": "x=10:y=10",
        "top_right": "x=W-tw-10:y=10",
        "bottom_left": "x=10:y=H-th-10",
        "bottom_right": "x=W-tw-10:y=H-th-10",
        "center": "x=(W-tw)/2:y=(H-th)/2",
    }
    pos_params = position_map.get(position, "x=W-tw-10:y=H-th-10")
    
    alpha = format(opacity, ".2f")
    
    draw_text = f"drawtext=text='{text}':fontsize={font_size}:fontcolor={font_color}@{alpha}:{pos_params}"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", input_path.as_posix(),
        "-vf", draw_text,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path.as_posix()
    ]
    
    logger.info(f"添加文字水印: {input_path.as_posix()}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"水印添加成功: {output_path.as_posix()}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "cmd": cmd,
    }

def add_blur_watermark(
    input_path: str,
    x: int,
    y: int,
    width: int,
    height: int,
    blur_strength: int = 20,
    output_path: str = None
) -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "输入文件不存在 / Input file not found"}
    
    input_path = Path(input_path)
    output_dir = get_output_dir()
    
    if output_path:
        output_path = Path(output_path)
    else:
        output_path = output_dir / f"{input_path.stem}_blurred.mp4"
    
    filter_complex = f"[0:v]crop={width}:{height}:{x}:{y},boxblur={min(blur_strength, 12)}:{min(blur_strength, 12)}[blur];[0:v][blur]overlay={x}:{y}"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", input_path.as_posix(),
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path.as_posix()
    ]
    
    logger.info(f"添加模糊水印: {input_path.as_posix()}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"模糊水印添加成功: {output_path.as_posix()}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "cmd": cmd,
    }

def generate_preview(
    input_path: str,
    watermark_type: str = "image",
    watermark_path: str = None,
    text: str = None,
    position: str = "bottom_right",
    opacity: float = 0.7,
    font_size: int = 24,
    font_color: str = "white",
) -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "输入文件不存在 / Input file not found"}
    
    input_path = Path(input_path)
    output_dir = get_output_dir()
    preview_path = output_dir / f"{input_path.stem}_preview.jpg"
    
    temp_output = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    temp_output_path = temp_output.name
    temp_output.close()
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", input_path.as_posix(),
    ]
    
    if watermark_type == "image" and watermark_path and Path(watermark_path).exists():
        position_map = {
            "top_left": "10:10",
            "top_right": "W-w-10:10",
            "bottom_left": "10:H-h-10",
            "bottom_right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2",
        }
        overlay_pos = position_map.get(position, "W-w-10:H-h-10")
        filter_complex = f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[wm];[0:v][wm]overlay={overlay_pos}"
        cmd.extend([
            "-i", Path(watermark_path).as_posix(),
            "-filter_complex", filter_complex,
            "-vframes", "1",
            "-q:v", "2",
        ])
    elif watermark_type == "text" and text:
        position_map = {
            "top_left": "x=10:y=10",
            "top_right": "x=W-tw-10:y=10",
            "bottom_left": "x=10:y=H-th-10",
            "bottom_right": "x=W-tw-10:y=H-th-10",
            "center": "x=(W-tw)/2:y=(H-th)/2",
        }
        pos_params = position_map.get(position, "x=W-tw-10:y=H-th-10")
        alpha = format(opacity, ".2f")
        draw_text = f"drawtext=text='{text}':fontsize={font_size}:fontcolor={font_color}@{alpha}:{pos_params}"
        cmd.extend([
            "-vf", draw_text,
            "-vframes", "1",
            "-q:v", "2",
        ])
    else:
        cmd.extend(["-vframes", "1", "-q:v", "2"])
    
    cmd.append(temp_output_path)
    
    logger.info(f"生成预览: {input_path.as_posix()}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"预览生成失败: {result.stderr}"}
    
    import shutil
    shutil.move(temp_output_path, preview_path.as_posix())
    
    logger.success(f"预览生成成功: {preview_path.as_posix()}")
    return {
        "success": True,
        "preview_path": preview_path.as_posix(),
    }

__all__ = [
    "add_image_watermark",
    "add_text_watermark",
    "add_blur_watermark",
    "generate_preview",
]
