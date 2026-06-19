import gradio as gr
from utils.metadata import get_media_metadata, format_duration, format_size, format_bitrate
from utils.i18n import translate_text

def create_metadata_page(lang="zh"):
    with gr.Column() as col:
        file_input = gr.File(
            label=translate_text('common.select_file', lang) if lang == 'zh' else "Select a file",
            file_types=[".mp4", ".avi", ".mkv", ".mov", ".mp3", ".wav", ".flac", ".aac", ".m4a", ".webm"]
        )
        
        analyze_btn = gr.Button("🔍 " + (translate_text('common.preview', lang) if lang == 'zh' else "Analyze"), variant="primary")
        clear_btn = gr.Button("🗑️ " + (translate_text('common.clear', lang) if lang == 'zh' else "Clear"), variant="secondary")
        
        with gr.Row():
            with gr.Column(scale=1):
                video_preview = gr.Video(label="视频预览" if lang == 'zh' else "Video Preview", visible=False)
                audio_preview = gr.Audio(label="音频预览" if lang == 'zh' else "Audio Preview", visible=False)
        
        metadata_output = gr.HTML(label="元数据信息" if lang == 'zh' else "Metadata")
        
        def analyze_file(file):
            if not file:
                return gr.update(visible=False), gr.update(visible=False), "<p>请选择文件 / Please select a file</p>"
            
            result = get_media_metadata(file.name)
            
            if not result.get("success"):
                return gr.update(visible=False), gr.update(visible=False), f"<p style='color:red;'>❌ {result.get('error', 'Unknown error')}</p>"
            
            is_video = "video" in result
            is_audio = "audio" in result and not is_video
            
            html_parts = [f"""
<div style="padding:15px;background:#f5f5f5;border-radius:8px;">
    <h3>📁 {'基本信息' if lang == 'zh' else 'Basic Info'}</h3>
    <table style="width:100%;">
        <tr><td><strong>文件名:</strong></td><td>{result.get('filename', '')}</td></tr>
        <tr><td><strong>格式:</strong></td><td>{result.get('format', '')}</td></tr>
        <tr><td><strong>时长:</strong></td><td>{format_duration(result.get('duration', 0))}</td></tr>
        <tr><td><strong>大小:</strong></td><td>{format_size(result.get('size', 0))}</td></tr>
        <tr><td><strong>比特率:</strong></td><td>{format_bitrate(result.get('bit_rate', 0))}</td></tr>
    </table>
"""]
            
            if "video" in result:
                v = result["video"]
                html_parts.append(f"""
    <h3>🎬 {'视频流' if lang == 'zh' else 'Video Stream'}</h3>
    <table style="width:100%;">
        <tr><td><strong>编码:</strong></td><td>{v.get('codec', '')} ({v.get('codec_long', '')})</td></tr>
        <tr><td><strong>分辨率:</strong></td><td>{v.get('width', 0)} x {v.get('height', 0)}</td></tr>
        <tr><td><strong>帧率:</strong></td><td>{v.get('fps', 0):.2f} fps</td></tr>
        <tr><td><strong>宽高比:</strong></td><td>{v.get('aspect_ratio', 'N/A')}</td></tr>
    </table>
""")
            
            if "audio" in result:
                a = result["audio"]
                html_parts.append(f"""
    <h3>🎵 {'音频流' if lang == 'zh' else 'Audio Stream'}</h3>
    <table style="width:100%;">
        <tr><td><strong>编码:</strong></td><td>{a.get('codec', '')} ({a.get('codec_long', '')})</td></tr>
        <tr><td><strong>采样率:</strong></td><td>{a.get('sample_rate', 0)} Hz</td></tr>
        <tr><td><strong>声道数:</strong></td><td>{a.get('channels', 0)}</td></tr>
        <tr><td><strong>声道布局:</strong></td><td>{a.get('channel_layout', 'N/A')}</td></tr>
    </table>
""")
            
            if "tags" in result:
                tags = result["tags"]
                tags_html = "".join([f"<tr><td><strong>{k}:</strong></td><td>{v}</td></tr>" for k, v in tags.items()])
                html_parts.append(f"""
    <h3>🏷️ {'标签信息' if lang == 'zh' else 'Tags'}</h3>
    <table style="width:100%;">{tags_html}</table>
""")
            
            html_parts.append("</div>")
            
            video_update = gr.update(value=file.name, visible=is_video) if is_video else gr.update(visible=False)
            audio_update = gr.update(value=file.name, visible=is_audio) if is_audio else gr.update(visible=False)
            
            return video_update, audio_update, "".join(html_parts)
        
        def clear_all():
            return None, gr.update(visible=False), gr.update(visible=False), "<p></p>"
        
        analyze_btn.click(analyze_file, inputs=[file_input], outputs=[video_preview, audio_preview, metadata_output])
        clear_btn.click(clear_all, outputs=[file_input, video_preview, audio_preview, metadata_output])
    
    return col
