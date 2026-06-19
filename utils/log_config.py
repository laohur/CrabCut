import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "outputs"

def setup_logger():
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = OUTPUT_DIR / today
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / f"crabcut_{today}.log"
    
    logger.remove()
    
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG"
    )
    
    logger.add(
        log_file.as_posix(),
        rotation="1 day",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )

setup_logger()

def log_subprocess(cmd: list, stdout: str, stderr: str, returncode: int):
    cmd_str = " ".join(str(c) for c in cmd)
    logger.info(f"返回码: {returncode}")
    if stdout:
        logger.info(f"STDOUT:\n{stdout}")
    if stderr:
        if returncode != 0:
            logger.error(f"STDERR:\n{stderr}")
        else:
            logger.info(f"OUTPUT:\n{stderr}")

def log_cmd(cmd: list):
    cmd_str = " ".join(str(c) for c in cmd)
    logger.info(f"执行命令: {cmd_str}")

__all__ = ["logger", "log_subprocess", "log_cmd"]
