import gradio as gr
from pathlib import Path
from utils.auto_cut import auto_cut_speaking, generate_subtitle_files
from utils.asr import ALL_ASR_MODELS
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

VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

def create_auto_edit_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("口播自动剪切" if lang == 'zh' else "Auto Cut Speaking Segments"))

        with gr.Row():
            with gr.Column(scale=1):
                with gr.Tabs():
                    with gr.Tab("视频 / Video"):
                        video_input = gr.Video(
                            label="输入视频" if lang == 'zh' else "Input Video",
                        )
                        output_video = gr.Video(
                            label="输出视频" if lang == 'zh' else "Output Video",
                        )
                    with gr.Tab("音频 / Audio"):
                        audio_input = gr.Audio(
                            label="输入音频" if lang == 'zh' else "Input Audio",
                            type="filepath",
                        )
                        output_audio = gr.Audio(
                            label="输出音频" if lang == 'zh' else "Output Audio",
                            type="filepath",
                        )

            with gr.Column(scale=1):
                asr_model = gr.Dropdown(
                    choices=[(f"{v['name']} ({v.get('params', '')})", k) for k, v in ALL_ASR_MODELS.items()],
                    value="whisper-large-v3-turbo",
                    label="ASR 模型" if lang == 'zh' else "ASR Model"
                )

                asr_lang = gr.Dropdown(
                    choices=ASR_LANGUAGES,
                    value="auto",
                    label="识别语言" if lang == 'zh' else "Language"
                )

                use_punc = gr.Checkbox(
                    value=True,
                    label="启用标点" if lang == 'zh' else "Enable Punctuation",
                )

                padding = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.1,
                    step=0.05,
                    label="前后过渡时长（秒）" if lang == 'zh' else "Padding (seconds)",
                )

                merge_gap = gr.Slider(
                    minimum=0.1,
                    maximum=5.0,
                    value=1.0,
                    step=0.1,
                    label="合并间隔阈值（秒）" if lang == 'zh' else "Merge Gap (seconds)",
                )

                output_formats = gr.CheckboxGroup(
                    choices=["SRT", "JSON", "TXT"],
                    value=["SRT", "JSON", "TXT"],
                    label="输出字幕格式" if lang == 'zh' else "Output Subtitle Formats",
                )

                cut_btn = gr.Button("✂️ " + ("自动剪切" if lang == 'zh' else "Auto Cut"), variant="primary")

                status = gr.Textbox(label="状态" if lang == 'zh' else "Status", interactive=False, lines=3)

                output_files = gr.File(
                    label="输出字幕文件" if lang == 'zh' else "Output Subtitle Files",
                    file_count="multiple",
                )

        def do_auto_cut(video_file, audio_file, model_key, language, enable_punc, pad, gap, formats):
            file_path = video_file if video_file else audio_file
            if not file_path:
                return None, None, "❌ 请选择文件 / Please select a file", []

            logger.info(f"开始口播自动剪切: file={file_path}, ASR={model_key}, padding={pad}s, merge_gap={gap}s")

            result = auto_cut_speaking(
                file_path=file_path,
                asr_model=model_key,
                use_punc=enable_punc,
                padding=pad,
                merge_gap=gap,
                language=language,
            )

            if not result["success"]:
                logger.error(f"口播自动剪切失败: {result['error']}")
                return None, None, f"❌ {result['error']}", []

            cut_ranges = result.get("cut_ranges", [])
            segments = result.get("segments", [])
            cache_mark = " (已有 / cached)" if result.get("from_cache") else ""

            original_dur = result.get("original_duration", 0)
            output_dur = result.get("output_duration", 0)

            if result.get("no_cut_needed"):
                status_msg = f"ℹ️ 口播覆盖 {output_dur/original_dur*100:.0f}%，无需剪切\n⏱️ {original_dur:.1f}s（无静音段）\n📊 {len(segments)} 个口播片段"
            else:
                status_msg = f"✅ 剪切成功{cache_mark}\n📁 {Path(result['output']).name}\n⏱️ {original_dur:.1f}s → {output_dur:.1f}s\n📊 {len(segments)} 个口播片段, 合并为 {len(cut_ranges)} 段"

            output = result["output"]
            is_video_output = Path(output).suffix.lower() in VIDEO_EXTS
            out_video = output if is_video_output else None
            out_audio = output if not is_video_output else None

            fmt_list = [f.lower() for f in formats] if formats else []
            sub_files = []
            if fmt_list:
                sub_result = generate_subtitle_files(file_path, segments, fmt_list)
                if sub_result["success"]:
                    sub_files = sub_result["output_files"]

            logger.success(f"口播自动剪切完成: {Path(result['output']).name}")
            return out_video, out_audio, status_msg, sub_files

        cut_btn.click(
            do_auto_cut,
            inputs=[video_input, audio_input, asr_model, asr_lang, use_punc, padding, merge_gap, output_formats],
            outputs=[output_video, output_audio, status, output_files]
        )
