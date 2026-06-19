import gradio as gr
from utils.downloader import download_video, download_multiple, get_video_info
from utils.i18n import translate_text
from config import LANGUAGES

def create_downloader_page(lang="zh"):
    with gr.Column() as col:
        with gr.Row():
            with gr.Column(scale=2):
                url_input = gr.Textbox(
                    label=translate_text('downloader.urls', lang) if lang == 'zh' else "Video URLs (one per line)",
                    placeholder="https://www.youtube.com/watch?v=...\nhttps://www.bilibili.com/video/...",
                    lines=5,
                    interactive=True
                )
            
            with gr.Column(scale=1):
                format_type = gr.Radio(
                    choices=[
                        ("视频 (Video)", "video"),
                        ("音频 (Audio)", "audio")
                    ],
                    value="video",
                    label=translate_text('downloader.format', lang) if lang == 'zh' else "Format",
                    interactive=True
                )
        
        with gr.Row():
            preview_btn = gr.Button("🔍 " + (translate_text('common.preview', lang) if lang == 'zh' else "Preview"), variant="secondary")
            download_btn = gr.Button("⬇️ " + (translate_text('common.download', lang) if lang == 'zh' else "Download"), variant="primary")
            clear_btn = gr.Button("🗑️ " + (translate_text('common.clear', lang) if lang == 'zh' else "Clear"), variant="secondary")
        
        with gr.Row():
            preview_output = gr.HTML(label=translate_text('downloader.preview', lang) if lang == 'zh' else "Preview")
        
        status_output = gr.Textbox(
            label=translate_text('common.status', lang) if lang == 'zh' else "Status",
            interactive=False,
            lines=5
        )
        
        video_output = gr.Video(label=translate_text('common.output', lang) if lang == 'zh' else "Output")
        
        def preview_video(urls):
            if not urls.strip():
                return "<p>请输入链接 / Please enter a URL</p>"
            
            first_url = urls.strip().split('\n')[0].strip()
            info = get_video_info(first_url)
            
            if info['success']:
                thumbnail = info.get('thumbnail', '')
                thumbnail_html = f'<img src="{thumbnail}" style="max-width:300px;border-radius:8px;">' if thumbnail else ''
                
                info_items = []
                for key, value in info.items():
                    if key != 'success' and key != 'thumbnail' and value:
                        info_items.append(f"<p><strong>{key}:</strong> {value}</p>")
                
                return f"""
<div style="padding:10px;">
    {thumbnail_html}
    {''.join(info_items)}
</div>
"""
            else:
                return f"<p style='color:red;'>❌ {info.get('error', 'Unknown error')}</p>"
        
        def do_download(urls, fmt):
            if not urls.strip():
                return "请输入链接 / Please enter URLs", None
            
            results = download_multiple(urls, fmt)
            
            status_lines = []
            downloaded_files = []
            
            for r in results:
                if r['success']:
                    status_lines.append(f"✅ {r['title']}")
                    status_lines.append(f"   📁 {r['filename']}")
                    downloaded_files.append(r['filename'])
                else:
                    status_lines.append(f"❌ {r['url']}: {r.get('error', 'Unknown error')}")
            
            output_file = downloaded_files[0] if len(downloaded_files) == 1 else None
            
            if len(downloaded_files) > 1:
                status_lines.append(f"\n共下载 {len(downloaded_files)} 个文件")
            
            return "\n".join(status_lines), output_file
        
        def clear_all():
            return "", "video", "<p></p>", "", None
        
        preview_btn.click(preview_video, inputs=[url_input], outputs=[preview_output])
        download_btn.click(do_download, inputs=[url_input, format_type], outputs=[status_output, video_output])
        clear_btn.click(clear_all, outputs=[url_input, format_type, preview_output, status_output, video_output])
    
    return col
