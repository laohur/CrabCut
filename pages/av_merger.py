import gradio as gr
from utils.av_merger import merge_audio_video, replace_audio as replace_audio_track, add_background_music
from utils.i18n import translate_text

def create_av_merger_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("音视频合并" if lang == 'zh' else "Audio/Video Merge"))
        
        with gr.Tabs():
            with gr.TabItem("添加背景音乐" if lang == 'zh' else "Add BGM"):
                with gr.Row():
                    with gr.Column(scale=1):
                        bgm_video = gr.File(
                            label="选择视频" if lang == 'zh' else "Select Video",
                            file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm"]
                        )
                        bgm_audio = gr.File(
                            label="选择背景音乐" if lang == 'zh' else "Select BGM",
                            file_types=[".mp3", ".wav", ".flac", ".aac", ".ogg"]
                        )
                    
                    with gr.Column(scale=1):
                        bgm_volume = gr.Slider(
                            minimum=0.0, maximum=1.0, value=0.3, step=0.1,
                            label="背景音乐音量" if lang == 'zh' else "BGM Volume"
                        )
                        bgm_loop = gr.Checkbox(
                            value=True,
                            label="循环背景音乐" if lang == 'zh' else "Loop BGM"
                        )
                        bgm_format = gr.Dropdown(
                            choices=["mp4", "mkv", "mov"],
                            value="mp4",
                            label="输出格式" if lang == 'zh' else "Output Format"
                        )
                        bgm_btn = gr.Button("🎵 " + ("添加背景音乐" if lang == 'zh' else "Add BGM"), variant="primary")
                    
                    with gr.Column(scale=1):
                        bgm_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                        bgm_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
            
            with gr.TabItem("替换音频" if lang == 'zh' else "Replace Audio"):
                with gr.Row():
                    with gr.Column(scale=1):
                        replace_video = gr.File(
                            label="选择视频" if lang == 'zh' else "Select Video",
                            file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm"]
                        )
                        replace_audio = gr.File(
                            label="选择新音频" if lang == 'zh' else "Select New Audio",
                            file_types=[".mp3", ".wav", ".flac", ".aac", ".ogg"]
                        )
                    
                    with gr.Column(scale=1):
                        replace_format = gr.Dropdown(
                            choices=["mp4", "mkv", "mov"],
                            value="mp4",
                            label="输出格式" if lang == 'zh' else "Output Format"
                        )
                        replace_btn = gr.Button("🔄 " + ("替换音频" if lang == 'zh' else "Replace Audio"), variant="primary")
                    
                    with gr.Column(scale=1):
                        replace_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                        replace_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
            
            with gr.TabItem("混合音轨" if lang == 'zh' else "Mix Audio"):
                with gr.Row():
                    with gr.Column(scale=1):
                        mix_video = gr.File(
                            label="选择视频" if lang == 'zh' else "Select Video",
                            file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm"]
                        )
                        mix_audio = gr.File(
                            label="选择额外音频" if lang == 'zh' else "Select Additional Audio",
                            file_types=[".mp3", ".wav", ".flac", ".aac", ".ogg"]
                        )
                    
                    with gr.Column(scale=1):
                        mix_audio_volume = gr.Slider(
                            minimum=0.0, maximum=2.0, value=1.0, step=0.1,
                            label="额外音频音量" if lang == 'zh' else "Additional Audio Volume"
                        )
                        mix_video_volume = gr.Slider(
                            minimum=0.0, maximum=1.0, value=0.5, step=0.1,
                            label="原视频音量" if lang == 'zh' else "Original Video Volume"
                        )
                        mix_format = gr.Dropdown(
                            choices=["mp4", "mkv", "mov"],
                            value="mp4",
                            label="输出格式" if lang == 'zh' else "Output Format"
                        )
                        mix_btn = gr.Button("🔀 " + ("混合音轨" if lang == 'zh' else "Mix Audio"), variant="primary")
                    
                    with gr.Column(scale=1):
                        mix_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                        mix_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def do_add_bgm(video, audio, volume, loop, fmt):
            if not video or not audio:
                return "请选择视频和音频文件 / Please select video and audio files", None
            result = add_background_music(video.name, audio.name, fmt, volume, loop)
            if result["success"]:
                return f"✅ 添加成功\n📁 {result['output_path']}", result["output_path"]
            return f"❌ {result['error']}", None
        
        def do_replace_audio(video, audio, fmt):
            if not video or not audio:
                return "请选择视频和音频文件 / Please select video and audio files", None
            result = replace_audio_track(video.name, audio.name, fmt)
            if result["success"]:
                return f"✅ 替换成功\n📁 {result['output_path']}", result["output_path"]
            return f"❌ {result['error']}", None
        
        def do_mix_audio(video, audio, audio_vol, video_vol, fmt):
            if not video or not audio:
                return "请选择视频和音频文件 / Please select video and audio files", None
            result = merge_audio_video(video.name, audio.name, fmt, audio_vol, video_vol)
            if result["success"]:
                return f"✅ 混合成功\n📁 {result['output_path']}", result["output_path"]
            return f"❌ {result['error']}", None
        
        bgm_btn.click(do_add_bgm, inputs=[bgm_video, bgm_audio, bgm_volume, bgm_loop, bgm_format], outputs=[bgm_status, bgm_output])
        replace_btn.click(do_replace_audio, inputs=[replace_video, replace_audio, replace_format], outputs=[replace_status, replace_output])
        mix_btn.click(do_mix_audio, inputs=[mix_video, mix_audio, mix_audio_volume, mix_video_volume, mix_format], outputs=[mix_status, mix_output])
