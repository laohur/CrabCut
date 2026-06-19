import gradio as gr
from utils.merger import concat_videos, concat_audios
from utils.i18n import translate_text
from datetime import datetime

def create_merger_page(lang="zh"):
    with gr.Column() as col:
        gr.Markdown("#### " + ("视频拼接" if lang == 'zh' else "Video Concat"))
        with gr.Row():
            with gr.Column(scale=1):
                vconcat_input = gr.File(label="选择视频文件(按顺序)" if lang == 'zh' else "Select Videos (in order)", file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm"], file_count="multiple")
                vconcat_name = gr.Textbox(label="输出文件名(可选)" if lang == 'zh' else "Output Name (optional)", value="")
            with gr.Column(scale=1):
                vconcat_format = gr.Dropdown(label="输出格式" if lang == 'zh' else "Output Format", choices=["mp4", "avi", "mkv", "mov", "webm"], value="mp4")
                vconcat_resize = gr.Radio(label="尺寸不一致时" if lang == 'zh' else "When sizes differ", choices=[("黑边补全", "pad"), ("中心截取", "crop"), ("保持原样", "none")], value="pad")
                vconcat_width = gr.Number(label="输出宽度(0=自动)" if lang == 'zh' else "Output Width (0=auto)", value=0)
                vconcat_height = gr.Number(label="输出高度(0=自动)" if lang == 'zh' else "Output Height (0=auto)", value=0)
                vconcat_fps = gr.Number(label="帧率(0=自动)" if lang == 'zh' else "FPS (0=auto)", value=0)
                vconcat_btn = gr.Button("🔗 " + ("拼接视频" if lang == 'zh' else "Concat Videos"), variant="primary")
            with gr.Column(scale=1):
                vconcat_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=5)
                vconcat_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def update_vconcat_name(files):
            if not files:
                return "", "", 0, 0, 0
            from pathlib import Path
            from utils.metadata import get_media_metadata
            first_chars = ""
            for f in files:
                if hasattr(f, 'name'):
                    path = f.name
                elif isinstance(f, dict):
                    path = f.get("name", "")
                else:
                    path = f
                if path:
                    stem = Path(path).stem
                    if stem:
                        first_chars += stem[0]
            file_count = len(files)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"{first_chars}-concat{file_count}-{timestamp}"
            
            first_file = files[0]
            if hasattr(first_file, 'name'):
                first_path = first_file.name
            else:
                first_path = first_file
            result = get_media_metadata(first_path)
            width = 0
            height = 0
            fps = 0
            if result["success"]:
                video_info = result.get("video", {})
                width = video_info.get("width", 0)
                height = video_info.get("height", 0)
                fps = video_info.get("fps", 0)
            
            return default_name, "", width, height, fps
        
        def do_vconcat(files, name, fmt, resize, w, h, fps):
            if not files:
                return "请选择视频文件 / Please select video files", None
            result = concat_videos(files, name if name.strip() else None, fmt, resize, int(w), int(h), int(fps))
            cmd_str = " ".join(result.get("cmd", []))
            if result["success"]:
                return f"✅ 拼接成功\n📁 {result['output_path']}\n\n💻 CMD:\n{cmd_str}", result["output_path"]
            return f"❌ {result['error']}\n\n💻 CMD:\n{cmd_str}", None
        
        vconcat_input.change(update_vconcat_name, inputs=[vconcat_input], outputs=[vconcat_name, vconcat_status, vconcat_width, vconcat_height, vconcat_fps])
        vconcat_btn.click(do_vconcat, inputs=[vconcat_input, vconcat_name, vconcat_format, vconcat_resize, vconcat_width, vconcat_height, vconcat_fps], outputs=[vconcat_status, vconcat_output])
        
        gr.Markdown("---")
        gr.Markdown("#### " + ("音频拼接" if lang == 'zh' else "Audio Concat"))
        with gr.Row():
            with gr.Column(scale=1):
                aconcat_input = gr.File(label="选择音频文件(按顺序)" if lang == 'zh' else "Select Audios (in order)", file_types=[".mp3", ".wav", ".aac", ".flac", ".ogg"], file_count="multiple")
                aconcat_name = gr.Textbox(label="输出文件名(可选)" if lang == 'zh' else "Output Name (optional)", value="")
            with gr.Column(scale=1):
                aconcat_format = gr.Dropdown(label="输出格式" if lang == 'zh' else "Output Format", choices=["aac", "mp3", "wav", "flac", "ogg"], value="aac")
                aconcat_bitrate = gr.Number(label="码率(kbps, 0=自动)" if lang == 'zh' else "Bitrate (kbps, 0=auto)", value=0)
                aconcat_channels = gr.Dropdown(label="声道数" if lang == 'zh' else "Channels", choices=[("自动", 0), ("单声道", 1), ("立体声", 2)], value=0)
                aconcat_btn = gr.Button("🔗 " + ("拼接音频" if lang == 'zh' else "Concat Audios"), variant="primary")
            with gr.Column(scale=1):
                aconcat_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=5)
                aconcat_output = gr.Audio(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def update_aconcat_name(files):
            if not files:
                return "", "", 0, 0
            from pathlib import Path
            from utils.metadata import get_media_metadata
            first_chars = ""
            for f in files:
                if hasattr(f, 'name'):
                    path = f.name
                elif isinstance(f, dict):
                    path = f.get("name", "")
                else:
                    path = f
                if path:
                    stem = Path(path).stem
                    if stem:
                        first_chars += stem[0]
            file_count = len(files)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"{first_chars}-concat{file_count}-{timestamp}"
            
            first_file = files[0]
            if hasattr(first_file, 'name'):
                first_path = first_file.name
            else:
                first_path = first_file
            result = get_media_metadata(first_path)
            bitrate = 0
            channels = 0
            if result["success"]:
                audio_info = result.get("audio", {})
                bitrate = audio_info.get("bitrate", 0) // 1000 if audio_info.get("bitrate") else 0
                channels = audio_info.get("channels", 0)
            
            return default_name, "", bitrate, channels
        
        def do_aconcat(files, name, fmt, bitrate, channels):
            if not files:
                return "请选择音频文件 / Please select audio files", None
            result = concat_audios(files, name if name.strip() else None, fmt, int(bitrate), int(channels))
            cmd_str = " ".join(result.get("cmd", []))
            if result["success"]:
                return f"✅ 拼接成功\n📁 {result['output_path']}\n\n💻 CMD:\n{cmd_str}", result["output_path"]
            return f"❌ {result['error']}\n\n💻 CMD:\n{cmd_str}", None
        
        aconcat_input.change(update_aconcat_name, inputs=[aconcat_input], outputs=[aconcat_name, aconcat_status, aconcat_bitrate, aconcat_channels])
        aconcat_btn.click(do_aconcat, inputs=[aconcat_input, aconcat_name, aconcat_format, aconcat_bitrate, aconcat_channels], outputs=[aconcat_status, aconcat_output])
    
    return col
