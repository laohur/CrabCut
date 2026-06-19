import gradio as gr
from utils.composer import compose_video, SUBTITLE_FONTS
from utils.i18n import translate_text
from utils.log_config import logger

def create_composer_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("视频合成工具" if lang == 'zh' else "Video Composer"))
        
        with gr.Row():
            with gr.Column(scale=1):
                video_input = gr.File(
                    label="选择视频" if lang == 'zh' else "Select Video",
                    file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm"]
                )
                audio_input = gr.File(
                    label="选择音频（可选）" if lang == 'zh' else "Select Audio (Optional)",
                    file_types=[".mp3", ".wav", ".flac", ".aac", ".ogg"]
                )
                subtitle_input = gr.File(
                    label="选择字幕（可选）" if lang == 'zh' else "Select Subtitle (Optional)",
                    file_types=[".srt", ".ass", ".ssa"]
                )
            
            with gr.Column(scale=1):
                with gr.Accordion("音频设置" if lang == 'zh' else "Audio Settings", open=True):
                    video_volume = gr.Slider(
                        minimum=0.0, maximum=2.0, value=1.0, step=0.1,
                        label="原视频音量" if lang == 'zh' else "Original Video Volume"
                    )
                    audio_volume = gr.Slider(
                        minimum=0.0, maximum=2.0, value=1.0, step=0.1,
                        label="添加音频音量" if lang == 'zh' else "Added Audio Volume"
                    )
                
                with gr.Accordion("字幕设置" if lang == 'zh' else "Subtitle Settings", open=False):
                    subtitle_embed = gr.Radio(
                        choices=[
                            ("硬嵌入（烧录到视频）" if lang == 'zh' else "Hard (Burn into video)", "hard"),
                            ("软嵌入（作为独立轨道）" if lang == 'zh' else "Soft (As separate track)", "soft"),
                        ],
                        value="hard",
                        label="嵌入方式" if lang == 'zh' else "Embed Method"
                    )
                    
                    subtitle_font = gr.Dropdown(
                        choices=list(SUBTITLE_FONTS.values()),
                        value=SUBTITLE_FONTS["default"],
                        label="字体" if lang == 'zh' else "Font",
                        filterable=True
                    )
                    
                    subtitle_font_size = gr.Slider(
                        minimum=12, maximum=72, value=24, step=2,
                        label="字体大小" if lang == 'zh' else "Font Size"
                    )
                    
                    with gr.Row():
                        subtitle_color = gr.ColorPicker(
                            value="#ffffff",
                            label="字体颜色" if lang == 'zh' else "Font Color"
                        )
                        subtitle_outline_color = gr.ColorPicker(
                            value="#000000",
                            label="描边颜色" if lang == 'zh' else "Outline Color"
                        )
                    
                    subtitle_outline = gr.Slider(
                        minimum=0, maximum=5, value=2, step=1,
                        label="描边宽度" if lang == 'zh' else "Outline Width"
                    )
                    
                    with gr.Row():
                        subtitle_bg_color = gr.ColorPicker(
                            value="#000000",
                            label="背景颜色" if lang == 'zh' else "Background Color"
                        )
                        subtitle_bg_opacity = gr.Slider(
                            minimum=0.0, maximum=1.0, value=0.5, step=0.1,
                            label="背景透明度" if lang == 'zh' else "Background Opacity"
                        )
                    
                    subtitle_margin_v = gr.Slider(
                        minimum=0, maximum=100, value=20, step=5,
                        label="底部边距" if lang == 'zh' else "Bottom Margin"
                    )
                
                with gr.Accordion("水印设置" if lang == 'zh' else "Watermark Settings", open=False):
                    watermark_type = gr.Radio(
                        choices=[
                            ("无" if lang == 'zh' else "None", "none"),
                            ("图片水印" if lang == 'zh' else "Image", "image"),
                            ("文字水印" if lang == 'zh' else "Text", "text"),
                        ],
                        value="none",
                        label="水印类型" if lang == 'zh' else "Watermark Type"
                    )
                    watermark_file = gr.File(
                        label="选择水印图片" if lang == 'zh' else "Select Watermark Image",
                        file_types=[".png", ".jpg", ".jpeg"],
                        visible=False
                    )
                    text_watermark = gr.Textbox(
                        label="水印文字" if lang == 'zh' else "Watermark Text",
                        visible=False
                    )
                    watermark_position = gr.Radio(
                        choices=[
                            ("左上" if lang == 'zh' else "Top Left", "top_left"),
                            ("右上" if lang == 'zh' else "Top Right", "top_right"),
                            ("左下" if lang == 'zh' else "Bottom Left", "bottom_left"),
                            ("右下" if lang == 'zh' else "Bottom Right", "bottom_right"),
                            ("居中" if lang == 'zh' else "Center", "center"),
                        ],
                        value="bottom_right",
                        label="位置" if lang == 'zh' else "Position",
                        visible=False
                    )
                    watermark_opacity = gr.Slider(
                        minimum=0.1, maximum=1.0, value=0.7, step=0.1,
                        label="透明度" if lang == 'zh' else "Opacity",
                        visible=False
                    )
                    text_font_size = gr.Slider(
                        minimum=12, maximum=72, value=24, step=2,
                        label="字体大小" if lang == 'zh' else "Font Size",
                        visible=False
                    )
                    text_color = gr.ColorPicker(
                        value="#ffffff",
                        label="文字颜色" if lang == 'zh' else "Text Color",
                        visible=False
                    )
            
            with gr.Column(scale=1):
                output_format = gr.Dropdown(
                    choices=["mp4", "mkv", "mov"],
                    value="mp4",
                    label="输出格式" if lang == 'zh' else "Output Format"
                )
                compose_btn = gr.Button("🎬 " + ("合成视频" if lang == 'zh' else "Compose Video"), variant="primary")
                status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def update_watermark_ui(wm_type):
            if wm_type == "image":
                return [
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                ]
            elif wm_type == "text":
                return [
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=True),
                ]
            else:
                return [
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                ]
        
        watermark_type.change(
            update_watermark_ui,
            inputs=[watermark_type],
            outputs=[watermark_file, text_watermark, watermark_position, watermark_opacity, text_font_size, text_color]
        )
        
        def do_compose(video, audio, subtitle, audio_vol, video_vol, 
                       sub_embed, sub_font, sub_font_size, sub_color, sub_outline_color, 
                       sub_outline, sub_bg_color, sub_bg_opacity, sub_margin_v,
                       wm_type, wm_file, text_wm, wm_pos, wm_opacity, font_size, text_clr, fmt):
            logger.info(f"开始视频合成: video={video.name if video else None}, audio={audio.name if audio else None}, subtitle={subtitle.name if subtitle else None}")
            
            if not video:
                return "请选择视频文件 / Please select video file", None
            
            wm_path = None
            text_watermark_val = None
            
            if wm_type == "image" and wm_file:
                wm_path = wm_file.name
            elif wm_type == "text" and text_wm:
                text_watermark_val = text_wm
            
            audio_path = audio.name if audio else None
            sub_path = subtitle.name if subtitle else None
            
            result = compose_video(
                video_path=video.name,
                audio_path=audio_path,
                audio_volume=audio_vol,
                video_volume=video_vol,
                subtitle_path=sub_path,
                subtitle_embed=sub_embed,
                subtitle_font=sub_font,
                subtitle_font_size=int(sub_font_size),
                subtitle_color=sub_color.lstrip('#'),
                subtitle_bg_color=sub_bg_color.lstrip('#'),
                subtitle_bg_opacity=sub_bg_opacity,
                subtitle_outline=int(sub_outline),
                subtitle_outline_color=sub_outline_color.lstrip('#'),
                subtitle_margin_v=int(sub_margin_v),
                watermark_path=wm_path,
                watermark_position=wm_pos,
                watermark_opacity=wm_opacity,
                text_watermark=text_watermark_val,
                text_font_size=int(font_size),
                text_color=text_clr.lstrip('#'),
                output_format=fmt
            )
            
            if result["success"]:
                sub_info = ""
                if sub_path:
                    sub_type = "硬嵌入" if sub_embed == "hard" else "软嵌入"
                    sub_info = f"\n📝 字幕: {sub_type}"
                logger.success(f"视频合成完成: {result['output_path']}")
                return f"✅ 合成成功\n📁 {result['output_path']}{sub_info}", result["output_path"]
            logger.error(f"视频合成失败: {result['error']}")
            return f"❌ {result['error']}", None
        
        compose_btn.click(
            do_compose,
            inputs=[
                video_input, audio_input, subtitle_input,
                audio_volume, video_volume,
                subtitle_embed, subtitle_font, subtitle_font_size, 
                subtitle_color, subtitle_outline_color, subtitle_outline,
                subtitle_bg_color, subtitle_bg_opacity, subtitle_margin_v,
                watermark_type, watermark_file, text_watermark,
                watermark_position, watermark_opacity, text_font_size, text_color,
                output_format
            ],
            outputs=[status, output]
        )
