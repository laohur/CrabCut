import os
import yt_dlp
from pathlib import Path
from config import get_output_dir
from utils.i18n import translate_text
from utils.log_config import logger

def download_video(url: str, format_type: str = "video", progress_callback=None) -> dict:
    output_dir = get_output_dir()
    
    ydl_opts = {
        'outtmpl': (output_dir / '%(title)s.%(ext)s').as_posix(),
        'quiet': True,
        'no_warnings': True,
    }
    
    if format_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'aac',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    
    try:
        logger.info(f"开始下载: {url} ({format_type})")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type == "audio":
                filename = Path(filename).with_suffix('.aac')
            
            logger.success(f"下载成功: {filename}")
            return {
                'success': True,
                'filename': Path(filename).as_posix(),
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
            }
    except Exception as e:
        logger.error(f"下载失败: {url} - {e}")
        return {
            'success': False,
            'error': str(e)
        }

def download_multiple(urls: str, format_type: str = "video", progress_callback=None):
    url_list = [u.strip() for u in urls.strip().split('\n') if u.strip()]
    results = []
    
    logger.info(f"批量下载: {len(url_list)}个URL")
    for i, url in enumerate(url_list):
        if progress_callback:
            progress_callback(i + 1, len(url_list), url)
        result = download_video(url, format_type)
        result['url'] = url
        results.append(result)
    
    return results

def get_video_info(url: str) -> dict:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        logger.info(f"获取视频信息: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'success': True,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'description': info.get('description', '')[:500] if info.get('description') else '',
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
            }
    except Exception as e:
        logger.error(f"获取视频信息失败: {url} - {e}")
        return {
            'success': False,
            'error': str(e)
        }
