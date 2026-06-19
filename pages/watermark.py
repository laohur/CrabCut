import gradio as gr
from utils.watermark import add_image_watermark, add_text_watermark, add_blur_watermark, generate_preview
from utils.i18n import translate_text

def create_watermark_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("水印工具" if lang == 'zh' else "Watermark Tool"))
        
        with gr.Tabs():
            with gr.TabItem("图片水印" if lang == 'zh' else "Image Watermark"):
                with gr.Row():
                    with gr.Column(scale=1):
                        img_wm_input = gr.File(
                            label="选择视频/图片" if lang == 'zh' else "Select Video/Image",
                            file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm", ".jpg", ".png", ".jpeg"]
                        )
                        img_wm_file = gr.File(
                            label="选择水印图片" if lang == 'zh' else "Select Watermark Image",
                            file_types=[".png", ".jpg", ".jpeg"]
                        )
                    
                    with gr.Column(scale=1):
                        img_wm_position = gr.Radio(
                            choices=[
                                ("左上" if lang == 'zh' else "Top Left", "top_left"),
                                ("右上" if lang == 'zh' else "Top Right", "top_right"),
                                ("左下" if lang == 'zh' else "Bottom Left", "bottom_left"),
                                ("右下" if lang == 'zh' else "Bottom Right", "bottom_right"),
                                ("居中" if lang == 'zh' else "Center", "center"),
                            ],
                            value="bottom_right",
                            label="位置" if lang == 'zh' else "Position"
                        )
                        img_wm_opacity = gr.Slider(
                            minimum=0.1, maximum=1.0, value=0.7, step=0.1,
                            label="透明度" if lang == 'zh' else "Opacity"
                        )
                    
                    with gr.Column(scale=1):
                        img_wm_preview_btn = gr.Button("👁️ " + ("预览" if lang == 'zh' else "Preview"), variant="secondary")
                        img_wm_btn = gr.Button("💧 " + ("添加水印" if lang == 'zh' else "Add Watermark"), variant="primary")
                        img_wm_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=2)
                        img_wm_preview = gr.Image(label="预览" if lang == 'zh' else "Preview")
                        img_wm_output = gr.Video(label="输出" if lang == 'zh' else "Output")
                
                def do_img_wm_preview(video, wm_img, position, opacity):
                    if not video or not wm_img:
                        return "请选择视频和水印图片 / Please select video and watermark", None, None
                    result = generate_preview(
                        video.name, 
                        watermark_type="image",
                        watermark_path=wm_img.name,
                        position=position,
                        opacity=opacity
                    )
                    if result["success"]:
                        return "预览生成成功 / Preview generated", result["preview_path"], None
                    return f"❌ {result['error']}", None, None
                
                def do_img_wm(video, wm_img, position, opacity):
                    if not video or not wm_img:
                        return "请选择视频和水印图片 / Please select video and watermark", None
                    result = add_image_watermark(
                        video.name,
                        wm_img.name,
                        position=position,
                        opacity=opacity
                    )
                    if result["success"]:
                        return f"✅ 水印添加成功\n📁 {result['output_path']}", result["output_path"]
                    return f"❌ {result['error']}", None
                
                img_wm_preview_btn.click(do_img_wm_preview, inputs=[img_wm_input, img_wm_file, img_wm_position, img_wm_opacity], outputs=[img_wm_status, img_wm_preview, img_wm_output])
                img_wm_btn.click(do_img_wm, inputs=[img_wm_input, img_wm_file, img_wm_position, img_wm_opacity], outputs=[img_wm_status, img_wm_output])
            
            with gr.TabItem("文字水印" if lang == 'zh' else "Text Watermark"):
                with gr.Row():
                    with gr.Column(scale=1):
                        txt_wm_input = gr.File(
                            label="选择视频/图片" if lang == 'zh' else "Select Video/Image",
                            file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm", ".jpg", ".png", ".jpeg"]
                        )
                        txt_wm_text = gr.Textbox(
                            label="水印文字" if lang == 'zh' else "Watermark Text",
                            placeholder="输入水印文字..." if lang == 'zh' else "Enter watermark text..."
                        )
                    
                    with gr.Column(scale=1):
                        txt_wm_position = gr.Radio(
                            choices=[
                                ("左上" if lang == 'zh' else "Top Left", "top_left"),
                                ("右上" if lang == 'zh' else "Top Right", "top_right"),
                                ("左下" if lang == 'zh' else "Bottom Left", "bottom_left"),
                                ("右下" if lang == 'zh' else "Bottom Right", "bottom_right"),
                                ("居中" if lang == 'zh' else "Center", "center"),
                            ],
                            value="bottom_right",
                            label="位置" if lang == 'zh' else "Position"
                        )
                        txt_wm_font_size = gr.Slider(
                            minimum=12, maximum=72, value=24, step=2,
                            label="字体大小" if lang == 'zh' else "Font Size"
                        )
                        txt_wm_font_color = gr.ColorPicker(
                            value="#FFFFFF",
                            label="字体颜色" if lang == 'zh' else "Font Color"
                        )
                        txt_wm_opacity = gr.Slider(
                            minimum=0.1, maximum=1.0, value=0.7, step=0.1,
                            label="透明度" if lang == 'zh' else "Opacity"
                        )
                    
                    with gr.Column(scale=1):
                        txt_wm_preview_btn = gr.Button("👁️ " + ("预览" if lang == 'zh' else "Preview"), variant="secondary")
                        txt_wm_btn = gr.Button("💧 " + ("添加水印" if lang == 'zh' else "Add Watermark"), variant="primary")
                        txt_wm_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=2)
                        txt_wm_preview = gr.Image(label="预览" if lang == 'zh' else "Preview")
                        txt_wm_output = gr.Video(label="输出" if lang == 'zh' else "Output")
                
                def do_txt_wm_preview(video, text, position, font_size, font_color, opacity):
                    if not video or not text:
                        return "请选择视频并输入水印文字 / Please select video and enter text", None, None
                    result = generate_preview(
                        video.name,
                        watermark_type="text",
                        text=text,
                        position=position,
                        opacity=opacity,
                        font_size=font_size,
                        font_color=font_color.lstrip('#')
                    )
                    if result["success"]:
                        return "预览生成成功 / Preview generated", result["preview_path"], None
                    return f"❌ {result['error']}", None, None
                
                def do_txt_wm(video, text, position, font_size, font_color, opacity):
                    if not video or not text:
                        return "请选择视频并输入水印文字 / Please select video and enter text", None
                    result = add_text_watermark(
                        video.name,
                        text,
                        position=position,
                        font_size=font_size,
                        font_color=font_color.lstrip('#'),
                        opacity=opacity
                    )
                    if result["success"]:
                        return f"✅ 水印添加成功\n📁 {result['output_path']}", result["output_path"]
                    return f"❌ {result['error']}", None
                
                txt_wm_preview_btn.click(do_txt_wm_preview, inputs=[txt_wm_input, txt_wm_text, txt_wm_position, txt_wm_font_size, txt_wm_font_color, txt_wm_opacity], outputs=[txt_wm_status, txt_wm_preview, txt_wm_output])
                txt_wm_btn.click(do_txt_wm, inputs=[txt_wm_input, txt_wm_text, txt_wm_position, txt_wm_font_size, txt_wm_font_color, txt_wm_opacity], outputs=[txt_wm_status, txt_wm_output])
            
            with gr.TabItem("模糊水印" if lang == 'zh' else "Blur Watermark"):
                with gr.Row():
                    with gr.Column(scale=1):
                        blur_wm_input = gr.Video(
                            label="选择视频" if lang == 'zh' else "Select Video",
                        )
                        blur_wm_info = gr.Textbox(
                            label="视频信息" if lang == 'zh' else "Video Info",
                            interactive=False,
                            lines=2
                        )
                    
                    with gr.Column(scale=1):
                        blur_wm_x = gr.Number(value=10, label="X坐标" if lang == 'zh' else "X Position")
                        blur_wm_y = gr.Number(value=10, label="Y坐标" if lang == 'zh' else "Y Position")
                        blur_wm_width = gr.Number(value=200, label="宽度" if lang == 'zh' else "Width")
                        blur_wm_height = gr.Number(value=100, label="高度" if lang == 'zh' else "Height")
                        blur_wm_strength = gr.Slider(
                            minimum=1, maximum=12, value=5, step=1,
                            label="模糊强度" if lang == 'zh' else "Blur Strength"
                        )
                    
                    with gr.Column(scale=1):
                        blur_wm_btn = gr.Button("🌫️ " + ("添加模糊" if lang == 'zh' else "Add Blur"), variant="primary")
                        blur_wm_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=2)
                        blur_wm_output = gr.Video(label="输出" if lang == 'zh' else "Output")
                
                def update_blur_video_info(video):
                    if not video:
                        return ""
                    from utils.metadata import get_media_metadata
                    result = get_media_metadata(video)
                    if result.get("success"):
                        video_info = result.get("video", {})
                        width = video_info.get("width", 0)
                        height = video_info.get("height", 0)
                        duration = result.get("duration", 0)
                        return f"尺寸: {width} x {height}\n时长: {duration:.2f}s"
                    return "无法获取视频信息"
                
                blur_wm_input.change(update_blur_video_info, inputs=[blur_wm_input], outputs=[blur_wm_info])
                
                def do_blur_wm(video, x, y, width, height, strength):
                    if not video:
                        return "请选择视频 / Please select video", None
                    result = add_blur_watermark(
                        video,
                        x=int(x),
                        y=int(y),
                        width=int(width),
                        height=int(height),
                        blur_strength=int(strength)
                    )
                    if result["success"]:
                        return f"✅ 模糊添加成功\n📁 {result['output_path']}", result["output_path"]
                    return f"❌ {result['error']}", None
                
                blur_wm_btn.click(do_blur_wm, inputs=[blur_wm_input, blur_wm_x, blur_wm_y, blur_wm_width, blur_wm_height, blur_wm_strength], outputs=[blur_wm_status, blur_wm_output])
