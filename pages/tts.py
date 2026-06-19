import gradio as gr
from pathlib import Path
from utils.tts import (
    get_output_dir,
    get_lang_groups,
    get_lang_name,
    get_all_voices_for_lang,
    tts_text_with_filename,
    tts_from_file,
    tts_batch_files,
    generate_output_filename,
    get_tts_preview,
)
from utils.i18n import translate_text
from utils.translate import translate_text

_LANG_GROUPS_CACHE = None

def _get_lang_groups_cached():
    global _LANG_GROUPS_CACHE
    if _LANG_GROUPS_CACHE is None:
        _LANG_GROUPS_CACHE = get_lang_groups()
    return _LANG_GROUPS_CACHE

def parse_srt(srt_content: str):
    blocks = []
    current_block = []
    for line in srt_content.strip().split('\n'):
        if line.strip() == '':
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)
    return blocks

def translate_srt(srt_content: str, target_lang: str) -> str:
    blocks = parse_srt(srt_content)
    translated_blocks = []
    
    for block in blocks:
        if len(block) >= 3:
            index = block[0]
            timestamp = block[1]
            text_lines = block[2:]
            
            text = '\n'.join(text_lines)
            trans_result = translate_text(text, source="auto", target=target_lang)
            
            if trans_result.get("success"):
                translated_text = trans_result["translated"]
            else:
                translated_text = text
            
            translated_blocks.append(f"{index}\n{timestamp}\n{translated_text}")
        else:
            translated_blocks.append('\n'.join(block))
    
    return '\n\n'.join(translated_blocks)

