import gradio as gr
from pathlib import Path
from utils.translate import (
    get_available_languages, translate_long_text, translate_file,
    translate_audio_video, LT_LANGUAGES, install_language_pair
)
from utils.asr import ALL_ASR_MODELS
from utils.i18n import translate_text
from utils.log_config import logger

def create_translate_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("翻译工具" if lang == 'zh' else "Translator"))
        
        is_zh = lang == 'zh'
        lang_choices = [(f"{v['name']}-{v['native']}" if is_zh else f"{v['native']}-{v['name']}", k) for k, v in LT_LANGUAGES.items()]

        with gr.Row():
            source_lang = gr.Dropdown(
                choices=[("自动检测 / Auto Detect", "auto")] + lang_choices,
                value="auto",
                label="源语言" if is_zh else "Source Language",
                filterable=True,
                scale=2
            )
            target_lang = gr.Dropdown(
                choices=lang_choices,
                value="zh",
                label="目标语言" if is_zh else "Target Language",
                filterable=True,
                scale=2
            )
        
        with gr.Row():
            swap_lang_btn = gr.Button("🔄 " + ("交换语言" if lang == 'zh' else "Swap Languages"), variant="secondary")
            install_btn = gr.Button("📥 " + ("安装语言包" if lang == 'zh' else "Install Language Pack"), variant="secondary")
        
        def do_install(from_code, to_code):
            logger.info(f"开始安装语言包: {from_code} -> {to_code}")
            if from_code == "auto":
                error_msg = "❌ 无法从\"自动检测\"安装语言包，请选择具体源语言 / Cannot install from 'auto', please select a specific source language"
                logger.error(f"语言包安装失败: 源语言不能是 auto")
                return error_msg
            result = install_language_pair(from_code, to_code)
            if result["success"]:
                logger.success(f"语言包安装成功: {result['message']}")
                return f"📥 {result['message']}"
            else:
                logger.error(f"语言包安装失败: {result['error']}")
                return f"❌ {result['error']}"
        
        install_btn.click(
            do_install,
            inputs=[source_lang, target_lang],
            outputs=[install_btn]
        )
        
        def reset_install_btn():
            return "📥 " + ("安装语言包" if lang == 'zh' else "Install Language Pack")

        source_lang.change(reset_install_btn, outputs=[install_btn])
        target_lang.change(reset_install_btn, outputs=[install_btn])
        
        gr.Markdown("---")
        
        with gr.Tabs():
            with gr.TabItem("📝 " + ("文本翻译" if lang == 'zh' else "Text Translation")):
                with gr.Row():
                    with gr.Column(scale=1):
                        text_input = gr.Textbox(
                            label="输入文本" if lang == 'zh' else "Input Text",
                            lines=15,
                            placeholder="在此输入要翻译的文本..." if lang == 'zh' else "Enter text to translate..."
                        )
                    with gr.Column(scale=1):
                        text_translate_btn = gr.Button("🌐 " + ("翻译" if lang == 'zh' else "Translate"), variant="primary")
                        text_output = gr.Textbox(
                            label="翻译结果" if lang == 'zh' else "Translation Result",
                            lines=15,
                            interactive=False
                        )
                        text_status = gr.Textbox(label="状态" if lang == 'zh' else "Status", interactive=False, lines=2)
                
                def do_text_translate(text, source, target):
                    logger.info(f"开始文本翻译: {source} -> {target}, 长度={len(text) if text else 0}")
                    if not text or not text.strip():
                        return "", "❌ 请输入文本 / Please enter text"
                    
                    result = translate_long_text(text.strip(), source, target)
                    if result["success"]:
                        chunks_info = f" ({result.get('chunks', 1)} 段)" if result.get("chunks", 1) > 1 else ""
                        logger.success(f"文本翻译完成: {source} -> {target}")
                        return result["translated"], f"✅ 翻译成功{chunks_info}"
                    else:
                        logger.error(f"文本翻译失败: {result.get('error')}")
                        return "", f"❌ {result.get('error', '翻译失败')}"
                
                text_translate_btn.click(
                    do_text_translate,
                    inputs=[text_input, source_lang, target_lang],
                    outputs=[text_output, text_status]
                )
            
            with gr.TabItem("📄 " + ("文本文件翻译" if lang == 'zh' else "Text File Translation")):
                with gr.Row():
                    with gr.Column(scale=1):
                        text_file_input = gr.File(
                            label="选择文本文件（txt/json/srt）" if lang == 'zh' else "Select Text Files (txt/json/srt)",
                            file_types=[".txt", ".json", ".srt"],
                            file_count="multiple"
                        )
                        text_file_translate_btn = gr.Button("🌐 " + ("翻译" if lang == 'zh' else "Translate"), variant="primary")
                        text_file_status = gr.Textbox(label="状态" if lang == 'zh' else "Status", interactive=False, lines=5)
                    
                    with gr.Column(scale=1):
                        text_file_output = gr.File(label="输出文件" if lang == 'zh' else "Output Files")
                
                def do_text_file_translate(files, source, target):
                    logger.info(f"开始文本文件翻译: {source} -> {target}, 文件数={len(files) if files else 0}")
                    if not files or len(files) == 0:
                        return "❌ 请选择文件 / Please select files", None
                    
                    all_outputs = []
                    status_parts = []
                    success_count = 0
                    
                    for f in files:
                        file_path = f.name if hasattr(f, 'name') else str(f)
                        result = translate_file(file_path, source, target)
                        
                        if result["success"]:
                            success_count += 1
                            if "output" in result:
                                all_outputs.append(result["output"])
                            status_parts.append(f"✅ {Path(file_path).name}")
                        else:
                            status_parts.append(f"❌ {Path(file_path).name}: {result.get('error')}")
                    
                    status_parts.append(f"\n✅ 成功: {success_count}/{len(files)}")
                    logger.success(f"文本文件翻译完成: 成功 {success_count}/{len(files)}")
                    return "\n".join(status_parts), all_outputs if all_outputs else None
                
                text_file_translate_btn.click(
                    do_text_file_translate,
                    inputs=[text_file_input, source_lang, target_lang],
                    outputs=[text_file_status, text_file_output]
                )
            
            with gr.TabItem("🎵 " + ("音频翻译" if lang == 'zh' else "Audio Translation")):
                with gr.Row():
                    with gr.Column(scale=1):
                        audio_file_input = gr.File(
                            label="选择音频文件" if lang == 'zh' else "Select Audio Files",
                            file_types=[".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
                            file_count="multiple"
                        )
                        audio_asr_model = gr.Dropdown(
                            choices=[(f"{v['name']} ({v.get('params', '')})", k) for k, v in ALL_ASR_MODELS.items()],
                            value="whisper-large-v3-turbo",
                            label="ASR 模型" if lang == 'zh' else "ASR Model"
                        )
                        audio_use_punc = gr.Checkbox(
                            value=True,
                            label="启用标点" if lang == 'zh' else "Enable Punctuation"
                        )
                        audio_file_translate_btn = gr.Button("🌐 " + ("翻译" if lang == 'zh' else "Translate"), variant="primary")
                        audio_file_status = gr.Textbox(label="状态" if lang == 'zh' else "Status", interactive=False, lines=5)
                    
                    with gr.Column(scale=1):
                        with gr.Accordion("输出选项" if lang == 'zh' else "Output Options", open=True):
                            audio_output_srt = gr.Checkbox(label="SRT 字幕", value=True)
                            audio_output_json = gr.Checkbox(label="JSON", value=True)
                            audio_output_txt = gr.Checkbox(label="TXT 文本", value=True)
                        audio_file_output = gr.File(label="输出文件" if lang == 'zh' else "Output Files")
                
                def do_audio_translate(files, source, target, asr_model_key, use_punc, out_srt, out_json, out_txt):
                    logger.info(f"开始音频翻译: {source} -> {target}, 文件数={len(files) if files else 0}, ASR={asr_model_key}, 标点={use_punc}")
                    if not files or len(files) == 0:
                        return "❌ 请选择文件 / Please select files", None
                    
                    output_formats = []
                    if out_srt:
                        output_formats.append("srt")
                    if out_json:
                        output_formats.append("json")
                    if out_txt:
                        output_formats.append("txt")
                    
                    all_outputs = []
                    status_parts = []
                    success_count = 0
                    
                    for f in files:
                        file_path = f.name if hasattr(f, 'name') else str(f)
                        result = translate_audio_video(file_path, source, target, output_formats, asr_model_key, use_punc)
                        
                        if result["success"]:
                            success_count += 1
                            if "output_files" in result:
                                all_outputs.extend(result["output_files"])
                            status_parts.append(f"✅ {Path(file_path).name}")
                        else:
                            status_parts.append(f"❌ {Path(file_path).name}: {result.get('error')}")
                    
                    status_parts.append(f"\n✅ 成功: {success_count}/{len(files)}")
                    logger.success(f"音频翻译完成: 成功 {success_count}/{len(files)}")
                    return "\n".join(status_parts), all_outputs if all_outputs else None
                
                audio_file_translate_btn.click(
                    do_audio_translate,
                    inputs=[audio_file_input, source_lang, target_lang, audio_asr_model, audio_use_punc, audio_output_srt, audio_output_json, audio_output_txt],
                    outputs=[audio_file_status, audio_file_output]
                )
            
            with gr.TabItem("🎬 " + ("视频翻译" if lang == 'zh' else "Video Translation")):
                with gr.Row():
                    with gr.Column(scale=1):
                        video_file_input = gr.File(
                            label="选择视频文件" if lang == 'zh' else "Select Video Files",
                            file_types=[".mp4", ".mkv", ".avi", ".mov", ".webm"],
                            file_count="multiple"
                        )
                        video_asr_model = gr.Dropdown(
                            choices=[(f"{v['name']} ({v.get('params', '')})", k) for k, v in ALL_ASR_MODELS.items()],
                            value="whisper-large-v3-turbo",
                            label="ASR 模型" if lang == 'zh' else "ASR Model"
                        )
                        video_use_punc = gr.Checkbox(
                            value=True,
                            label="启用标点" if lang == 'zh' else "Enable Punctuation"
                        )
                        video_file_translate_btn = gr.Button("🌐 " + ("翻译" if lang == 'zh' else "Translate"), variant="primary")
                        video_file_status = gr.Textbox(label="状态" if lang == 'zh' else "Status", interactive=False, lines=5)
                    
                    with gr.Column(scale=1):
                        with gr.Accordion("输出选项" if lang == 'zh' else "Output Options", open=True):
                            video_output_srt = gr.Checkbox(label="SRT 字幕", value=True)
                            video_output_json = gr.Checkbox(label="JSON", value=True)
                            video_output_txt = gr.Checkbox(label="TXT 文本", value=True)
                        video_file_output = gr.File(label="输出文件" if lang == 'zh' else "Output Files")
                
                def do_video_translate(files, source, target, asr_model_key, use_punc, out_srt, out_json, out_txt):
                    logger.info(f"开始视频翻译: {source} -> {target}, 文件数={len(files) if files else 0}, ASR={asr_model_key}, 标点={use_punc}")
                    if not files or len(files) == 0:
                        return "❌ 请选择文件 / Please select files", None
                    
                    output_formats = []
                    if out_srt:
                        output_formats.append("srt")
                    if out_json:
                        output_formats.append("json")
                    if out_txt:
                        output_formats.append("txt")
                    
                    all_outputs = []
                    status_parts = []
                    success_count = 0
                    
                    for f in files:
                        file_path = f.name if hasattr(f, 'name') else str(f)
                        result = translate_audio_video(file_path, source, target, output_formats, asr_model_key, use_punc)
                        
                        if result["success"]:
                            success_count += 1
                            if "output_files" in result:
                                all_outputs.extend(result["output_files"])
                            status_parts.append(f"✅ {Path(file_path).name}")
                        else:
                            status_parts.append(f"❌ {Path(file_path).name}: {result.get('error')}")
                    
                    status_parts.append(f"\n✅ 成功: {success_count}/{len(files)}")
                    logger.success(f"视频翻译完成: 成功 {success_count}/{len(files)}")
                    return "\n".join(status_parts), all_outputs if all_outputs else None
                
                video_file_translate_btn.click(
                    do_video_translate,
                    inputs=[video_file_input, source_lang, target_lang, video_asr_model, video_use_punc, video_output_srt, video_output_json, video_output_txt],
                    outputs=[video_file_status, video_file_output]
                )
        
        def swap_languages(source, target):
            if source != "auto" and target != "auto":
                return target, source
            return source, target
        
        swap_lang_btn.click(
            swap_languages,
            inputs=[source_lang, target_lang],
            outputs=[source_lang, target_lang]
        )
