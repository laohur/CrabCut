"""
TTS: edge-tts
    322 voices in 142 locales
    Data file: data/edge_tts_voices.json
"""

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Optional, List, Dict
from utils.log_config import logger

VOICES_DATA_PATH = Path(__file__).parent.parent / "data" / "edge_tts_voices.json"
_voices_cache = None

LANG_GROUPS = {
    "zh": {"name": "中文", "name_en": "Chinese", "locales": ["zh-CN", "zh-HK", "zh-TW", "zh-CN-liaoning", "zh-CN-shaanxi"]},
    "en": {"name": "English", "name_en": "English", "locales": ["en-US", "en-GB", "en-AU", "en-CA", "en-IN", "en-IE", "en-NZ", "en-ZA", "en-SG", "en-HK", "en-KE", "en-NG", "en-PH", "en-TZ"]},
    "ja": {"name": "日本語", "name_en": "Japanese", "locales": ["ja-JP"]},
    "ko": {"name": "한국어", "name_en": "Korean", "locales": ["ko-KR"]},
    "fr": {"name": "Français", "name_en": "French", "locales": ["fr-FR", "fr-CA", "fr-CH", "fr-BE"]},
    "de": {"name": "Deutsch", "name_en": "German", "locales": ["de-DE", "de-AT", "de-CH"]},
    "es": {"name": "Español", "name_en": "Spanish", "locales": ["es-ES", "es-MX", "es-AR", "es-CO", "es-CL", "es-PE", "es-VE", "es-PR", "es-US", "es-BO", "es-CR", "es-CU", "es-DO", "es-EC", "es-SV", "es-GQ", "es-GT", "es-HN", "es-NI", "es-PA", "es-PY", "es-UY"]},
    "pt": {"name": "Português", "name_en": "Portuguese", "locales": ["pt-BR", "pt-PT"]},
    "ru": {"name": "Русский", "name_en": "Russian", "locales": ["ru-RU"]},
    "ar": {"name": "العربية", "name_en": "Arabic", "locales": ["ar-SA", "ar-AE", "ar-EG", "ar-BH", "ar-DZ", "ar-IQ", "ar-JO", "ar-KW", "ar-LB", "ar-LY", "ar-MA", "ar-OM", "ar-QA", "ar-SY", "ar-TN", "ar-YE"]},
    "it": {"name": "Italiano", "name_en": "Italian", "locales": ["it-IT"]},
    "nl": {"name": "Nederlands", "name_en": "Dutch", "locales": ["nl-NL", "nl-BE"]},
    "pl": {"name": "Polski", "name_en": "Polish", "locales": ["pl-PL"]},
    "tr": {"name": "Türkçe", "name_en": "Turkish", "locales": ["tr-TR"]},
    "vi": {"name": "Tiếng Việt", "name_en": "Vietnamese", "locales": ["vi-VN"]},
    "th": {"name": "ไทย", "name_en": "Thai", "locales": ["th-TH"]},
    "id": {"name": "Bahasa Indonesia", "name_en": "Indonesian", "locales": ["id-ID"]},
    "hi": {"name": "हिन्दी", "name_en": "Hindi", "locales": ["hi-IN"]},
    "uk": {"name": "Українська", "name_en": "Ukrainian", "locales": ["uk-UA"]},
    "cs": {"name": "Čeština", "name_en": "Czech", "locales": ["cs-CZ"]},
    "da": {"name": "Dansk", "name_en": "Danish", "locales": ["da-DK"]},
    "fi": {"name": "Suomi", "name_en": "Finnish", "locales": ["fi-FI"]},
    "el": {"name": "Ελληνικά", "name_en": "Greek", "locales": ["el-GR"]},
    "he": {"name": "עברית", "name_en": "Hebrew", "locales": ["he-IL"]},
    "hu": {"name": "Magyar", "name_en": "Hungarian", "locales": ["hu-HU"]},
    "ms": {"name": "Bahasa Melayu", "name_en": "Malay", "locales": ["ms-MY"]},
    "nb": {"name": "Norsk", "name_en": "Norwegian", "locales": ["nb-NO"]},
    "ro": {"name": "Română", "name_en": "Romanian", "locales": ["ro-RO"]},
    "sk": {"name": "Slovenčina", "name_en": "Slovak", "locales": ["sk-SK"]},
    "sv": {"name": "Svenska", "name_en": "Swedish", "locales": ["sv-SE"]},
    "ta": {"name": "தமிழ்", "name_en": "Tamil", "locales": ["ta-IN", "ta-MY", "ta-SG", "ta-LK"]},
    "te": {"name": "తెలుగు", "name_en": "Telugu", "locales": ["te-IN"]},
    "bn": {"name": "বাংলা", "name_en": "Bengali", "locales": ["bn-BD", "bn-IN"]},
    "gu": {"name": "ગુજરાતી", "name_en": "Gujarati", "locales": ["gu-IN"]},
    "kn": {"name": "ಕನ್ನಡ", "name_en": "Kannada", "locales": ["kn-IN"]},
    "ml": {"name": "മലയാളം", "name_en": "Malayalam", "locales": ["ml-IN"]},
    "mr": {"name": "मराठी", "name_en": "Marathi", "locales": ["mr-IN"]},
    "fa": {"name": "فارسی", "name_en": "Persian", "locales": ["fa-IR"]},
    "ur": {"name": "اردو", "name_en": "Urdu", "locales": ["ur-IN", "ur-PK"]},
    "af": {"name": "Afrikaans", "name_en": "Afrikaans", "locales": ["af-ZA"]},
    "bg": {"name": "Български", "name_en": "Bulgarian", "locales": ["bg-BG"]},
    "ca": {"name": "Català", "name_en": "Catalan", "locales": ["ca-ES"]},
    "hr": {"name": "Hrvatski", "name_en": "Croatian", "locales": ["hr-HR"]},
    "et": {"name": "Eesti", "name_en": "Estonian", "locales": ["et-EE"]},
    "gl": {"name": "Galego", "name_en": "Galician", "locales": ["gl-ES"]},
    "ka": {"name": "ქართული", "name_en": "Georgian", "locales": ["ka-GE"]},
    "is": {"name": "Íslenska", "name_en": "Icelandic", "locales": ["is-IS"]},
    "lo": {"name": "ລາວ", "name_en": "Lao", "locales": ["lo-LA"]},
    "lv": {"name": "Latviešu", "name_en": "Latvian", "locales": ["lv-LV"]},
    "lt": {"name": "Lietuvių", "name_en": "Lithuanian", "locales": ["lt-LT"]},
    "mk": {"name": "Македонски", "name_en": "Macedonian", "locales": ["mk-MK"]},
    "mt": {"name": "Malti", "name_en": "Maltese", "locales": ["mt-MT"]},
    "mn": {"name": "Монгол", "name_en": "Mongolian", "locales": ["mn-MN"]},
    "ne": {"name": "नेपाली", "name_en": "Nepali", "locales": ["ne-NP"]},
    "ps": {"name": "پښتو", "name_en": "Pashto", "locales": ["ps-AF"]},
    "sr": {"name": "Српски", "name_en": "Serbian", "locales": ["sr-RS"]},
    "si": {"name": "සිංහල", "name_en": "Sinhala", "locales": ["si-LK"]},
    "sl": {"name": "Slovenščina", "name_en": "Slovenian", "locales": ["sl-SI"]},
    "sw": {"name": "Kiswahili", "name_en": "Swahili", "locales": ["sw-KE", "sw-TZ"]},
    "fil": {"name": "Filipino", "name_en": "Filipino", "locales": ["fil-PH"]},
    "zu": {"name": "IsiZulu", "name_en": "Zulu", "locales": ["zu-ZA"]},
}

