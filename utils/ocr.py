import json
from pathlib import Path
from utils.log_config import logger

_reader_cache = {}

def get_output_dir():
    from utils.converter import get_output_dir as base_get_output_dir
    return base_get_output_dir()

def get_json_path(file_path: Path) -> Path:
    output_dir = get_output_dir()
    return output_dir / f"{file_path.stem}-ocr.json"

def load_json_result(file_path: Path) -> dict:
    json_path = get_json_path(file_path)
    if json_path.exists():
        logger.info(f"加载已有结果: {json_path.as_posix()}")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_json_result(file_path: Path, data: dict):
    json_path = get_json_path(file_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"保存结果: {json_path.as_posix()}")
    return json_path

def get_reader(languages: list):
    global _reader_cache
    lang_key = tuple(sorted(languages))
    if lang_key not in _reader_cache:
        import easyocr
        logger.info(f"加载OCR模型: {languages}")
        _reader_cache[lang_key] = easyocr.Reader(languages, gpu=True, verbose=False)
        logger.success(f"OCR模型加载完成: {languages}")
    return _reader_cache[lang_key]

def ocr_single_file(file_path: str, languages: list = None) -> dict:
    if not file_path or not Path(file_path).exists():
        return {"success": False, "error": "文件不存在 / File not found"}
    
    if languages is None:
        languages = ["ch_sim", "en"]
    
    file_path = Path(file_path)
    
    cached = load_json_result(file_path)
    if cached:
        cached["from_cache"] = True
        return cached
    
    import pymupdf
    
    reader = get_reader(languages)
    suffix = file_path.suffix.lower()
    
    if suffix == ".pdf":
        logger.info(f"开始PDF OCR识别: {file_path.as_posix()}")
        doc = pymupdf.open(file_path.as_posix())
        
        all_text = []
        all_data = []
        
        for i, page in enumerate(doc):
            logger.info(f"处理第 {i+1}/{len(doc)} 页")
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            results = reader.readtext(img_bytes, detail=0, paragraph=True)
            
            page_text = results if isinstance(results, list) else [results]
            for j, text in enumerate(page_text):
                all_data.append({
                    "page": i + 1,
                    "text": text,
                    "confidence": 1.0,
                    "bbox": []
                })
            all_text.append(f"--- 第 {i+1} 页 ---\n" + "\n".join(page_text))
        
        doc.close()
        full_text = "\n\n".join(all_text)
        
        result = {
            "success": True,
            "text": full_text,
            "data": all_data,
            "file_path": file_path.as_posix(),
            "from_cache": False
        }
    else:
        logger.info(f"开始OCR识别: {file_path.as_posix()}")
        results = reader.readtext(file_path.as_posix())
        
        text_lines = []
        ocr_data = []
        
        for bbox, text, confidence in results:
            text_lines.append(text)
            ocr_data.append({
                "text": text,
                "confidence": round(confidence, 4),
                "bbox": [[int(p[0]), int(p[1])] for p in bbox]
            })
        
        full_text = "\n".join(text_lines)
        
        result = {
            "success": True,
            "text": full_text,
            "data": ocr_data,
            "file_path": file_path.as_posix(),
            "from_cache": False
        }
    
    save_json_result(file_path, result)
    logger.success(f"OCR识别成功: {len(result['data'])}条记录")
    
    return result

def ocr_batch_files(file_paths: list, languages: list = None) -> dict:
    if not file_paths:
        return {"success": False, "error": "没有输入文件 / No input files"}
    
    if languages is None:
        languages = ["ch_sim", "en"]
    
    import pymupdf
    
    reader = get_reader(languages)
    
    all_results = []
    success_count = 0
    cache_count = 0
    
    for file_path in file_paths:
        if hasattr(file_path, 'name'):
            path = file_path.name
        elif isinstance(file_path, dict):
            path = file_path.get("name")
        else:
            path = file_path
        
        if not path or not Path(path).exists():
            all_results.append({"file": path, "success": False, "error": "文件不存在"})
            continue
        
        file_path = Path(path)
        
        cached = load_json_result(file_path)
        if cached:
            all_results.append({
                "file": file_path.as_posix(),
                "success": True,
                "text": cached.get("text", ""),
                "data": cached.get("data", []),
                "from_cache": True
            })
            success_count += 1
            cache_count += 1
            continue
        
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            logger.info(f"开始PDF OCR识别: {file_path.as_posix()}")
            doc = pymupdf.open(file_path.as_posix())
            
            page_texts = []
            page_data = []
            
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                results = reader.readtext(img_bytes, detail=0, paragraph=True)
                
                page_text = results if isinstance(results, list) else [results]
                for j, text in enumerate(page_text):
                    page_data.append({
                        "page": i + 1,
                        "text": text,
                        "confidence": 1.0,
                        "bbox": []
                    })
                page_texts.append(f"--- 第 {i+1} 页 ---\n" + "\n".join(page_text))
            
            doc.close()
            full_text = "\n\n".join(page_texts)
            
            result = {
                "success": True,
                "text": full_text,
                "data": page_data,
                "file_path": file_path.as_posix(),
                "from_cache": False
            }
        else:
            logger.info(f"开始OCR识别: {file_path.as_posix()}")
            results = reader.readtext(file_path.as_posix())
            
            text_lines = []
            ocr_data = []
            
            for bbox, text, confidence in results:
                text_lines.append(text)
                ocr_data.append({
                    "text": text,
                    "confidence": round(confidence, 4),
                    "bbox": [[int(p[0]), int(p[1])] for p in bbox]
                })
            
            full_text = "\n".join(text_lines)
            
            result = {
                "success": True,
                "text": full_text,
                "data": ocr_data,
                "file_path": file_path.as_posix(),
                "from_cache": False
            }
        
        save_json_result(file_path, result)
        all_results.append({
            "file": file_path.as_posix(),
            "success": True,
            "text": result["text"],
            "data": result["data"],
            "from_cache": False
        })
        success_count += 1
    
    logger.success(f"批量OCR完成: {success_count}/{len(file_paths)} 成功, {cache_count}个已有结果")
    
    return {
        "success": True,
        "results": all_results,
        "success_count": success_count,
        "total_count": len(file_paths),
        "cache_count": cache_count
    }

__all__ = ["get_output_dir", "get_json_path", "load_json_result", "save_json_result", "ocr_single_file", "ocr_batch_files"]
