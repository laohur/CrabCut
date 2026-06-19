import gradio as gr
from utils.cropper import crop_video, trim_video, get_video_frame, crop_image
from utils.metadata import get_media_metadata
from utils.i18n import translate_text

def create_cropper_page(lang="zh"):
    with gr.Column() as col:
        gr.Markdown("#### " + ("时间裁剪" if lang == 'zh' else "Time Trim"))
        with gr.Row():
            with gr.Column(scale=1):
                trim_input = gr.File(label="选择视频" if lang == 'zh' else "Select Video", file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm"])
                trim_video_preview = gr.Video(label="原视频预览" if lang == 'zh' else "Original Video")
                trim_duration = gr.Textbox(label="视频时长" if lang == 'zh' else "Duration", interactive=False)
            with gr.Column(scale=1):
                trim_start = gr.Number(label="开始时间(秒)" if lang == 'zh' else "Start Time (s)", value=0)
                trim_end = gr.Number(label="结束时间(秒)" if lang == 'zh' else "End Time (s)", value=0)
                trim_btn = gr.Button("✂️ " + ("裁剪" if lang == 'zh' else "Trim"), variant="primary")
            with gr.Column(scale=1):
                trim_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                trim_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def load_trim_video(file):
            if not file:
                return None, ""
            result = get_media_metadata(file.name)
            if result["success"]:
                duration = result.get("duration", 0)
                return file.name, f"{duration:.2f}s"
            return file.name, ""
        
        def do_trim(file, start, end):
            if not file:
                return "请选择视频 / Please select video", None
            result = trim_video(file.name if hasattr(file, 'name') else file, float(start), float(end))
            if result["success"]:
                return f"✅ 裁剪成功\n📁 {result['output_path']}", result["output_path"]
            return f"❌ {result['error']}", None
        
        trim_input.change(load_trim_video, inputs=[trim_input], outputs=[trim_video_preview, trim_duration])
        trim_btn.click(do_trim, inputs=[trim_input, trim_start, trim_end], outputs=[trim_status, trim_output])
        
        gr.Markdown("---")
        gr.Markdown("#### " + ("视频区域裁剪" if lang == 'zh' else "Video Area Crop"))
        with gr.Row():
            with gr.Column(scale=1):
                vcrop_input = gr.File(label="选择视频" if lang == 'zh' else "Select Video", file_types=[".mp4", ".avi", ".mkv", ".mov", ".webm"])
                vcrop_video_preview = gr.Video(label="预览视频" if lang == 'zh' else "Preview Video")
                vcrop_duration = gr.Textbox(label="视频时长" if lang == 'zh' else "Duration", interactive=False)
            with gr.Column(scale=1):
                vcrop_time = gr.Number(label="截图时间点(秒)" if lang == 'zh' else "Screenshot Time (s)", value=0)
                preview_btn = gr.Button("🔍 " + ("预览" if lang == 'zh' else "Preview"), variant="secondary")
                
                vcrop_frame = gr.Image(label="选择裁剪区域" if lang == 'zh' else "Select Crop Area")
                
                with gr.Row():
                    vcrop_x = gr.Number(label="X", value=0)
                    vcrop_y = gr.Number(label="Y", value=0)
                with gr.Row():
                    vcrop_w = gr.Number(label="宽度" if lang == 'zh' else "Width", value=0)
                    vcrop_h = gr.Number(label="高度" if lang == 'zh' else "Height", value=0)
                
                vcrop_btn = gr.Button("✂️ " + ("裁剪视频" if lang == 'zh' else "Crop Video"), variant="primary")
            with gr.Column(scale=1):
                vcrop_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                vcrop_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def load_vcrop_video(file):
            if not file:
                return None, "", None, 0, 0, 0, 0
            result = get_media_metadata(file.name)
            if result["success"]:
                duration = result.get("duration", 0)
                video_info = result.get("video", {})
                width = video_info.get("width", 0)
                height = video_info.get("height", 0)
                frame_result = get_video_frame(file.name, 0)
                frame_path = frame_result.get("frame_path") if frame_result["success"] else None
                return file.name, f"{duration:.2f}s ({width}x{height})", frame_path, 0, 0, width, height
            return file.name, "", None, 0, 0, 0, 0
        
        def do_preview(file, time):
            if not file:
                return None
            result = get_video_frame(file.name if hasattr(file, 'name') else file, float(time))
            if result["success"]:
                return result["frame_path"]
            return None
        
        def do_vcrop(file, x, y, w, h):
            if not file:
                return "请选择视频 / Please select video", None
            if w <= 0 or h <= 0:
                return "请输入有效的裁剪区域 / Please enter valid crop area", None
            result = crop_video(file.name if hasattr(file, 'name') else file, 0, 0, int(x), int(y), int(w), int(h))
            if result["success"]:
                return f"✅ 裁剪成功\n📁 {result['output_path']}", result["output_path"]
            return f"❌ {result['error']}", None
        
        vcrop_input.change(load_vcrop_video, inputs=[vcrop_input], outputs=[vcrop_video_preview, vcrop_duration, vcrop_frame, vcrop_x, vcrop_y, vcrop_w, vcrop_h])
        preview_btn.click(do_preview, inputs=[vcrop_input, vcrop_time], outputs=[vcrop_frame])
        vcrop_btn.click(do_vcrop, inputs=[vcrop_input, vcrop_x, vcrop_y, vcrop_w, vcrop_h], outputs=[vcrop_status, vcrop_output])
        
        gr.Markdown("---")
        gr.Markdown("#### " + ("图片裁剪" if lang == 'zh' else "Image Crop"))
        with gr.Row():
            with gr.Column(scale=1):
                icrop_input = gr.File(label="选择图片" if lang == 'zh' else "Select Image", file_types=["image"])
                icrop_preview = gr.Image(label="预览图片" if lang == 'zh' else "Preview Image")
                icrop_size = gr.Textbox(label="图片尺寸" if lang == 'zh' else "Image Size", interactive=False)
            with gr.Column(scale=1):
                with gr.Row():
                    icrop_x = gr.Number(label="X", value=0)
                    icrop_y = gr.Number(label="Y", value=0)
                with gr.Row():
                    icrop_w = gr.Number(label="宽度" if lang == 'zh' else "Width", value=0)
                    icrop_h = gr.Number(label="高度" if lang == 'zh' else "Height", value=0)
                icrop_btn = gr.Button("✂️ " + ("裁剪" if lang == 'zh' else "Crop"), variant="primary")
            with gr.Column(scale=1):
                icrop_status = gr.Textbox(label=translate_text('common.status', lang) if lang == 'zh' else "Status", interactive=False, lines=3)
                icrop_output = gr.Image(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def load_icrop_image(file):
            if not file:
                return None, "", 0, 0, 0, 0
            from PIL import Image
            img = Image.open(file.name)
            return file.name, f"{img.width} x {img.height}", 0, 0, img.width, img.height
        
        def do_icrop(file, x, y, w, h):
            if not file:
                return "请选择图片 / Please select image", None
            if w <= 0 or h <= 0:
                return "请输入有效的裁剪区域 / Please enter valid crop area", None
            result = crop_image(file.name if hasattr(file, 'name') else file, int(x), int(y), int(w), int(h))
            if result["success"]:
                return f"✅ 裁剪成功\n📁 {result['output_path']}", result["output_path"]
            return f"❌ {result['error']}", None
        
        icrop_input.change(load_icrop_image, inputs=[icrop_input], outputs=[icrop_preview, icrop_size, icrop_x, icrop_y, icrop_w, icrop_h])
        icrop_btn.click(do_icrop, inputs=[icrop_input, icrop_x, icrop_y, icrop_w, icrop_h], outputs=[icrop_status, icrop_output])
    
    return col
