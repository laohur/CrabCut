import subprocess
import tempfile
import os
from pathlib import Path
from utils.log_config import logger, log_cmd, log_subprocess
from utils.metadata import get_media_metadata
from utils.ffmpeg_utils import FFMPEG_PATH

def get_output_dir():
    from utils.converter import get_output_dir as base_get_output_dir
    return base_get_output_dir()

def extract_audio(input_path: str, audio_format: str = "aac", bitrate: str = "192k") -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    input_path = Path(input_path)
    output_dir = get_output_dir()
    output_path = output_dir / f"{input_path.stem}.{audio_format}"
    
    if audio_format == "mp3":
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path.as_posix(),
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", bitrate,
            output_path.as_posix()
        ]
    elif audio_format == "aac":
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path.as_posix(),
            "-vn",
            "-acodec", "aac",
            "-b:a", bitrate,
            output_path.as_posix()
        ]
    elif audio_format == "wav":
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path.as_posix(),
            "-vn",
            "-acodec", "pcm_s16le",
            output_path.as_posix()
        ]
    elif audio_format == "flac":
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path.as_posix(),
            "-vn",
            "-acodec", "flac",
            output_path.as_posix()
        ]
    else:
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path.as_posix(),
            "-vn",
            "-acodec", "copy",
            output_path.as_posix()
        ]
    
    logger.info(f"开始提取音频: {input_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"音频提取成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "cmd": cmd,
    }

def extract_video(input_path: str, video_format: str = "mp4") -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    input_path = Path(input_path)
    output_dir = get_output_dir()
    output_path = output_dir / f"{input_path.stem}_video.{video_format}"
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", input_path.as_posix(),
        "-an",
        "-c:v", "copy",
        output_path.as_posix()
    ]
    
    logger.info(f"开始提取视频: {input_path}")
    log_cmd(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    log_subprocess(cmd, result.stdout, result.stderr, result.returncode)
    
    if result.returncode != 0:
        return {"success": False, "error": f"ffmpeg error: {result.stderr}", "cmd": cmd}
    
    logger.success(f"视频提取成功: {output_path}")
    return {
        "success": True,
        "output_path": output_path.as_posix(),
        "cmd": cmd,
    }

def separate_vocals(input_path: str, model: str = "htdemucs_ft.yaml") -> dict:
    if not input_path or not Path(input_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    input_path = Path(input_path)
    output_dir = get_output_dir()
    
    try:
        import audio_separator
    except ImportError as e:
        return {"success": False, "error": f"audio-separator未安装: {e}\n请运行: pip install audio-separator"}
    
    logger.info(f"开始人声分离: {input_path.as_posix()}")
    
    temp_wav = None
    try:
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav_path = Path(temp_wav.name).as_posix()
        temp_wav.close()
        
        convert_cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path.as_posix(),
            "-ar", "44100",
            "-ac", "2",
            "-f", "wav",
            temp_wav_path
        ]
        logger.info("转换音频格式...")
        log_cmd(convert_cmd)
        result = subprocess.run(convert_cmd, capture_output=True, text=True)
        log_subprocess(convert_cmd, result.stdout, result.stderr, result.returncode)
        
        if result.returncode != 0:
            return {"success": False, "error": f"音频转换失败: {result.stderr}"}
        
        output_folder = output_dir / f"{input_path.stem}_separated"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        from audio_separator.separator import Separator
        
        separator = Separator(
            output_dir=output_folder.as_posix(),
            output_format="WAV",
        )
        
        logger.info(f"加载模型: {model}")
        separator.load_model(model)
        
        original_name = input_path.stem
        custom_names = {
            "vocals": f"{original_name}_vocals",
            "no_vocals": f"{original_name}_instrumental",
            "instrumental": f"{original_name}_instrumental",
        }
        
        logger.info(f"执行人声分离: {model}")
        output_files = separator.separate(temp_wav_path, custom_output_names=custom_names)
        
        logger.info(f"输出文件: {output_files}")
        
        vocals_path = None
        accompaniment_path = None
        
        for f in output_files:
            f_path = Path(f)
            if not f_path.is_absolute():
                f_path = output_folder / f_path
            f_lower = f.lower()
            f_name = Path(f).stem.lower()
            
            if "vocals" in f_name and "instrumental" not in f_name and "no_vocals" not in f_name:
                vocals_path = f_path.as_posix()
            elif "instrumental" in f_name or "no_vocals" in f_name:
                accompaniment_path = f_path.as_posix()
        
        logger.success(f"人声分离成功: {output_folder.as_posix()}")
        logger.info(f"人声: {vocals_path}, 伴奏: {accompaniment_path}")
        return {
            "success": True,
            "output_dir": output_folder.as_posix(),
            "vocals_path": vocals_path,
            "accompaniment_path": accompaniment_path,
        }
        
    except Exception as e:
        logger.error(f"人声分离失败: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if temp_wav:
            try:
                os.unlink(temp_wav_path)
            except:
                pass

__all__ = ["extract_audio", "extract_video", "separate_vocals"]
