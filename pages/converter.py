import gradio as gr
from utils.converter import convert_media, images_to_video, video_to_images, VIDEO_FORMATS, AUDIO_FORMATS
from utils.i18n import translate_text

def create_converter_page(lang="zh"):
    with gr.Column() as col:
        gr.Markdown("#### " + ("音视频转换" if lang == 'zh' else "Media Convert"))
        with gr.Row():
            with gr.Column(scale=1):
                file_input = gr.File(label=translate_text('common.select_file', lang) if lang == 'zh' else "Select a file")
            with gr.Column(scale=1):
                output_format = gr.Dropdown(
                    choices=list(VIDEO_FORMATS.keys()) + list(AUDIO_FORMATS.keys()),
                    value="mp4",
                    label="输出格式" if lang == 'zh' else "Output Format"
                )
                quality = gr.Radio(
                    choices=[
                        ("高质量" if lang == 'zh' else "High", "high"),
                        ("中等" if lang == 'zh' else "Medium", "medium"),
                        ("低质量" if lang == 'zh' else "Low", "low"),
                    ],
                    value="medium",
                    label="质量" if lang == 'zh' else "Quality"
                )
                video_fps = gr.Number(label="帧率(0=自动)" if lang == 'zh' else "FPS (0=auto)", value=0, visible=True)
                speed = gr.Slider(minimum=0.1, maximum=10.0, value=1.0, step=0.1, label="播放速度" if lang == 'zh' else "Speed")
                volume = gr.Slider(minimum=0.0, maximum=3.0, value=1.0, step=0.1, label="音量" if lang == 'zh' else "Volume")
                audio_bitrate = gr.Number(label="音频码率kbps(0=自动)" if lang == 'zh' else "Audio Bitrate kbps (0=auto)", value=0, visible=True)
                audio_channels = gr.Dropdown(
                    label="声道数" if lang == 'zh' else "Channels",
                    choices=[("自动", 0), ("单声道", 1), ("立体声", 2)],
                    value=0,
                    visible=True
                )
                convert_btn = gr.Button("🔄 " + ("开始转换" if lang == 'zh' else "Convert"), variant="primary")
            with gr.Column(scale=1):
                status_output = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=5)
                video_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
                audio_output = gr.Audio(label=translate_text('common.output', lang) if lang == 'zh' else "Output", visible=False)
        
        def update_format_params(fmt):
            is_video = fmt in VIDEO_FORMATS
            return gr.update(visible=is_video), gr.update(visible=True), gr.update(visible=True)
        
        output_format.change(update_format_params, inputs=[output_format], outputs=[video_fps, audio_bitrate, audio_channels])
        
        def do_convert(file, fmt, q, fps, spd, vol, bitrate, channels):
            if not file:
                return "请选择文件 / Please select a file", None, gr.update(visible=False)
            
            result = convert_media(file.name, fmt, q, int(fps) if fps else 0, int(bitrate) if bitrate else 0, int(channels), spd, vol)
            cmd_str = " ".join(result.get("cmd", []))
            
            if result["success"]:
                is_audio = fmt in AUDIO_FORMATS
                return (
                    f"✅ 转换成功\n📁 {result['output_path']}\n\n💻 CMD:\n{cmd_str}",
                    result["output_path"] if not is_audio else None,
                    gr.update(value=result["output_path"], visible=is_audio)
                )
            else:
                return f"❌ {result['error']}\n\n💻 CMD:\n{cmd_str}", None, gr.update(visible=False)
        
        convert_btn.click(do_convert, inputs=[file_input, output_format, quality, video_fps, speed, volume, audio_bitrate, audio_channels], outputs=[status_output, video_output, audio_output])
        
        gr.Markdown("---")
        gr.Markdown("#### " + ("图片转视频" if lang == 'zh' else "Images to Video"))
        with gr.Row():
            with gr.Column(scale=1):
                images_input = gr.File(
                    label="选择图片（可多选）" if lang == 'zh' else "Select Images (multiple)",
                    file_count="multiple",
                    file_types=["image"]
                )
            with gr.Column(scale=1):
                img_fps = gr.Slider(minimum=1, maximum=30, value=24, step=1, label="帧率 (FPS)" if lang == 'zh' else "FPS")
                img_duration = gr.Slider(minimum=1, maximum=10, value=2, step=1, label="每张图片时长(秒)" if lang == 'zh' else "Duration per image (s)")
                img_width = gr.Number(label="宽度" if lang == 'zh' else "Width", value=1280)
                img_height = gr.Number(label="高度" if lang == 'zh' else "Height", value=720)
                img_resize_mode = gr.Radio(
                    choices=[
                        ("黑边补全" if lang == 'zh' else "Pad", "pad"),
                        ("中心裁剪" if lang == 'zh' else "Crop", "crop"),
                    ],
                    value="pad",
                    label="尺寸不一致处理" if lang == 'zh' else "Resize Mode"
                )
                img_output_format = gr.Dropdown(
                    choices=list(VIDEO_FORMATS.keys()),
                    value="mp4",
                    label="输出格式" if lang == 'zh' else "Output Format"
                )
                img_convert_btn = gr.Button("🔄 " + ("生成视频" if lang == 'zh' else "Create Video"), variant="primary")
            with gr.Column(scale=1):
                img_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=5)
                img_video_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def do_images_to_video(files, fps, duration, width, height, resize_mode, fmt):
            if not files:
                return "请选择图片 / Please select images", None
            
            image_paths = [f.name for f in files]
            result = images_to_video(image_paths, fmt, fps, duration, int(width), int(height), resize_mode)
            cmd_str = " ".join(result.get("cmd", []))
            
            if result["success"]:
                return f"✅ 生成成功 ({result['image_count']}张图片)\n📁 {result['output_path']}\n\n💻 CMD:\n{cmd_str}", result["output_path"]
            else:
                return f"❌ {result['error']}\n\n💻 CMD:\n{cmd_str}", None
        
        img_convert_btn.click(do_images_to_video, inputs=[images_input, img_fps, img_duration, img_width, img_height, img_resize_mode, img_output_format], outputs=[img_status, img_video_output])
        
        gr.Markdown("---")
        gr.Markdown("#### " + ("视频转图片" if lang == 'zh' else "Video to Images"))
        with gr.Row():
            with gr.Column(scale=1):
                v2i_video_input = gr.File(
                    label="选择视频" if lang == 'zh' else "Select Video",
                    file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"]
                )
            with gr.Column(scale=1):
                v2i_fps = gr.Slider(minimum=1, maximum=30, value=1, step=1, label="提取帧率 (FPS)" if lang == 'zh' else "Extract FPS")
                v2i_format = gr.Dropdown(
                    choices=["png", "jpg", "bmp"],
                    value="png",
                    label="图片格式" if lang == 'zh' else "Image Format"
                )
                v2i_btn = gr.Button("🔄 " + ("提取图片" if lang == 'zh' else "Extract Images"), variant="primary")
            with gr.Column(scale=1):
                v2i_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=5)
                v2i_gallery = gr.Gallery(label="提取的图片" if lang == 'zh' else "Extracted Images", columns=3, height=200)
        
        def do_video_to_images(file, fps, fmt):
            if not file:
                return "请选择视频 / Please select video", None
            
            result = video_to_images(file.name, fps, fmt)
            cmd_str = " ".join(result.get("cmd", []))
            
            if result["success"]:
                return f"✅ 提取成功 ({result['image_count']}张图片)\n📁 输出目录: {result['output_dir']}\n\n💻 CMD:\n{cmd_str}", result["image_paths"]
            else:
                return f"❌ {result['error']}\n\n💻 CMD:\n{cmd_str}", None
        
        v2i_btn.click(do_video_to_images, inputs=[v2i_video_input, v2i_fps, v2i_format], outputs=[v2i_status, v2i_gallery])
    
    return col