def _load_voices_data() -> Dict:
    global _voices_cache
    if _voices_cache is not None:
        return _voices_cache
    
    if VOICES_DATA_PATH.exists():
        with open(VOICES_DATA_PATH, "r", encoding="utf-8") as f:
            _voices_cache = json.load(f)
            return _voices_cache
    return {"total": 0, "locales": [], "voices_by_locale": {}, "all_voices": []}

def get_lang_groups() -> List[str]:
    return list(LANG_GROUPS.keys())

def get_lang_name(lang_code: str, ui_lang: str = "zh") -> str:
    lang = LANG_GROUPS.get(lang_code, {})
    if ui_lang == "zh":
        return lang.get("name", lang_code)
    return lang.get("name_en", lang_code)

def get_all_locales() -> List[str]:
    data = _load_voices_data()
    return sorted(data.get("locales", []))

def get_locales_for_lang(lang_code: str) -> List[str]:
    lang = LANG_GROUPS.get(lang_code, {})
    return lang.get("locales", [])

def get_voices_for_locale(locale: str) -> List[Dict]:
    data = _load_voices_data()
    voices = data.get("voices_by_locale", {}).get(locale, [])
    return [
        {
            "name": v.get("name", v.get("voice", "")),
            "voice": v.get("voice", ""),
            "gender": v.get("gender", "Unknown"),
            "locale": v.get("locale", locale),
        }
        for v in voices
    ]

