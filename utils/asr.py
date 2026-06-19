"""
ASR:
    iic/SenseVoiceSmall
    iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch
    iic/speech_paraformer_asr-en-16k-vocab4199-pytorch   
VAD: 
    iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
punc:
    iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch
    iic/punc_ct-transformer_cn-en-common-vocab471067-large
speaker:
    iic/speech_campplus_sv_zh-cn_16k-common
    iic/speech_campplus_sv_zh_en_16k-common_advanced
"""

import json
from pathlib import Path
from utils.log_config import logger

_model_cache = {}

ASR_COMBOS = {
    "paraformer-zh": {
        "name": "Paraformer 中文",
        "engine": "funasr",
        "asr": "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "vad": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        "punc": "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
        "spk": "iic/speech_campplus_sv_zh-cn_16k-common",
        "hotword_supported": True,
        "spk_supported": True,
    },
    "paraformer-en": {
        "name": "Paraformer 英文",
        "engine": "funasr",
        "asr": "iic/speech_paraformer_asr-en-16k-vocab4199-pytorch",
        "vad": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        "punc": "iic/punc_ct-transformer_cn-en-common-vocab471067-large",
        "spk": "iic/speech_campplus_sv_zh_en_16k-common_advanced",
        "hotword_supported": True,
        "spk_supported": True,
    },
    "sensevoice": {
        "name": "SenseVoice 多语言",
        "engine": "funasr",
        "asr": "iic/SenseVoiceSmall",
        "vad": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        "punc": "",
        "spk": "",
        "hotword_supported": False,
        "spk_supported": False,
    },
}

WHISPER_MODELS = {
    "whisper-tiny": {"name": "Whisper Tiny", "engine": "whisper", "size": "tiny", "params": "39M"},
    "whisper-tiny-en": {"name": "Whisper Tiny (EN)", "engine": "whisper", "size": "tiny.en", "params": "39M"},
    "whisper-base": {"name": "Whisper Base", "engine": "whisper", "size": "base", "params": "74M"},
    "whisper-base-en": {"name": "Whisper Base (EN)", "engine": "whisper", "size": "base.en", "params": "74M"},
    "whisper-small": {"name": "Whisper Small", "engine": "whisper", "size": "small", "params": "244M"},
    "whisper-small-en": {"name": "Whisper Small (EN)", "engine": "whisper", "size": "small.en", "params": "244M"},
    "whisper-medium": {"name": "Whisper Medium", "engine": "whisper", "size": "medium", "params": "769M"},
    "whisper-medium-en": {"name": "Whisper Medium (EN)", "engine": "whisper", "size": "medium.en", "params": "769M"},
    "whisper-large": {"name": "Whisper Large", "engine": "whisper", "size": "large-v2", "params": "1550M"},
    "whisper-large-v3": {"name": "Whisper Large V3", "engine": "whisper", "size": "large-v3", "params": "1550M"},
    "whisper-large-v3-turbo": {"name": "Whisper Large V3 Turbo", "engine": "whisper", "size": "large-v3-turbo", "params": "809M"},
}

ALL_ASR_MODELS = {**ASR_COMBOS, **WHISPER_MODELS}

PRESET_CONFIGS = ASR_COMBOS

def get_output_dir():
    from utils.converter import get_output_dir as base_get_output_dir
    return base_get_output_dir()

def get_json_path(file_path: Path) -> Path:
    output_dir = get_output_dir()
    return output_dir / f"{file_path.stem}-asr.json"

def load_json_result(file_path: Path) -> dict:
    json_path = get_json_path(file_path)
    if json_path.exists():
        logger.info(f"加载已有结果 / Load cached result: {json_path.as_posix()}")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_json_result(file_path: Path, data: dict):
    json_path = get_json_path(file_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"保存结果 / Save result: {json_path.as_posix()}")
    return json_path

