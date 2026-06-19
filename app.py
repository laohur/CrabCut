import gradio as gr
from config import LANGUAGES, DEFAULT_LANG
from utils.i18n import translate_text
from utils.log_config import logger
from pages.downloader import create_downloader_page
from pages.metadata import create_metadata_page
from pages.converter import create_converter_page
from pages.cropper import create_cropper_page
from pages.merger import create_merger_page
from pages.separator import create_separator_page
from pages.av_merger import create_av_merger_page
from pages.watermark import create_watermark_page
from pages.composer import create_composer_page
from pages.ocr import create_ocr_page
from pages.asr import create_asr_page
from pages.tts import create_tts_page
from pages.translate import create_translate_page
from pages.auto_cut import create_auto_edit_page

PAGES = [
    ("downloader",  "📥", create_downloader_page),
    ("metadata",    "📋", create_metadata_page),
    ("converter",   "🔄", create_converter_page),
    ("cropper",     "✂️", create_cropper_page),
    ("merger",      "🔗", create_merger_page),
    ("separator",   "🎵", create_separator_page),
    ("av_merger",   "🎬", create_av_merger_page),
    ("watermark",   "💧", create_watermark_page),
    ("composer",    "🎞️", create_composer_page),
    ("ocr",         "📝", create_ocr_page),
    ("asr",         "🎤", create_asr_page),
    ("tts",         "🔊", create_tts_page),
    ("translate",   "🌐", create_translate_page),
    ("auto_edit",   "🤖", create_auto_edit_page),
]


def build_app():
    with gr.Blocks(title="CrabCut 螃蟹快剪", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🦀 CrabCut 螃蟹快剪")

        with gr.Tabs():
            with gr.TabItem("🇨🇳 中文"):
                with gr.Tabs():
                    for page_id, icon, page_fn in PAGES:
                        with gr.TabItem(f"{icon} {translate_text(f'nav.{page_id}', 'zh')}"):
                            page_fn("zh")

            with gr.TabItem("🇺🇸 English"):
                with gr.Tabs():
                    for page_id, icon, page_fn in PAGES:
                        with gr.TabItem(f"{icon} {translate_text(f'nav.{page_id}', 'en')}"):
                            page_fn("en")

    return app


if __name__ == "__main__":
    logger.info("\n\n\n\nCrabCut 螃蟹快剪 启动中...")
    app = build_app()
    logger.success("应用启动成功")
    app.launch()