def get_all_voices_for_lang(lang_code: str) -> List[Dict]:
    locales = get_locales_for_lang(lang_code)
    all_voices = []
    data = _load_voices_data()
    
    for locale in locales:
        voices = data.get("voices_by_locale", {}).get(locale, [])
        for v in voices:
            all_voices.append({
                "name": v.get("name", v.get("voice", "")),
                "voice": v.get("voice", ""),
                "gender": v.get("gender", "Unknown"),
                "locale": v.get("locale", locale),
            })
    
    return all_voices

def get_all_voices() -> List[Dict]:
    data = _load_voices_data()
    return data.get("all_voices", [])

def get_output_dir():
    from utils.converter import get_output_dir as base_get_output_dir
    return base_get_output_dir()

def sanitize_filename(text: str, max_len: int = 20) -> str:
    text = re.sub(r'[<>:"/\\|?*\n\r\t]', '', text)
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len]
    if not text:
        text = "tts"
    return text

def generate_output_filename(text: str, source_file: Optional[str] = None) -> str:
    if source_file:
        stem = Path(source_file).stem
        return f"{stem}-tts.mp3"
    
    text = text.strip()
    if len(text) <= 10:
        safe_name = sanitize_filename(text, 20)
        return f"{safe_name}.mp3"
    else:
        prefix = sanitize_filename(text[:5], 5)
        suffix = sanitize_filename(text[-5:], 5)
        return f"{prefix}...{suffix}.mp3"

BYTES_PER_SECOND = 100
AUDIO_BYTES_PER_SECOND = 10

def estimate_time(byte_count: int) -> float:
    return byte_count / BYTES_PER_SECOND

def estimate_audio_duration(byte_count: int) -> float:
    return byte_count / AUDIO_BYTES_PER_SECOND

def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}时{minutes}分"

def format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def get_audio_duration(audio_path: str) -> float:
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"无法获取音频时长 / Cannot get audio duration: {e}")
        return 0.0

def split_text_by_length(text: str, max_bytes: int = 1500) -> List[str]:
    if not text or not text.strip():
        return []
    
    text = text.strip()
    text_bytes = len(text.encode('utf-8'))
    
    if text_bytes <= max_bytes:
        return [text]
    
    try:
        from UnicodeTokenizer import UnicodeTokenizer
        tokenizer = UnicodeTokenizer()
        sentences = tokenizer.tokenize(text)
        if not sentences:
            sentences = [text]
    except ImportError:
        sentence_endings = r'([。！？.!?；;：:\n\r\t।॥။။።۔؟؛ฯ⳾])'
        sentences = re.split(sentence_endings, text)
        merged = []
        for i in range(0, len(sentences), 2):
            s = sentences[i]
            if i + 1 < len(sentences):
                s += sentences[i + 1]
            if s.strip():
                merged.append(s)
        sentences = merged if merged else [text]
    
    chunks = []
    current_chunk = ""
    current_bytes = 0
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        
        sentence_bytes = len(sentence.encode('utf-8'))
        
        if current_bytes + sentence_bytes <= max_bytes:
            current_chunk += sentence
            current_bytes += sentence_bytes
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            if sentence_bytes > max_bytes:
                for char in sentence:
                    char_bytes = len(char.encode('utf-8'))
                    if current_bytes + char_bytes <= max_bytes:
                        current_chunk += char
                        current_bytes += char_bytes
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = char
                        current_bytes = char_bytes
            else:
                current_chunk = sentence
                current_bytes = sentence_bytes
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def parse_srt_content(srt_content: str) -> List[Dict]:
    pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, srt_content, re.DOTALL)
    
    segments = []
    for match in matches:
        index, start, end, text = match
        text = text.strip().replace('\n', ' ')
        if text:
            segments.append({
                "index": int(index),
                "start": start,
                "end": end,
                "text": text
            })
    
    return segments

def parse_json_content(json_content: str) -> List[str]:
    try:
        data = json.loads(json_content)
        if isinstance(data, str):
            return [data]
        elif isinstance(data, list):
            texts = []
            for item in data:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict):
                    if "text" in item:
                        texts.append(item["text"])
                    elif "segments" in item:
                        for seg in item["segments"]:
                            if isinstance(seg, dict) and "text" in seg:
                                texts.append(seg["text"])
            return texts
        elif isinstance(data, dict):
            if "text" in data:
                return [data["text"]]
            elif "segments" in data:
                return [seg.get("text", "") for seg in data["segments"] if isinstance(seg, dict)]
        return []
    except json.JSONDecodeError:
        return [json_content]

