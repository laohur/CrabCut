def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"

def get_ffprobe_path():
    import shutil
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        return ffprobe
    return "ffprobe"

FFMPEG_PATH = get_ffmpeg_path()
FFPROBE_PATH = get_ffprobe_path()
