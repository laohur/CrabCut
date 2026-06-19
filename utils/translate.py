"""
翻译功能
支持文本、音频、视频翻译
使用 Argos Translate (离线翻译)
"""

import os
os.environ["ARGOS_DEVICE_TYPE"] = "cpu"
os.environ["ARGOS_CHUNK_TYPE"] = "MINISBD"

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from utils.log_config import logger

LT_LANGUAGES = {
    "en": {"name": "English", "native": "英语"},
    "zh": {"name": "Chinese", "native": "中文"},
    "es": {"name": "Spanish", "native": "西班牙语"},
    "fr": {"name": "French", "native": "法语"},
    "de": {"name": "German", "native": "德语"},
    "it": {"name": "Italian", "native": "意大利语"},
    "ja": {"name": "Japanese", "native": "日语"},
    "ko": {"name": "Korean", "native": "韩语"},
    "pt": {"name": "Portuguese", "native": "葡萄牙语"},
    "ru": {"name": "Russian", "native": "俄语"},
    "ar": {"name": "Arabic", "native": "阿拉伯语"},
    "hi": {"name": "Hindi", "native": "印地语"},
    "tr": {"name": "Turkish", "native": "土耳其语"},
    "vi": {"name": "Vietnamese", "native": "越南语"},
    "th": {"name": "Thai", "native": "泰语"},
    "id": {"name": "Indonesian", "native": "印尼语"},
    "nl": {"name": "Dutch", "native": "荷兰语"},
    "pl": {"name": "Polish", "native": "波兰语"},
    "uk": {"name": "Ukrainian", "native": "乌克兰语"},
    "cs": {"name": "Czech", "native": "捷克语"},
    "sv": {"name": "Swedish", "native": "瑞典语"},
    "da": {"name": "Danish", "native": "丹麦语"},
    "fi": {"name": "Finnish", "native": "芬兰语"},
    "el": {"name": "Greek", "native": "希腊语"},
    "he": {"name": "Hebrew", "native": "希伯来语"},
    "hu": {"name": "Hungarian", "native": "匈牙利语"},
    "no": {"name": "Norwegian", "native": "挪威语"},
    "ro": {"name": "Romanian", "native": "罗马尼亚语"},
    "sk": {"name": "Slovak", "native": "斯洛伐克语"},
    "bg": {"name": "Bulgarian", "native": "保加利亚语"},
    "fa": {"name": "Persian", "native": "波斯语"},
    "ur": {"name": "Urdu", "native": "乌尔都语"},
    "az": {"name": "Azerbaijani", "native": "阿塞拜疆语"},
    "eu": {"name": "Basque", "native": "巴斯克语"},
    "ca": {"name": "Catalan", "native": "加泰罗尼亚语"},
    "eo": {"name": "Esperanto", "native": "世界语"},
    "gl": {"name": "Galician", "native": "加利西亚语"},
    "ga": {"name": "Irish", "native": "爱尔兰语"},
    "ky": {"name": "Kyrgyz", "native": "吉尔吉斯语"},
    "ms": {"name": "Malay", "native": "马来语"},
}

_installed_languages = None
_available_packages = None

def get_output_dir():
    from utils.converter import get_output_dir as base_get_output_dir
    return base_get_output_dir()

def get_installed_languages() -> List:
    global _installed_languages
    try:
        import argostranslate.translate
        _installed_languages = argostranslate.translate.get_installed_languages()
        return _installed_languages
    except ImportError:
        logger.warning("请安装 argostranslate: pip install argostranslate")
        return []

def get_available_packages() -> List:
    global _available_packages
    try:
        import argostranslate.package
        argostranslate.package.update_package_index()
        _available_packages = argostranslate.package.get_available_packages()
        return _available_packages
    except Exception as e:
        logger.warning(f"获取可用翻译包失败: {e}")
        return []

def get_available_languages() -> List[Dict]:
    installed = get_installed_languages()
    installed_codes = {lang.code for lang in installed}
    
    available = get_available_packages()
    available_codes = set()
    for pkg in available:
        available_codes.add(pkg.from_code)
        available_codes.add(pkg.to_code)
    
    all_codes = installed_codes | available_codes
    
    result = []
    for code in sorted(all_codes):
        if code in LT_LANGUAGES:
            result.append({
                "code": code,
                "name": LT_LANGUAGES[code]["name"],
                "native": LT_LANGUAGES[code]["native"],
                "installed": code in installed_codes
            })
    
    if not result:
        result = [{"code": k, "name": v["name"], "native": v["native"], "installed": k in installed_codes} 
                  for k, v in LT_LANGUAGES.items()]
    
    return result