def generate_srt(segments: List[Dict], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{seg['start']} --> {seg['end']}\n")
            f.write(f"{seg['text']}\n\n")

def generate_json(segments: List[Dict], output_path: str):
    json_segments = []
    for seg in segments:
        json_segments.append({
            "index": seg.get("index", 0),
            "start": seg.get("start_sec", 0.0),
            "end": seg.get("end_sec", 0.0),
            "text": seg.get("text", "")
        })
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"segments": json_segments}, f, ensure_ascii=False, indent=2)

async def _tts_single(text: str, voice: str, output_path: str, rate: str = "+0%", volume: str = "+0%", pitch: str = "+0Hz") -> bool:
    import edge_tts
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
    await communicate.save(output_path)
    return True

def tts_single(text: str, voice: str, output_path: str, rate: str = "+0%", volume: str = "+0%", pitch: str = "+0Hz", skip_exists: bool = True) -> dict:
    if not text or not text.strip():
        return {"success": False, "error": "文本为空 / Text is empty"}
    
    if skip_exists and Path(output_path).exists():
        logger.info(f"文件已存在，跳过 / File exists, skip: {output_path}")
        return {"success": True, "output": output_path, "skipped": True}
    
    try:
        asyncio.run(_tts_single(text, voice, output_path, rate, volume, pitch))
        logger.success(f"TTS 生成成功 / TTS success: {output_path}")
        return {"success": True, "output": output_path}
    except Exception as e:
        logger.error(f"TTS 生成失败 / TTS failed: {e}")
        return {"success": False, "error": str(e)}

def tts_long_text(text: str, voice: str, output_path: str, rate: str = "+0%", volume: str = "+0%", pitch: str = "+0%", max_bytes: int = 1500, skip_exists: bool = True, export_formats: List[str] = None) -> dict:
    if export_formats is None:
        export_formats = []
    
    if not text or not text.strip():
        return {"success": False, "error": "文本为空 / Text is empty"}
    
    if skip_exists and Path(output_path).exists():
        logger.info(f"文件已存在，跳过 / File exists, skip: {output_path}")
        return {"success": True, "output": output_path, "skipped": True}
    
    chunks = split_text_by_length(text, max_bytes)
    if not chunks:
        return {"success": False, "error": "文本为空 / Text is empty"}
    
    if len(chunks) == 1:
        result = tts_single(chunks[0], voice, output_path, rate, volume, pitch, skip_exists=False)
        if result["success"] and export_formats:
            output_stem = Path(output_path).stem
            output_dir = Path(output_path).parent
            audio_duration = get_audio_duration(output_path)
            segments = [{
                "index": 1, 
                "start": "00:00:00,000", 
                "end": format_srt_time(audio_duration), 
                "text": chunks[0],
                "start_sec": 0.0,
                "end_sec": audio_duration
            }]
            if "srt" in export_formats:
                generate_srt(segments, output_dir / f"{output_stem}.srt")
            if "json" in export_formats:
                generate_json(segments, output_dir / f"{output_stem}.json")
        return result
    
    import subprocess
    
    output_dir = Path(output_path).parent
    output_stem = Path(output_path).stem
    chunk_dir = output_dir / f"{output_stem}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    
    temp_files = []
    segments = []
    current_time = 0.0
    
    try:
        for i, chunk in enumerate(chunks):
            chunk_path = chunk_dir / f"{i+1:03d}.mp3"
            result = tts_single(chunk, voice, str(chunk_path), rate, volume, pitch, skip_exists=False)
            if not result["success"]:
                return result
            
            chunk_duration = get_audio_duration(str(chunk_path))
            temp_files.append(str(chunk_path))
            segments.append({
                "index": i + 1,
                "start": format_srt_time(current_time),
                "end": format_srt_time(current_time + chunk_duration),
                "text": chunk,
                "start_sec": current_time,
                "end_sec": current_time + chunk_duration
            })
            current_time += chunk_duration
        
        concat_list = chunk_dir / "concat_list.txt"
        with open(concat_list, "w") as f:
            for tf in temp_files:
                f.write(f"file '{tf}'\n")
        
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list), "-c", "copy", output_path
        ]
        subprocess.run(cmd, check=True)
        
        concat_list.unlink(missing_ok=True)
        
        if "srt" in export_formats:
            generate_srt(segments, output_dir / f"{output_stem}.srt")
        if "json" in export_formats:
            generate_json(segments, output_dir / f"{output_stem}.json")
        
        logger.success(f"TTS 长文本生成成功 / TTS long text success: {output_path}")
        return {
            "success": True,
            "output": output_path,
            "chunks": len(chunks),
            "chunk_dir": str(chunk_dir),
            "segments": segments
        }
    
    except Exception as e:
        logger.error(f"TTS 长文本生成失败 / TTS long text failed: {e}")
        return {"success": False, "error": str(e)}

