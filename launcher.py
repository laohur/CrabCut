import gradio as gr
from config import LANGUAGES, DEFAULT_LANG
from utils.i18n import translate_text
from utils.log_config import logger

PAGES = [
    ("downloader",  "📥", "pages.downloader",  "create_downloader_page"),
    ("metadata",    "📋", "pages.metadata",    "create_metadata_page"),
    ("converter",   "🔄", "pages.converter",   "create_converter_page"),
    ("cropper",     "✂️", "pages.cropper",     "create_cropper_page"),
    ("merger",      "🔗", "pages.merger",      "create_merger_page"),
    ("separator",   "🎵", "pages.separator",   "create_separator_page"),
    ("av_merger",   "🎬", "pages.av_merger",   "create_av_merger_page"),
    ("watermark",   "💧", "pages.watermark",   "create_watermark_page"),
    ("composer",    "🎞️", "pages.composer",    "create_composer_page"),
    ("ocr",         "📝", "pages.ocr",         "create_ocr_page"),
    ("asr",         "🎤", "pages.asr",         "create_asr_page"),
    ("tts",         "🔊", "pages.tts",         "create_tts_page"),
    ("translate",   "🌐", "pages.translate",   "create_translate_page"),
    ("auto_edit",   "🤖", "pages.auto_cut",    "create_auto_edit_page"),
]

_cache = {}


def _load_page(module_path: str, func_name: str):
    key = f"{module_path}.{func_name}"
    if key not in _cache:
        import importlib
        mod = importlib.import_module(module_path)
        _cache[key] = getattr(mod, func_name)
    return _cache[key]


def build_app():
    demo = gr.Blocks(title="CrabCut 螃蟹快剪", theme=gr.themes.Soft())

    with demo:
        gr.Navbar(visible=True, main_page_name="🦀 CrabCut")

        gr.Markdown("# 🦀 CrabCut 螃蟹快剪")
        gr.Markdown("### 请选择语言 / Select Language")
        gr.Markdown("[🇨🇳 中文版](/zh-downloader) | [🇺🇸 English](/en-downloader)")

        gr.Markdown("---")
        gr.Markdown("### 功能列表 / Features")

        page_links_zh = []
        page_links_en = []
        for i, (page_id, icon, module_path, func_name) in enumerate(PAGES):
            zh_name = translate_text(f"nav.{page_id}", "zh")
            en_name = translate_text(f"nav.{page_id}", "en")
            page_links_zh.append(f"[{icon} {zh_name}](/zh-{page_id})")
            page_links_en.append(f"[{icon} {en_name}](/en-{page_id})")

        half = (len(page_links_zh) + 1) // 2
        gr.Markdown("**中文版 / Chinese:**")
        gr.Markdown(" | ".join(page_links_zh[:half]))
        gr.Markdown(" | ".join(page_links_zh[half:]))

        gr.Markdown("**English:**")
        gr.Markdown(" | ".join(page_links_en[:half]))
        gr.Markdown(" | ".join(page_links_en[half:]))

    for lang in ["zh", "en"]:
        for page_id, icon, module_path, func_name in PAGES:
            page_fn = _load_page(module_path, func_name)
            route_title = f"{icon} {translate_text(f'nav.{page_id}', lang)}"
            with demo.route(route_title, f"{lang}-{page_id}"):
                gr.Markdown(f"## {icon} {translate_text(f'nav.{page_id}', lang)}")

                other_lang = "en" if lang == "zh" else "zh"
                other_lang_name = "English" if lang == "zh" else "中文"
                gr.Markdown(f"[🌐 {other_lang_name}](/{other_lang}-{page_id})")

                gr.Markdown("---")
                page_fn(lang)

    return demo


if __name__ == "__main__":
    logger.info("\n\n\n\nCrabCut 螃蟹快剪 启动中...")
    app = build_app()
    logger.success("应用启动成功")
    app.launch()
