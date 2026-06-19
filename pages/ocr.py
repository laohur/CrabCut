import gradio as gr
import json
from pathlib import Path
from utils.ocr import get_output_dir, get_json_path, ocr_single_file, ocr_batch_files
from utils.i18n import translate_text

def create_ocr_page(lang: str = "zh"):
    with gr.Column():
        gr.Markdown("#### " + ("OCR文字识别" if lang == 'zh' else "OCR Text Recognition"))
        
        with gr.Row():
            with gr.Column(scale=1):
                ocr_input = gr.File(
                    label="选择图片或PDF（支持多选）" if lang == 'zh' else "Select Image or PDF (Multiple)",
                    file_types=[".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".pdf"],
                    file_count="multiple"
                )
                ocr_lang = gr.CheckboxGroup(
                    choices=[
                        ("中文简体" if lang == 'zh' else "Chinese Simplified", "ch_sim"),
                        ("中文繁体" if lang == 'zh' else "Chinese Traditional", "ch_tra"),
                        ("英文" if lang == 'zh' else "English", "en"),
                        ("日文" if lang == 'zh' else "Japanese", "ja"),
                        ("韩文" if lang == 'zh' else "Korean", "ko"),
                    ],
                    value=["ch_sim", "en"],
                    label="识别语言" if lang == 'zh' else "Languages"
                )
                with gr.Row():
                    output_json = gr.Checkbox(value=True, label="输出JSON" if lang == 'zh' else "Output JSON")
                    output_txt = gr.Checkbox(value=True, label="输出TXT" if lang == 'zh' else "Output TXT")
                ocr_btn = gr.Button("📝 " + ("开始识别" if lang == 'zh' else "Start OCR"), variant="primary")
                ocr_status = gr.Textbox(label="状态" if lang == 'zh' else "Status", interactive=False)
            
            with gr.Column(scale=1):
                ocr_output = gr.Textbox(
                    label="识别结果" if lang == 'zh' else "OCR Result",
                    lines=20,
                    interactive=False
                )
                output_files = gr.File(label="输出文件" if lang == 'zh' else "Output Files")
        
        last_result = gr.State(None)
        
        def do_ocr(files, langs, out_json, out_txt):
            if not files:
                return "❌ 请选择文件 / Please select files", "", None, None
            
            langs = list(langs) if langs else ["ch_sim", "en"]
            
            if len(files) == 1:
                file = files[0]
                file_path = Path(file.name)
                
                result = ocr_single_file(file.name, langs)
                
                if not result["success"]:
                    return f"❌ {result['error']}", "", None, None
                
                cache_mark = " (已有)" if result.get("from_cache") else ""
                status = f"✅ 识别成功{cache_mark}: {len(result['data'])}条记录"
                
                output_file_list = []
                if out_json:
                    output_file_list.append(get_json_path(file_path).as_posix())
                if out_txt:
                    txt_path = get_output_dir() / f"{file_path.stem}-ocr.txt"
                    txt_path.write_text(result["text"], encoding="utf-8")
                    output_file_list.append(txt_path.as_posix())
                
                return status, result["text"], output_file_list if output_file_list else None, result
            
            result = ocr_batch_files(files, langs)
            
            if not result["success"]:
                return f"❌ {result['error']}", "", None, None
            
            status_lines = [
                f"✅ 批量识别完成: {result['success_count']}/{result['total_count']} 成功",
                f"📦 已有结果: {result['cache_count']}"
            ]
            
            all_texts = []
            for r in result["results"]:
                if r["success"]:
                    cache_mark = " (已有)" if r.get("from_cache") else ""
                    status_lines.append(f"  ✅ {Path(r['file']).name}: {len(r.get('data', []))}条{cache_mark}")
                    all_texts.append(f"=== {Path(r['file']).name} ===\n{r['text']}")
            
            first_chars = "".join(Path(r['file']).stem[0] for r in result["results"] if r["success"])[:10]
            output_name = f"{first_chars}-ocr"
            
            output_file_list = []
            if out_txt:
                txt_path = get_output_dir() / f"{output_name}.txt"
                txt_path.write_text("\n\n".join(all_texts), encoding="utf-8")
                output_file_list.append(txt_path.as_posix())
            
            if out_json:
                json_path = get_output_dir() / f"{output_name}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result["results"], f, ensure_ascii=False, indent=2)
                output_file_list.append(json_path.as_posix())
            
            return "\n".join(status_lines), "\n\n".join(all_texts), output_file_list if output_file_list else None, result
        
        ocr_btn.click(do_ocr, inputs=[ocr_input, ocr_lang, output_json, output_txt], outputs=[ocr_status, ocr_output, output_files, last_result])
