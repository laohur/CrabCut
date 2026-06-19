import gradio as gr
from utils.separator import extract_audio, extract_video, separate_vocals
from utils.i18n import translate_text

def create_separator_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("音视频分离" if lang == 'zh' else "Audio/Video Separation"))
        
        with gr.Row():
            with gr.Column(scale=1):
                av_input = gr.File(
                    label="选择音视频文件" if lang == 'zh' else "Select Media File",
                    file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm", ".mp3", ".wav", ".flac", ".aac"]
                )
            
            with gr.Column(scale=1):
                with gr.Tab("提取音频" if lang == 'zh' else "Extract Audio"):
                    audio_format = gr.Dropdown(
                        choices=["aac", "mp3", "wav", "flac"],
                        value="aac",
                        label="音频格式" if lang == 'zh' else "Audio Format"
                    )
                    audio_bitrate = gr.Dropdown(
                        choices=["128k", "192k", "256k", "320k"],
                        value="192k",
                        label="比特率" if lang == 'zh' else "Bitrate"
                    )
                    extract_audio_btn = gr.Button("🎵 " + ("提取音频" if lang == 'zh' else "Extract Audio"), variant="primary")
                
                with gr.Tab("提取视频" if lang == 'zh' else "Extract Video"):
                    video_format = gr.Dropdown(
                        choices=["mp4", "avi", "mkv", "mov"],
                        value="mp4",
                        label="视频格式" if lang == 'zh' else "Video Format"
                    )
                    extract_video_btn = gr.Button("🎬 " + ("提取视频" if lang == 'zh' else "Extract Video"), variant="primary")
            
            with gr.Column(scale=1):
                av_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                av_audio_output = gr.Audio(label="音频输出" if lang == 'zh' else "Audio Output")
                av_video_output = gr.Video(label="视频输出" if lang == 'zh' else "Video Output")
        
        def do_extract_audio(file, fmt, bitrate):
            if not file:
                return "请选择文件 / Please select a file", None, None
            result = extract_audio(file.name, fmt, bitrate)
            if result["success"]:
                return f"✅ 提取成功\n📁 {result['output_path']}", result["output_path"], None
            return f"❌ {result['error']}", None, None
        
        def do_extract_video(file, fmt):
            if not file:
                return "请选择文件 / Please select a file", None, None
            result = extract_video(file.name, fmt)
            if result["success"]:
                return f"✅ 提取成功\n📁 {result['output_path']}", None, result["output_path"]
            return f"❌ {result['error']}", None, None
        
        extract_audio_btn.click(do_extract_audio, inputs=[av_input, audio_format, audio_bitrate], outputs=[av_status, av_audio_output, av_video_output])
        extract_video_btn.click(do_extract_video, inputs=[av_input, video_format], outputs=[av_status, av_audio_output, av_video_output])
        
        gr.Markdown("---")
        gr.Markdown("#### " + ("人声分离" if lang == 'zh' else "Vocal Separation"))
        
        with gr.Row():
            with gr.Column(scale=1):
                vocal_input = gr.File(
                    label="选择音频文件" if lang == 'zh' else "Select Audio File",
                    file_types=[".mp3", ".wav", ".flac", ".ogg", ".m4a"]
                )
            
            with gr.Column(scale=1):
                demucs_model = gr.Radio(
                    choices=[
                        ("htdemucs_ft" + (" (快速)" if lang == 'zh' else " (Fast)"), "htdemucs_ft.yaml"),
                        ("UVR-MDX-NET-Inst_HQ_3" + (" (MDX快速)" if lang == 'zh' else " (MDX Fast)"), "UVR-MDX-NET-Inst_HQ_3.onnx"),
                        ("UVR-MDX-NET-Inst_Main" + (" (MDX极速)" if lang == 'zh' else " (MDX Fastest)"), "UVR-MDX-NET-Inst_Main.onnx"),
                        ("UVR_MDXNET_KARA_2" + (" (卡拉OK)" if lang == 'zh' else " (Karaoke)"), "UVR_MDXNET_KARA_2.onnx"),
                        ("htdemucs" + (" (Demucs标准)" if lang == 'zh' else " (Demucs Standard)"), "htdemucs.yaml"),
                        ("htdemucs_6s" + (" (6轨分离)" if lang == 'zh' else " (6-stem)"), "htdemucs_6s.yaml"),
                    ],
                    value="htdemucs_ft.yaml",
                    label="分离模式" if lang == 'zh' else "Separation Mode"
                )
                separate_btn = gr.Button("🎤 " + ("分离人声" if lang == 'zh' else "Separate Vocals"), variant="primary")
            
            with gr.Column(scale=1):
                vocal_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                vocals_output = gr.Audio(label="人声" if lang == 'zh' else "Vocals")
                accompaniment_output = gr.Audio(label="伴奏" if lang == 'zh' else "Accompaniment")
        
        def do_separate_vocals(file, model):
            if not file:
                return "请选择音频文件 / Please select an audio file", None, None
            result = separate_vocals(file.name, model)
            if result["success"]:
                status = f"✅ 分离成功\n📁 {result['output_dir']}"
                return status, result.get("vocals_path"), result.get("accompaniment_path")
            return f"❌ {result['error']}", None, None
        
        separate_btn.click(do_separate_vocals, inputs=[vocal_input, demucs_model], outputs=[vocal_status, vocals_output, accompaniment_output])