def install_language_pair(from_code: str, to_code: str) -> Dict:
    try:
        import argostranslate.package
        
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        package_to_install = next(
            filter(
                lambda x: x.from_code == from_code and x.to_code == to_code,
                available_packages
            ),
            None
        )
        
        if package_to_install is None:
            return {"success": False, "error": f"未找到翻译包: {from_code} -> {to_code}"}
        
        download_path = package_to_install.download()
        argostranslate.package.install_from_path(download_path)
        
        global _installed_languages
        _installed_languages = None
        
        return {"success": True, "message": f"已安装翻译包: {from_code} -> {to_code}"}
    except Exception as e:
        logger.error(f"安装翻译包失败: {e}")
        return {"success": False, "error": str(e)}

def translate_text(text: str, source: str = "auto", target: str = "zh") -> Dict:
    if not text or not text.strip():
        return {"success": False, "error": "文本为空 / Text is empty"}

    logger.info(f"translate_text 调用: source={source}, target={target}, text={text[:50]}...")
    
    try:
        import argostranslate.translate
        from argostranslate import settings
        settings.auto_update = False
        
        installed_languages = argostranslate.translate.get_installed_languages()
        logger.info(f"已安装语言: {[l.code for l in installed_languages]}")
        
        from_lang = next((l for l in installed_languages if l.code == source), None)
        
        if source == "auto":
            try:
                from lingua import Language, LanguageDetectorBuilder
                lingua_langs = [Language.ENGLISH, Language.CHINESE, Language.JAPANESE, Language.KOREAN,
                              Language.FRENCH, Language.GERMAN, Language.SPANISH, Language.ITALIAN,
                              Language.PORTUGUESE, Language.RUSSIAN, Language.ARABIC]
                detector = LanguageDetectorBuilder.from_languages(*lingua_langs).build()
                detected = detector.detect_language_of(text[:100])
                if detected:
                    lingua_to_argos = {
                        "CHINESE": "zh",
                        "ENGLISH": "en",
                        "JAPANESE": "ja",
                        "KOREAN": "ko",
                        "FRENCH": "fr",
                        "GERMAN": "de",
                        "SPANISH": "es",
                        "ITALIAN": "it",
                        "PORTUGUESE": "pt",
                        "RUSSIAN": "ru",
                        "ARABIC": "ar",
                    }
                    detected_name = detected.name
                    source = lingua_to_argos.get(detected_name, detected_name.lower())
                    logger.info(f"语言检测: {detected_name} -> {source}")
                    from_lang = next((l for l in installed_languages if l.code == source), None)
            except Exception as e:
                logger.warning(f"语言检测失败: {e}")
                source = "en"
                from_lang = next((l for l in installed_languages if l.code == source), None)
        
        to_lang = next((l for l in installed_languages if l.code == target), None)
        
        if from_lang is None or to_lang is None:
            missing = []
            if from_lang is None:
                missing.append(source)
            if to_lang is None:
                missing.append(target)
            return {
                "success": False, 
                "error": f"未安装语言包: {', '.join(missing)}。请先安装对应的翻译包。"
            }
        
        translation = from_lang.get_translation(to_lang)
        translated = translation.translate(text)
        logger.info(f"翻译成功: '{text[:30]}...' -> '{translated[:30]}...'")
        
        return {
            "success": True,
            "original": text,
            "translated": translated,
            "source": source,
            "target": target
        }
    except Exception as e:
        logger.error(f"翻译失败: {e}")
        return {"success": False, "error": str(e)}

def translate_batch(texts: List[str], source: str = "auto", target: str = "zh") -> Dict:
    if not texts:
        return {"success": False, "error": "文本列表为空 / Text list is empty"}
    
    results = []
    for text in texts:
        result = translate_text(text, source, target)
        results.append(result)
    
    success_count = sum(1 for r in results if r["success"])
    return {
        "success": success_count > 0,
        "total": len(texts),
        "success_count": success_count,
        "results": results
    }