def create_tts_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("文本转语音 (TTS)" if lang == 'zh' else "Text-to-Speech (TTS)"))
        
        with gr.Row():
            with gr.Column(scale=1):
                tts_text = gr.Textbox(
                    label="输入文本" if lang == 'zh' else "Input Text",
                    lines=6,
                    placeholder="在此输入要转换的文本..." if lang == 'zh' else "Enter text to convert..."
                )
                
                tts_files = gr.File(
                    label="选择文件（txt/json/srt）" if lang == 'zh' else "Select Files (txt/json/srt)",
                    file_types=[".txt", ".json", ".srt"],
                    file_count="multiple"
                )
                
                gr.Markdown("---")
                gr.Markdown("**" + ("语音设置" if lang == 'zh' else "Voice Settings") + "**")
                
                lang_groups = _get_lang_groups_cached()
                default_lang = "zh" if lang == "zh" else "en"
                if default_lang not in lang_groups:
                    default_lang = lang_groups[0] if lang_groups else "zh"
                
                tts_lang = gr.Dropdown(
                    choices=[(get_lang_name(lg, lang), lg) for lg in lang_groups],
                    value=default_lang,
                    label="语言" if lang == 'zh' else "Language",
                    filterable=True
                )
                
                default_voices = get_all_voices_for_lang(default_lang)
                tts_voice = gr.Dropdown(
                    choices=[(f"{v['locale']} - {v['name']} ({v['gender']})", v["voice"]) for v in default_voices],
                    value=default_voices[0]["voice"] if default_voices else None,
                    label="音色" if lang == 'zh' else "Voice",
                    filterable=True
                )
                
                with gr.Row():
                    tts_rate = gr.Slider(
                        minimum=-50,
                        maximum=50,
                        value=0,
                        step=10,
                        label="语速 (%)" if lang == 'zh' else "Rate (%)"
                    )
                    tts_volume = gr.Slider(
                        minimum=-50,
                        maximum=50,
                        value=0,
                        step=10,
                        label="音量 (%)" if lang == 'zh' else "Volume (%)"
                    )
                
                tts_pitch = gr.Slider(
                    minimum=-50,
                    maximum=50,
                    value=0,
                    step=10,
                    label="音调 (Hz)" if lang == 'zh' else "Pitch (Hz)"
                )
            
            with gr.Column(scale=1):
                tts_preview = gr.HTML(
                    value="<span style='color: gray;'>输入文本或选择文件后显示预览信息</span>",
                    label="预览" if lang == 'zh' else "Preview"
                )
                gr.Markdown("---")
                gr.Markdown("**" + ("翻译设置" if lang == 'zh' else "Translation Settings") + "**")
                
                with gr.Row():
                    tts_enable_translate = gr.Checkbox(
                        label="翻译后再生成语音" if lang == 'zh' else "Translate before TTS",
                        value=False
                    )
                    tts_target_lang = gr.Dropdown(
                        choices=[
                            ("英语 / English", "en"),
                            ("中文", "zh"),
                            ("日语 / Japanese", "ja"),
                            ("韩语 / Korean", "ko"),
                            ("法语 / French", "fr"),
                            ("德语 / German", "de"),
                            ("西班牙语 / Spanish", "es"),
                            ("俄语 / Russian", "ru"),
                        ],
                        value="en",
                        label="目标语言" if lang == 'zh' else "Target Language"
                    )
                
                gr.Markdown("---")
                gr.Markdown("**" + ("导出选项" if lang == 'zh' else "Export Options") + "**")
                
                with gr.Row():
                    tts_export_srt = gr.Checkbox(
                        label="SRT 字幕" if lang == 'zh' else "SRT Subtitle",
                        value=False
                    )
                    tts_export_json = gr.Checkbox(
                        label="JSON" if lang == 'zh' else "JSON",
                        value=False
                    )
                
                tts_btn = gr.Button("🔊 " + ("生成语音" if lang == 'zh' else "Generate Speech"), variant="primary")
                tts_status = gr.Textbox(label="状态" if lang == 'zh' else "Status", interactive=False, lines=5)
                
                tts_audio = gr.Audio(
                    label="生成的音频" if lang == 'zh' else "Generated Audio",
                    type="filepath"
                )
                
                tts_output_files = gr.File(label="输出文件" if lang == 'zh' else "Output Files")
        
        def update_voices(lang_val):
            voices = get_all_voices_for_lang(lang_val)
            choices = [(f"{v['locale']} - {v['name']} ({v['gender']})", v["voice"]) for v in voices]
            default = voices[0]["voice"] if voices else None
            return gr.Dropdown(choices=choices, value=default)
        
        tts_lang.change(
            update_voices,
            inputs=[tts_lang],
            outputs=[tts_voice]
        )
        
        def update_preview(text, files):
            total_bytes = 0
            file_info = ""
            
            if text and text.strip():
                total_bytes += len(text.strip().encode('utf-8'))
            
            if files:
                if isinstance(files, list):
                    file_count = len(files)
                    file_names = []
                    for f in files:
                        try:
                            with open(f.name, "r", encoding="utf-8") as file:
                                content = file.read().strip()
                                total_bytes += len(content.encode('utf-8'))
                                file_names.append(Path(f.name).name)
                        except:
                            pass
                    if file_names:
                        file_info = f"<p><b>文件 / Files:</b> {file_count} 个</p>"
                else:
                    try:
                        with open(files.name, "r", encoding="utf-8") as file:
                            content = file.read().strip()
                            total_bytes += len(content.encode('utf-8'))
                            file_info = f"<p><b>文件 / File:</b> {Path(files.name).name}</p>"
                    except:
                        pass
            
            if total_bytes == 0:
                return "<span style='color: gray;'>输入文本或选择文件后显示预览信息</span>"
            
            preview = get_tts_preview(byte_count=total_bytes)
            html = f"""
            <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                {file_info}
                <p><b>总字节数 / Total Bytes:</b> {total_bytes:,}</p>
                <p><b>预估音频时长 / Audio Duration:</b> {preview['audio_duration_str']}</p>
                <p><b>预估生成耗时 / Estimated Time:</b> {preview['estimated_time_str']}</p>
            </div>
            """
            return html
        
        tts_text.change(
            update_preview,
            inputs=[tts_text, tts_files],
            outputs=[tts_preview]
        )
        
        tts_files.change(
            update_preview,
            inputs=[tts_text, tts_files],
            outputs=[tts_preview]
        )
        
        def do_tts(text, files, voice, rate, volume, pitch, export_srt, export_json, enable_translate, target_lang):
            from utils.log_config import logger
            logger.info(f"开始 TTS / Start TTS: voice={voice}, rate={rate}, volume={volume}, pitch={pitch}, translate={enable_translate}, target={target_lang}")
            
            rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
            volume_str = f"+{volume}%" if volume >= 0 else f"{volume}%"
            pitch_str = f"+{pitch}Hz" if pitch >= 0 else f"{pitch}Hz"
            
            output_dir = get_output_dir()
            
            has_text = text and text.strip()
            has_files = files and len(files) > 0
            
            if not has_text and not has_files:
                return "❌ 请输入文本或选择文件 / Please enter text or select files", None, None
            
            export_formats = []
            if export_srt:
                export_formats.append("srt")
            if export_json:
                export_formats.append("json")
            
            if has_text and not has_files:
                original_text = text.strip()
                
                if enable_translate:
                    logger.info(f"翻译文本: {original_text[:50]}... -> {target_lang}")
                    trans_result = translate_text(original_text, source="auto", target=target_lang)
                    if trans_result.get("success"):
                        original_text = trans_result["translated"]
                        logger.info(f"翻译完成: {trans_result['original'][:30]}... -> {original_text[:30]}...")
                    else:
                        return f"❌ 翻译失败: {trans_result.get('error', 'Unknown error')}", None, None
                
                preview = get_tts_preview(original_text)
                logger.info(f"预览: {preview['bytes']}字节, 音频{preview['audio_duration_str']}, 耗时{preview['estimated_time_str']}")
                
                result = tts_text_with_filename(original_text, voice, rate_str, volume_str, pitch_str, export_formats=export_formats)
                
                if result["success"]:
                    output_path = result["output"]
                    chunks_info = f" ({result.get('chunks', 1)} 段 / chunks)" if result.get("chunks", 1) > 1 else ""
                    skipped_info = " (已跳过 / skipped)" if result.get("skipped") else ""
                    chunk_dir_info = f"\n📁 子文件目录: {Path(result['chunk_dir']).name}" if result.get("chunk_dir") else ""
                    
                    export_info = ""
                    if export_formats:
                        export_names = [f"{Path(output_path).stem}.{fmt}" for fmt in export_formats]
                        export_info = f"\n📄 导出: {', '.join(export_names)}"
                    
                    status_msg = f"✅ 生成成功 / Success{chunks_info}{skipped_info}\n📁 {Path(output_path).name}{chunk_dir_info}{export_info}"
                    
                    all_outputs = [output_path]
                    output_dir_path = Path(output_path).parent
                    output_stem = Path(output_path).stem
                    for fmt in export_formats:
                        export_file = output_dir_path / f"{output_stem}.{fmt}"
                        if export_file.exists():
                            all_outputs.append(str(export_file))
                    
                    logger.success(f"TTS 完成: {Path(output_path).name}")
                    return status_msg, output_path, all_outputs
                else:
                    logger.error(f"TTS 失败: {result['error']}")
                    return f"❌ {result['error']}", None, None
            
            if has_files:
                if len(files) == 1:
                    file = files[0]
                    
                    with open(file.name, "r", encoding="utf-8") as f:
                        file_content = f.read().strip()
                    
                    if enable_translate:
                        file_ext = Path(file.name).suffix.lower()
                        logger.info(f"翻译文件内容: {file_ext} -> {target_lang}")
                        
                        if file_ext == '.srt':
                            file_content = translate_srt(file_content, target_lang)
                            logger.info(f"SRT 翻译完成")
                        else:
                            trans_result = translate_text(file_content, source="auto", target=target_lang)
                            if trans_result.get("success"):
                                file_content = trans_result["translated"]
                                logger.info(f"翻译完成")
                            else:
                                return f"❌ 翻译失败: {trans_result.get('error', 'Unknown error')}", None, None
                    
                    output_filename = generate_output_filename("", source_file=file.name)
                    if enable_translate:
                        output_filename = output_filename.replace(".wav", f"_{target_lang}.wav")
                    output_path = output_dir / output_filename
                    
                    result = tts_text_with_filename(file_content, voice, rate_str, volume_str, pitch_str, output_path=str(output_path), export_formats=export_formats)
                    
                    if result["success"]:
                        skipped_info = " (已跳过 / skipped)" if result.get("skipped") else ""
                        chunk_dir_info = f"\n📁 子文件目录: {Path(result['chunk_dir']).name}" if result.get("chunk_dir") else ""
                        
                        export_info = ""
                        if export_formats:
                            export_names = [f"{Path(output_path).stem}.{fmt}" for fmt in export_formats]
                            export_info = f"\n📄 导出: {', '.join(export_names)}"
                        
                        status_msg = f"✅ 生成成功 / Success{skipped_info}: {Path(file.name).name}\n📁 {output_filename}{chunk_dir_info}{export_info}"
                        
                        all_outputs = [str(output_path)]
                        output_stem = Path(output_path).stem
                        for fmt in export_formats:
                            export_file = output_dir / f"{output_stem}.{fmt}"
                            if export_file.exists():
                                all_outputs.append(str(export_file))
                        
                        logger.success(f"TTS 完成: {output_filename}")
                        return status_msg, str(output_path), all_outputs
                    else:
                        logger.error(f"TTS 失败: {result['error']}")
                        return f"❌ {result['error']}", None, None
                
                result = tts_batch_files([f.name for f in files], voice, rate_str, volume_str, pitch_str, export_formats=export_formats)
                
                status_lines = [
                    f"✅ 批量生成完成 / Batch done: {result['success_count']}/{result['total_count']} 成功"
                ]
                if result.get("skipped_count", 0) > 0:
                    status_lines.append(f"   (跳过 {result['skipped_count']} 个已存在文件)")
                
                output_files = []
                for r in result["results"]:
                    if r["success"]:
                        status_lines.append(f"  ✅ {Path(r['input']).name}")
                        output_files.append(r["output"])
                    else:
                        status_lines.append(f"  ❌ {Path(r['input']).name}: {r.get('error', 'Unknown error')}")
                
                logger.success(f"批量 TTS 完成: {result['success_count']}/{result['total_count']} 成功")
                return "\n".join(status_lines), output_files[0] if output_files else None, output_files if output_files else None
            
            logger.error("TTS 未知错误")
            return "❌ 未知错误 / Unknown error", None, None
        
        tts_btn.click(
            do_tts,
            inputs=[tts_text, tts_files, tts_voice, tts_rate, tts_volume, tts_pitch, tts_export_srt, tts_export_json, tts_enable_translate, tts_target_lang],
            outputs=[tts_status, tts_audio, tts_output_files]
        )