def get_model(asr_model: str, vad_model: str = None, punc_model: str = None, spk_model: str = None, vad_kwargs: dict = None):
    global _model_cache
    
    # 处理空字符串为None
    vad_model = vad_model if vad_model else None
    punc_model = punc_model if punc_model else None
    spk_model = spk_model if spk_model else None
    vad_kwargs = vad_kwargs if vad_kwargs else None
    
    cache_key = (asr_model, vad_model, punc_model, spk_model)
    
    if cache_key not in _model_cache:
        from funasr import AutoModel
        
        kwargs = {"model": asr_model}
        
        # iic/ 开头的模型需要指定 model_hub
        if asr_model.startswith("iic/"):
            kwargs["model_hub"] = "modelscope"
        
        # SenseVoiceSmall 需要特殊参数（严格按照官方文档）
        if asr_model == "iic/SenseVoiceSmall":
            kwargs["trust_remote_code"] = True
            kwargs["remote_code"] = "./model.py"
        
        # 所有模型使用用户指定的辅助模型
        if vad_model:
            kwargs["vad_model"] = vad_model
        if punc_model:
            kwargs["punc_model"] = punc_model
        if spk_model:
            kwargs["spk_model"] = spk_model
        if vad_kwargs:
            kwargs["vad_kwargs"] = vad_kwargs
        
        logger.info(f"加载ASR模型 / Loading ASR model: {asr_model} {kwargs}")
        _model_cache[cache_key] = AutoModel(**kwargs)
        logger.success(f"ASR模型加载完成 / ASR model {asr_model} loaded")
    
    return _model_cache[cache_key]

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    millis = int((secs - int(secs)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{millis:03d}"

def generate_srt(segments: list) -> str:
    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"]
        speaker = seg.get("speaker", "")
        if speaker:
            text = f"[{speaker}] {text}"
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(srt_lines)

def asr_single_file(
    file_path: str,
    asr_model: str,
    vad_model: str = None,
    punc_model: str = None,
    spk_model: str = None,
    enable_diarization: bool = True,
    hotword: str = "",
    vad_kwargs: dict = None,
    language: str = "auto",
) -> dict:
    if not file_path or not Path(file_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    file_path = Path(file_path)
    
    cached = load_json_result(file_path)
    if cached:
        cached["from_cache"] = True
        return cached
    
    model = get_model(asr_model, vad_model, punc_model, spk_model, vad_kwargs)
    
    logger.info(f"开始语音识别 / Start ASR: {file_path.as_posix()}")
    
    # 支持时间戳/说话人识别的模型白名单
    timestamp_supported_models = [
        "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "iic/speech_paraformer_asr-en-16k-vocab4199-pytorch",
    ]
    
    # 如果启用说话人分离但模型不支持 timestamp，则禁用说话人分离
    if enable_diarization and spk_model:
        if asr_model not in timestamp_supported_models:
            logger.warning(f"当前模型 {asr_model} 不支持说话人分离")
            enable_diarization = False
    
    kwargs = {
        "input": file_path.as_posix(),
        "cache": {},
    }
    
    # SenseVoiceSmall 特殊参数配置
    if asr_model == "iic/SenseVoiceSmall":
        # 根据语言设置映射：zh -> "zn", en -> "en", mlt -> "auto"
        lang_map = {"zh": "zn", "en": "en", "mlt": "auto"}
        sensevoice_lang = lang_map.get(language, "auto")
        kwargs["language"] = sensevoice_lang  # "zn", "en", "yue", "ja", "ko", "nospeech"
        kwargs["use_itn"] = True
        kwargs["batch_size_s"] = 60
        kwargs["merge_vad"] = True
        kwargs["merge_length_s"] = 15
    else:
        kwargs["batch_size_s"] = 60
        kwargs["return_raw_text"] = True
        kwargs["is_final"] = True
        kwargs["hotword"] = hotword or ""
        
        # 英文模型特殊参数（仅 vocab4199 支持时间戳）
        if asr_model == "iic/speech_paraformer_asr-en-16k-vocab4199-pytorch":
            kwargs["pred_timestamp"] = True
            kwargs["en_post_proc"] = True
        
        if enable_diarization and spk_model:
            kwargs["return_spk_res"] = True
            kwargs["sentence_timestamp"] = True
        else:
            kwargs["return_spk_res"] = False
            kwargs["sentence_timestamp"] = True
    
    result = model.generate(**kwargs)
    
    segments = []
    for res in result:
        # SenseVoiceSmall 特殊处理
        if asr_model == "iic/SenseVoiceSmall":
            from funasr.utils.postprocess_utils import rich_transcription_postprocess
            text = res.get("text", "")
            # 使用官方推荐的后处理方法
            processed_text = rich_transcription_postprocess(text)
            segments.append({
                "start": 0,
                "end": res.get("duration", 0) / 1000.0,
                "text": processed_text,
                "speaker": None
            })
        else:
            sentence_info = res.get("sentence_info", [])
            
            if sentence_info:
                for sent in sentence_info:
                    spk = sent.get("spk")
                    segments.append({
                        "start": sent.get("start", 0) / 1000.0,
                        "end": sent.get("end", 0) / 1000.0,
                        "text": sent.get("text", ""),
                        "speaker": spk
                    })
            else:
                segments.append({
                    "start": 0,
                    "end": res.get("duration", 0) / 1000.0,
                    "text": res.get("text", ""),
                    "speaker": None
                })
    
    full_text = "".join([s["text"] for s in segments])
    
    asr_result = {
        "success": True,
        "text": full_text,
        "segments": segments,
        "audio_path": file_path.as_posix(),
        "from_cache": False
    }
    
    save_json_result(file_path, asr_result)
    logger.success(f"语音识别成功 / ASR success: {len(segments)}个片段 / segments")
    
    return asr_result

_whisper_model_cache = {}

def get_whisper_model(model_size: str, device: str = "cuda", compute_type: str = "float16"):
    global _whisper_model_cache

    actual_device = device
    actual_compute_type = compute_type

    if device == "cuda":
        import torch
        if not torch.cuda.is_available():
            logger.warning("CUDA 不可用，回退到 CPU / CUDA not available, falling back to CPU")
            actual_device = "cpu"
            actual_compute_type = "int8"

    cache_key = (model_size, actual_device, actual_compute_type)

    if cache_key not in _whisper_model_cache:
        from faster_whisper import WhisperModel
        logger.info(f"加载 Faster-Whisper {model_size} 模型 ({actual_device})...")
        _whisper_model_cache[cache_key] = WhisperModel(
            model_size,
            device=actual_device,
            compute_type=actual_compute_type,
        )
        logger.success(f"Faster-Whisper {model_size} 模型加载完成")

    return _whisper_model_cache[cache_key]

def asr_faster_whisper(
    file_path: str,
    model_size: str = "base",
    language: str = "auto",
    compute_type: str = "float16",
    device: str = "cuda",
) -> dict:
    if not file_path or not Path(file_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}

    file_path = Path(file_path)

    cached = load_json_result(file_path)
    if cached:
        cached["from_cache"] = True
        return cached

    whisper_model = get_whisper_model(model_size, device, compute_type)

    logger.info(f"开始语音识别 / Start ASR: {file_path.as_posix()}")

    language_param = None if language == "auto" else language

    segments, info = whisper_model.transcribe(
        str(file_path),
        language=language_param,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    result_segments = []
    for seg in segments:
        result_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "speaker": None
        })

    full_text = "".join([s["text"] for s in result_segments])

    asr_result = {
        "success": True,
        "text": full_text,
        "segments": result_segments,
        "audio_path": file_path.as_posix(),
        "from_cache": False,
        "model": f"faster_whisper_{model_size}",
        "language_detected": info.language if info.language else language
    }

    save_json_result(file_path, asr_result)
    logger.success(f"Faster-Whisper 语音识别成功 / ASR success: {len(result_segments)}个片段 / segments")

    return asr_result

def asr_batch_files(
    file_paths: list,
    asr_model: str,
    vad_model: str = None,
    punc_model: str = None,
    spk_model: str = None,
    enable_diarization: bool = True,
    hotword: str = "",
    vad_kwargs: dict = None,
    language: str = "auto",
) -> dict:
    if not file_paths:
        return {"success": False, "error": "没有输入文件 / No input files"}
    
    model = get_model(asr_model, vad_model, punc_model, spk_model, vad_kwargs)
    
    # 支持时间戳/说话人识别的模型白名单
    timestamp_supported_models = [
        "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "iic/speech_paraformer_asr-en-16k-vocab4199-pytorch",
    ]
    
    # 如果启用说话人分离但模型不支持 timestamp，则禁用说话人分离
    if enable_diarization and spk_model:
        if asr_model not in timestamp_supported_models:
            logger.warning(f"当前模型 {asr_model} 不支持说话人分离")
            enable_diarization = False
    
    all_results = []
    success_count = 0
    cache_count = 0
    
    for file_path in file_paths:
        if hasattr(file_path, 'name'):
            path = file_path.name
        elif isinstance(file_path, dict):
            path = file_path.get("name")
        else:
            path = file_path
        
        file_path = Path(path)
        
        cached = load_json_result(file_path)
        if cached:
            all_results.append({
                "file": file_path.as_posix(),
                "success": True,
                "text": cached.get("text", ""),
                "segments": cached.get("segments", []),
                "from_cache": True
            })
            success_count += 1
            cache_count += 1
            continue
        
        logger.info(f"开始语音识别 / Start ASR: {file_path.as_posix()}")
        
        kwargs = {
            "input": file_path.as_posix(),
            "cache": {},
        }
        
        # SenseVoiceSmall 特殊参数配置
        if asr_model == "iic/SenseVoiceSmall":
            # 根据语言设置映射：zh -> "zn", en -> "en", mlt -> "auto"
            lang_map = {"zh": "zn", "en": "en", "mlt": "auto"}
            sensevoice_lang = lang_map.get(language, "auto")
            kwargs["language"] = sensevoice_lang  # "zn", "en", "yue", "ja", "ko", "nospeech"
            kwargs["use_itn"] = True
            kwargs["batch_size_s"] = 60
            kwargs["merge_vad"] = True
            kwargs["merge_length_s"] = 15
        else:
            kwargs["batch_size_s"] = 60
            kwargs["return_raw_text"] = True
            kwargs["is_final"] = True
            kwargs["hotword"] = hotword or ""
            
            # 英文模型特殊参数（仅 vocab4199 支持时间戳）
            if asr_model == "iic/speech_paraformer_asr-en-16k-vocab4199-pytorch":
                kwargs["pred_timestamp"] = True
                kwargs["en_post_proc"] = True
            
            if enable_diarization and spk_model:
                kwargs["return_spk_res"] = True
                kwargs["sentence_timestamp"] = True
            else:
                kwargs["return_spk_res"] = False
                kwargs["sentence_timestamp"] = True
        
        result = model.generate(**kwargs)
        
        segments = []
        for res in result:
            # SenseVoiceSmall 特殊处理
            if asr_model == "iic/SenseVoiceSmall":
                from funasr.utils.postprocess_utils import rich_transcription_postprocess
                text = res.get("text", "")
                # 使用官方推荐的后处理方法
                processed_text = rich_transcription_postprocess(text)
                segments.append({
                    "start": 0,
                    "end": res.get("duration", 0) / 1000.0,
                    "text": processed_text,
                    "speaker": None
                })
            else:
                sentence_info = res.get("sentence_info", [])
                
                if sentence_info:
                    for sent in sentence_info:
                        spk = sent.get("spk")
                        segments.append({
                            "start": sent.get("start", 0) / 1000.0,
                            "end": sent.get("end", 0) / 1000.0,
                            "text": sent.get("text", ""),
                            "speaker": spk
                        })
                else:
                    segments.append({
                        "start": 0,
                        "end": res.get("duration", 0) / 1000.0,
                        "text": res.get("text", ""),
                        "speaker": None
                    })
        
        full_text = "".join([s["text"] for s in segments])
        
        asr_result = {
            "success": True,
            "text": full_text,
            "segments": segments,
            "audio_path": file_path.as_posix(),
            "from_cache": False
        }
        
        save_json_result(file_path, asr_result)
        logger.success(f"语音识别成功 / ASR success: {len(segments)}个片段 / segments")
        
        all_results.append({
            "file": file_path.as_posix(),
            "success": True,
            "text": full_text,
            "segments": segments,
            "from_cache": False
        })
        success_count += 1
    
    return {
        "success": True,
        "total_count": len(file_paths),
        "success_count": success_count,
        "cache_count": cache_count,
        "results": all_results
    }