def split_text_for_translation(text: str, max_bytes: int = 5000) -> List[str]:
    if not text or not text.strip():
        return []
    
    text = text.strip()
    text_bytes = len(text.encode('utf-8'))
    
    if text_bytes <= max_bytes:
        return [text]
    
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

def translate_long_text(text: str, source: str = "auto", target: str = "zh", max_bytes: int = 5000) -> Dict:
    if not text or not text.strip():
        return {"success": False, "error": "文本为空 / Text is empty"}
    
    chunks = split_text_for_translation(text, max_bytes)
    if not chunks:
        return {"success": False, "error": "文本为空 / Text is empty"}
    
    if len(chunks) == 1:
        return translate_text(chunks[0], source, target)
    
    translated_parts = []
    for i, chunk in enumerate(chunks):
        result = translate_text(chunk, source, target)
        if result["success"]:
            translated_parts.append(result["translated"])
        else:
            logger.warning(f"分段 {i+1} 翻译失败: {result.get('error')}")
            translated_parts.append(chunk)
    
    full_translated = "".join(translated_parts)
    return {
        "success": True,
        "original": text,
        "translated": full_translated,
        "source": source,
        "target": target,
        "chunks": len(chunks)
    }

def parse_srt_for_translation(srt_content: str) -> List[Dict]:
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

def generate_srt_from_segments(segments: List[Dict], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"{seg['index']}\n")
            f.write(f"{seg['start']} --> {seg['end']}\n")
            f.write(f"{seg['text']}\n\n")

def translate_srt_content(srt_content: str, source: str = "auto", target: str = "zh") -> Dict:
    segments = parse_srt_for_translation(srt_content)
    if not segments:
        return {"success": False, "error": "SRT 内容为空或格式错误 / SRT content is empty or invalid"}
    
    translated_segments = []
    
    for i, seg in enumerate(segments):
        result = translate_text(seg["text"], source, target)
        if result["success"]:
            translated_segments.append({
                "index": seg["index"],
                "start": seg["start"],
                "end": seg["end"],
                "text": result["translated"]
            })
        else:
            translated_segments.append(seg)
    
    return {
        "success": True,
        "segments": translated_segments,
        "source": source,
        "target": target
    }

def translate_srt_file(srt_path: str, source: str = "auto", target: str = "zh", output_path: str = None) -> Dict:
    srt_path = Path(srt_path)
    if not srt_path.exists():
        return {"success": False, "error": f"文件不存在: {srt_path}"}
    
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()
    
    result = translate_srt_content(srt_content, source, target)
    if not result["success"]:
        return result
    
    if output_path is None:
        output_dir = get_output_dir()
        output_path = output_dir / f"{srt_path.stem}_{target}.srt"
    else:
        output_path = Path(output_path)
    
    generate_srt_from_segments(result["segments"], str(output_path))
    
    return {
        "success": True,
        "output": str(output_path),
        "segments": result["segments"]
    }

def parse_json_for_translation(json_content: str) -> List[Dict]:
    try:
        data = json.loads(json_content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "segments" in data:
                return data["segments"]
            elif "text" in data:
                return [{"index": 1, "text": data["text"]}]
        return []
    except json.JSONDecodeError:
        return []

def translate_json_content(json_content: str, source: str = "auto", target: str = "zh") -> Dict:
    segments = parse_json_for_translation(json_content)
    if not segments:
        return {"success": False, "error": "JSON 内容为空或格式错误 / JSON content is empty or invalid"}
    
    translated_segments = []
    for seg in segments:
        if "text" in seg:
            result = translate_text(seg["text"], source, target)
            new_seg = seg.copy()
            if result["success"]:
                new_seg["text"] = result["translated"]
            translated_segments.append(new_seg)
        else:
            translated_segments.append(seg)
    
    return {
        "success": True,
        "segments": translated_segments,
        "source": source,
        "target": target
    }

def translate_json_file(json_path: str, source: str = "auto", target: str = "zh", output_path: str = None) -> Dict:
    json_path = Path(json_path)
    if not json_path.exists():
        return {"success": False, "error": f"文件不存在: {json_path}"}
    
    with open(json_path, "r", encoding="utf-8") as f:
        json_content = f.read()
    
    result = translate_json_content(json_content, source, target)
    if not result["success"]:
        return result
    
    if output_path is None:
        output_dir = get_output_dir()
        output_path = output_dir / f"{json_path.stem}_{target}.json"
    else:
        output_path = Path(output_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"segments": result["segments"]}, f, ensure_ascii=False, indent=2)
    
    return {
        "success": True,
        "output": str(output_path),
        "segments": result["segments"]
    }

