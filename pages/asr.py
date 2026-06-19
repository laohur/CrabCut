import gradio as gr
import json
from pathlib import Path
from utils.asr import (
    get_output_dir, get_json_path, generate_srt,
    asr_single_file, asr_batch_files, asr_faster_whisper,
    ALL_ASR_MODELS
)
from utils.i18n import translate_text
from utils.log_config import logger

ASR_LANGUAGES = [
    ("自动 / Auto", "auto"),
    ("中文", "zh"),
    ("英语 / English", "en"),
    ("日语 / Japanese", "ja"),
    ("韩语 / Korean", "ko"),
    ("法语 / French", "fr"),
    ("德语 / German", "de"),
    ("西班牙语 / Spanish", "es"),
    ("俄语 / Russian", "ru"),
    ("阿拉伯语 / Arabic", "ar"),
]

def create_asr_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("语音识别 (ASR)" if lang == 'zh' else "Speech Recognition (ASR)"))

        with gr.Row():
            with gr.Column(scale=1):
                asr_input = gr.File(
                    label="选择音频文件（支持多选）" if lang == 'zh' else "Select Audio Files (Multiple)",
                    file_types=[".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".mp4", ".avi", ".mkv", ".mov"],
                    file_count="multiple"
                )

                asr_model = gr.Dropdown(
                    choices=[(f"{v['name']} ({v.get('params', '')})", k) for k, v in ALL_ASR_MODELS.items()],
                    value="whisper-large-v3-turbo",
                    label="模型" if lang == 'zh' else "Model"
                )

                asr_lang = gr.Dropdown(
                    choices=ASR_LANGUAGES,
                    value="auto",
                    label="识别语言" if lang == 'zh' else "Language"
                )

                with gr.Row():
                    use_spk = gr.Checkbox(
                        value=False,
                        label="启用说话人识别" if lang == 'zh' else "Enable Speaker Diarization",
                        interactive=True
                    )
                    use_punc = gr.Checkbox(
                        value=True,
                        label="启用标点" if lang == 'zh' else "Enable Punctuation",
                        interactive=True
                    )

                hotword = gr.Textbox(
                    label="热词（空格分隔）" if lang == 'zh' else "Hotwords (space separated)",
                    placeholder="多个热词用空格分隔 / Separate hotwords with spaces",
                    value=""
                )

                validation_msg = gr.HTML(
                    value="<span style='color: green;'>✓ 配置有效 / Valid config</span>"
                )

            with gr.Column(scale=1):
                with gr.Row():
                    output_json = gr.Checkbox(value=True, label="输出JSON" if lang == 'zh' else "Output JSON")
                    output_txt = gr.Checkbox(value=True, label="输出TXT" if lang == 'zh' else "Output TXT")
                    output_srt = gr.Checkbox(value=True, label="输出SRT" if lang == 'zh' else "Output SRT")

                asr_btn = gr.Button("🎤 " + ("转写" if lang == 'zh' else "Transcribe"), variant="primary")
                asr_status = gr.Textbox(label="状态" if lang == 'zh' else "Status", interactive=False)

                asr_output = gr.Textbox(
                    label="转写结果" if lang == 'zh' else "Transcription Result",
                    lines=20,
                    interactive=False
                )

                output_files = gr.File(label="输出文件" if lang == 'zh' else "Output Files")

        last_result = gr.State(None)

        def update_model_options(model_key):
            model_info = ALL_ASR_MODELS.get(model_key, {})
            engine = model_info.get("engine", "whisper")
            spk_supported = model_info.get("spk_supported", False)
            hotword_supported = model_info.get("hotword_supported", False)
            punc_supported = engine == "funasr"

            messages = []
            if not spk_supported:
                messages.append("<span style='color: orange;'>⚠️ 当前模型不支持说话人识别</span>" if engine == "funasr" else "")
            if not hotword_supported and engine == "funasr":
                messages.append("<span style='color: orange;'>⚠️ 当前模型不支持热词</span>")

            if not messages or all(not m for m in messages):
                msg = "<span style='color: green;'>✓ 配置有效 / Valid config</span>"
            else:
                msg = "<br>".join([m for m in messages if m])

            return gr.Checkbox(interactive=spk_supported), gr.Checkbox(interactive=punc_supported), gr.Textbox(interactive=hotword_supported), msg

        asr_model.change(
            update_model_options,
            inputs=[asr_model],
            outputs=[use_spk, use_punc, hotword, validation_msg]
        )

        def do_asr(files, model_key, language, enable_spk, enable_punc, hotword_text, out_json, out_txt, out_srt):
            logger.info(f"开始ASR转写 / Start ASR: model={model_key}, files={len(files) if files else 0}, 标点={enable_punc}")

            if not files:
                return "❌ 请选择文件 / Please select files", "", None, None

            model_info = ALL_ASR_MODELS.get(model_key, {})
            engine = model_info.get("engine", "whisper")

            if engine == "whisper":
                if len(files) == 1:
                    file = files[0]
                    file_path = Path(file.name)

                    logger.info(f"开始 Whisper 转写: {file_path.name}, model={model_key}, lang={language}")

                    result = asr_faster_whisper(
                        file.name,
                        model_size=model_info.get("size", "base"),
                        language=language,
                    )

                    if not result["success"]:
                        logger.error(f"Whisper 转写失败: {result['error']}")
                        return f"❌ {result['error']}", "", None, None

                    cache_mark = " (已有 / cached)" if result.get("from_cache") else ""
                    status = f"✅ 转写成功 / Transcribed{cache_mark}: {len(result['segments'])}个片段 / segments"

                    display_text = "\n".join([seg["text"] for seg in result["segments"]])

                    output_file_list = []
                    if out_json:
                        output_file_list.append(get_json_path(file_path).as_posix())
                    if out_txt:
                        txt_path = get_output_dir() / f"{file_path.stem}-asr.txt"
                        txt_path.write_text(display_text, encoding="utf-8")
                        output_file_list.append(txt_path.as_posix())
                    if out_srt:
                        srt_content = generate_srt(result["segments"])
                        srt_path = get_output_dir() / f"{file_path.stem}-asr.srt"
                        srt_path.write_text(srt_content, encoding="utf-8")
                        output_file_list.append(srt_path.as_posix())

                    logger.success(f"ASR 完成: {file_path.name}, {len(result['segments'])}个片段")
                    return status, display_text, output_file_list if output_file_list else None, result
                else:
                    logger.error("Whisper 模式暂不支持批量处理")
                    return "❌ Whisper 模式暂不支持批量处理 / Batch not supported in Whisper mode", "", None, None

            asr_model_name = model_info.get("asr")
            vad_model = model_info.get("vad")
            punc_model = model_info.get("punc", "") if enable_punc else None
            spk_model = model_info.get("spk", "") if enable_spk and model_info.get("spk_supported") else ""

            final_hotword = hotword_text if model_info.get("hotword_supported", False) else ""

            if len(files) == 1:
                file = files[0]
                file_path = Path(file.name)

                logger.info(f"开始 FunASR 转写: {file_path.name}")

                result = asr_single_file(
                    file.name,
                    asr_model=asr_model_name,
                    vad_model=vad_model,
                    punc_model=punc_model,
                    spk_model=spk_model,
                    enable_diarization=bool(spk_model),
                    hotword=final_hotword,
                    vad_kwargs={"max_single_segment_time": 30000},
                    language=language,
                )

                if not result["success"]:
                    logger.error(f"FunASR 转写失败: {result['error']}")
                    return f"❌ {result['error']}", "", None, None

                cache_mark = " (已有 / cached)" if result.get("from_cache") else ""
                status = f"✅ 转写成功 / Transcribed{cache_mark}: {len(result['segments'])}个片段 / segments"

                display_lines = []
                current_spk = None
                for seg in result["segments"]:
                    spk = seg.get("speaker")
                    if spk is not None and spk != current_spk:
                        display_lines.append(f"[{spk}]")
                        current_spk = spk
                    display_lines.append(seg["text"])
                display_text = "\n".join(display_lines)

                output_file_list = []
                if out_json:
                    output_file_list.append(get_json_path(file_path).as_posix())
                if out_txt:
                    txt_lines = []
                    current_spk = None
                    for seg in result["segments"]:
                        spk = seg.get("speaker")
                        if spk is not None and spk != current_spk:
                            txt_lines.append(f"[{spk}]")
                            current_spk = spk
                        txt_lines.append(seg["text"])
                    txt_path = get_output_dir() / f"{file_path.stem}-asr.txt"
                    txt_path.write_text("\n".join(txt_lines), encoding="utf-8")
                    output_file_list.append(txt_path.as_posix())
                if out_srt:
                    srt_content = generate_srt(result["segments"])
                    srt_path = get_output_dir() / f"{file_path.stem}-asr.srt"
                    srt_path.write_text(srt_content, encoding="utf-8")
                    output_file_list.append(srt_path.as_posix())

                logger.success(f"ASR 完成: {file_path.name}, {len(result['segments'])}个片段")
                return status, display_text, output_file_list if output_file_list else None, result

            result = asr_batch_files(
                files,
                asr_model=asr_model_name,
                vad_model=vad_model,
                punc_model=punc_model,
                spk_model=spk_model,
                enable_diarization=bool(spk_model),
                hotword=final_hotword,
                vad_kwargs={"max_single_segment_time": 30000},
                language=language,
            )

            if not result["success"]:
                logger.error(f"批量 ASR 失败: {result['error']}")
                return f"❌ {result['error']}", "", None, None

            status_lines = [
                f"✅ 批量转写完成 / Batch done: {result['success_count']}/{result['total_count']} 成功 / success",
                f"📦 已有结果 / Cached: {result['cache_count']}"
            ]

            all_texts = []
            for r in result["results"]:
                if r["success"]:
                    cache_mark = " (已有 / cached)" if r.get("from_cache") else ""
                    status_lines.append(f"  ✅ {Path(r['file']).name}: {len(r.get('segments', []))}个片段 / segments{cache_mark}")

                    display_lines = []
                    current_spk = None
                    for seg in r.get("segments", []):
                        spk = seg.get("speaker")
                        if spk is not None and spk != current_spk:
                            display_lines.append(f"[{spk}]")
                            current_spk = spk
                        display_lines.append(seg.get("text", ""))
                    all_texts.append(f"=== {Path(r['file']).name} ===\n" + "\n".join(display_lines))

            first_chars = "".join(Path(r['file']).stem[0] for r in result["results"] if r["success"])[:10]
            output_name = f"{first_chars}-asr"

            output_file_list = []
            if out_txt:
                txt_lines = []
                current_spk = None
                for r in result["results"]:
                    if r["success"]:
                        for seg in r.get("segments", []):
                            spk = seg.get("speaker")
                            if spk is not None and spk != current_spk:
                                txt_lines.append(f"[{spk}]")
                                current_spk = spk
                            txt_lines.append(seg.get("text", ""))
                txt_path = get_output_dir() / f"{output_name}.txt"
                txt_path.write_text("\n".join(txt_lines), encoding="utf-8")
                output_file_list.append(txt_path.as_posix())

            if out_json:
                json_path = get_output_dir() / f"{output_name}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result["results"], f, ensure_ascii=False, indent=2)
                output_file_list.append(json_path.as_posix())

            if out_srt:
                all_segments = []
                for r in result["results"]:
                    if r["success"]:
                        all_segments.extend(r.get("segments", []))
                srt_content = generate_srt(all_segments)
                srt_path = get_output_dir() / f"{output_name}.srt"
                srt_path.write_text(srt_content, encoding="utf-8")
                output_file_list.append(srt_path.as_posix())

            logger.success(f"批量 ASR 完成: {result['success_count']}/{result['total_count']} 成功")
            return "\n".join(status_lines), "\n\n".join(all_texts), output_file_list if output_file_list else None, result

        asr_btn.click(do_asr, inputs=[asr_input, asr_model, asr_lang, use_spk, use_punc, hotword, output_json, output_txt, output_srt],
                     outputs=[asr_status, asr_output, output_files, last_result])
