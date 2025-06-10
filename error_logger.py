# error_logger.py
# 自動記錄錯誤至 logs/error_trace/{模組名稱}_YYYYMMDD_HHMMSS.log

import traceback
import os
from datetime import datetime
from pathlib import Path

def log_exception(module_name: str, error: Exception):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs/error_trace")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{module_name}_{now}.log"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"[{now}] Module: {module_name}\n")
        f.write(f"Error Type: {type(error).__name__}\n")
        f.write(f"Message: {str(error)}\n\n")
        f.write("Traceback:\n")
        f.write("".join(traceback.format_exception(type(error), error, error.__traceback__)))

    print(f"🚨 已記錄錯誤至：{log_file}")

# 範例用法（模組內部包裝）
if __name__ == "__main__":
    try:
        # 模擬錯誤
        1 / 0
    except Exception as e:
        log_exception("M99_debug_demo", e)