def translate_file(file_path: str, source: str = "auto", target: str = "zh") -> Dict:
    file_path = Path(file_path)
    if not file_path.exists():
        return {"success": False, "error": f"文件不存在: {file_path}"}
    
    suffix = file_path.suffix.lower()
    
    if suffix == ".srt":
        return translate_srt_file(str(file_path), source, target)
    elif suffix == ".json":
        return translate_json_file(str(file_path), source, target)
    elif suffix == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        result = translate_long_text(text, source, target)
        if result["success"]:
            output_dir = get_output_dir()
            output_path = output_dir / f"{file_path.stem}_{target}.txt"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result["translated"])
            result["output"] = str(output_path)
        return result
    else:
        return {"success": False, "error": f"不支持的文件格式: {suffix}"}

def translate_audio_video(file_path: str, source: str = "auto", target: str = "zh", 
                          output_formats: List[str] = None, asr_model: str = None,
                          use_punc: bool = True) -> Dict:
    if output_formats is None:
        output_formats = ["srt", "json"]
    
    file_path = Path(file_path)
    if not file_path.exists():
        return {"success": False, "error": f"文件不存在: {file_path}"}
    
    from utils.asr import asr_single_file, asr_faster_whisper, ALL_ASR_MODELS

    if asr_model is None:
        lang_to_asr = {
            "zh": "paraformer-zh",
            "en": "paraformer-en",
            "auto": "whisper-large-v3-turbo"
        }
        asr_model = lang_to_asr.get(source, "whisper-large-v3-turbo")
    
    model_info = ALL_ASR_MODELS.get(asr_model, {})
    engine = model_info.get("engine", "funasr")
    
    if engine == "whisper":
        asr_result = asr_faster_whisper(
            str(file_path),
            model_size=model_info.get("size", "base"),
            language=source if source != "auto" else None,
        )
    else:
        asr_config = ALL_ASR_MODELS.get(asr_model, ALL_ASR_MODELS["sensevoice"])
        punc_model = asr_config.get("punc") if use_punc else None
        asr_result = asr_single_file(
            str(file_path),
            asr_model=asr_config["asr"],
            vad_model=asr_config.get("vad"),
            punc_model=punc_model,
            language=source if source != "auto" else "auto"
        )
    if not asr_result["success"]:
        return {"success": False, "error": f"ASR 失败: {asr_result.get('error')}"}
    
    segments = asr_result.get("segments", [])
    if not segments:
        return {"success": False, "error": "ASR 结果为空 / ASR result is empty"}
    
    translated_segments = []
    for seg in segments:
        text = seg.get("text", "")
        if text:
            result = translate_text(text, source, target)
            new_seg = seg.copy()
            if result["success"]:
                new_seg["text"] = result["translated"]
            translated_segments.append(new_seg)
        else:
            translated_segments.append(seg)
    
    output_dir = get_output_dir()
    output_stem = f"{file_path.stem}_{target}"
    output_files = []
    
    if "srt" in output_formats:
        srt_path = output_dir / f"{output_stem}.srt"
        srt_segments = []
        for seg in translated_segments:
            srt_segments.append({
                "index": seg.get("index", 1),
                "start": seg.get("start", "00:00:00,000"),
                "end": seg.get("end", "00:00:00,000"),
                "text": seg.get("text", "")
            })
        generate_srt_from_segments(srt_segments, str(srt_path))
        output_files.append(str(srt_path))
    
    if "json" in output_formats:
        json_path = output_dir / f"{output_stem}.json"
        json_segments = []
        for seg in translated_segments:
            json_segments.append({
                "index": seg.get("index", 1),
                "start": seg.get("start_sec", 0.0),
                "end": seg.get("end_sec", 0.0),
                "text": seg.get("text", "")
            })
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"segments": json_segments}, f, ensure_ascii=False, indent=2)
        output_files.append(str(json_path))
    
    if "txt" in output_formats:
        txt_path = output_dir / f"{output_stem}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            for seg in translated_segments:
                f.write(seg.get("text", "") + "\n")
        output_files.append(str(txt_path))
    
    return {
        "success": True,
        "output_files": output_files,
        "segments": translated_segments
    }