def tts_from_file(input_path: str, voice: str, output_path: str, rate: str = "+0%", volume: str = "+0%", pitch: str = "+0%", skip_exists: bool = True, export_formats: List[str] = None) -> dict:
    if export_formats is None:
        export_formats = []
    
    path = Path(input_path)
    if not path.exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    suffix = path.suffix.lower()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except Exception as e:
        return {"success": False, "error": f"读取文件失败 / Failed to read file: {e}"}
    
    if suffix == ".txt":
        return tts_long_text(content, voice, output_path, rate, volume, pitch, skip_exists=skip_exists, export_formats=export_formats)
    
    elif suffix == ".json":
        texts = parse_json_content(content)
        if not texts:
            return {"success": False, "error": "JSON 文件无有效文本 / No valid text in JSON"}
        combined_text = " ".join(texts)
        return tts_long_text(combined_text, voice, output_path, rate, volume, pitch, skip_exists=skip_exists, export_formats=export_formats)
    
    elif suffix == ".srt":
        segments = parse_srt_content(content)
        if not segments:
            return {"success": False, "error": "SRT 文件无有效内容 / No valid content in SRT"}
        combined_text = " ".join(seg["text"] for seg in segments)
        return tts_long_text(combined_text, voice, output_path, rate, volume, pitch, skip_exists=skip_exists, export_formats=export_formats)
    
    else:
        return {"success": False, "error": f"不支持的文件格式 / Unsupported format: {suffix}"}

def tts_batch_files(input_paths: List[str], voice: str, rate: str = "+0%", volume: str = "+0%", pitch: str = "+0%", skip_exists: bool = True, export_formats: List[str] = None) -> dict:
    if export_formats is None:
        export_formats = []
    
    output_dir = get_output_dir()
    results = []
    success_count = 0
    skipped_count = 0
    
    for input_path in input_paths:
        path = Path(input_path)
        output_filename = generate_output_filename("", source_file=input_path)
        output_path = output_dir / output_filename
        
        result = tts_from_file(input_path, voice, str(output_path), rate, volume, pitch, skip_exists=skip_exists, export_formats=export_formats)
        results.append({
            "input": input_path,
            "output": str(output_path) if result["success"] else None,
            "success": result["success"],
            "skipped": result.get("skipped", False),
            "error": result.get("error")
        })
        
        if result["success"]:
            success_count += 1
            if result.get("skipped"):
                skipped_count += 1
    
    return {
        "success": True,
        "total_count": len(input_paths),
        "success_count": success_count,
        "skipped_count": skipped_count,
        "results": results
    }

def tts_text_with_filename(text: str, voice: str, rate: str = "+0%", volume: str = "+0%", pitch: str = "+0%", skip_exists: bool = True, export_formats: List[str] = None, output_path: str = None) -> dict:
    if export_formats is None:
        export_formats = []
    
    if not text or not text.strip():
        return {"success": False, "error": "文本为空 / Text is empty"}
    
    output_dir = get_output_dir()
    if output_path:
        output_path = Path(output_path)
    else:
        output_filename = generate_output_filename(text)
        output_path = output_dir / output_filename
    
    return tts_long_text(text, voice, str(output_path), rate, volume, pitch, skip_exists=skip_exists, export_formats=export_formats)

def get_tts_preview(text: str = "", byte_count: int = 0) -> Dict:
    if byte_count <= 0:
        if not text or not text.strip():
            return {"bytes": 0, "chunks": 0, "estimated_time": 0, "estimated_time_str": "0秒", "audio_duration": 0, "audio_duration_str": "0秒"}
        text = text.strip()
        byte_count = len(text.encode('utf-8'))
    
    chunks = split_text_by_length(text) if text else []
    chunk_count = len(chunks)
    est_time = estimate_time(byte_count)
    audio_dur = estimate_audio_duration(byte_count)
    
    return {
        "bytes": byte_count,
        "chunks": chunk_count,
        "estimated_time": est_time,
        "estimated_time_str": format_duration(est_time),
        "audio_duration": audio_dur,
        "audio_duration_str": format_duration(audio_dur)
    }
