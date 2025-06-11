# m00_pre_check.py (路徑與風格修正版)
# -*- coding: utf-8 -*-

import os
import sys
import logging
import re
import numpy as np
from pathlib import Path

# --- 路徑修正 ---
try:
    project_root = Path(__file__).resolve().parent.parent
except NameError:
    project_root = Path(os.getcwd())
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- 全域設定 ---
BASE_DIR = project_root
DATA_DIR = BASE_DIR / 'data'
# *** 修改 ***: Tai_CM.txt 的路徑改為 data/
NETLIST_TEMPLATE_PATH = DATA_DIR / 'Tai_CM.txt'

# 需要確保存在的檔案
REQUIRED_DATA_FILES = {
    'CM_CURVE': DATA_DIR / '801CM.txt',
    'NM_CURVE': DATA_DIR / '801NM.txt',
    'CIRCUIT_TEMPLATE': NETLIST_TEMPLATE_PATH
}

# 需要確保存在的資料夾
REQUIRED_DIRS = [
    BASE_DIR / 'output',
    BASE_DIR / 'figure',
    BASE_DIR / 'results',
    BASE_DIR / 'logs',
    BASE_DIR / 'netlist',
    BASE_DIR / 'netlist' / 'templates', # 雖然樣板改到 data，但此目錄可能 M06 會用到，保留檢查
    BASE_DIR / 'netlist' / 'runnable'
]

# --- 日誌與輔助函式 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CHECK] - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def pause_and_exit(message: str):
    logging.error(message)
    input("\n... 按下 Enter 鍵以結束程式 ...")
    sys.exit(1)

# --- 核心檢查函式 ---
def _validate_data_file(file_path: Path):
    """ 驗證單一目標曲線檔案的格式與頻率範圍 """
    try:
        data = np.loadtxt(file_path)
        if data.ndim != 2 or data.shape[1] != 2:
            pause_and_exit(f"檔案 '{file_path.name}' 格式錯誤：必須是兩欄的數字資料。")
        
        freq_hz = data[:, 0]
        start_freq_mhz = freq_hz[0] / 1e6
        end_freq_mhz = freq_hz[-1] / 1e6

        if not (0 < start_freq_mhz <= 10):
            pause_and_exit(f"檔案 '{file_path.name}' 頻率範圍錯誤：起始頻率 ({start_freq_mhz:.2f} MHz) 不在 0~10 MHz 的合理範圍內。")
        
        if not (900 < end_freq_mhz <= 4000):
             pause_and_exit(f"檔案 '{file_path.name}' 頻率範圍錯誤：結束頻率 ({end_freq_mhz:.2f} MHz) 不在 900~4000 MHz 的合理範圍內。")

    except ValueError:
        pause_and_exit(f"檔案 '{file_path.name}' 格式錯誤：無法將內容解析為數字。")
    except Exception as e:
        pause_and_exit(f"讀取或驗證檔案 '{file_path.name}' 時發生未知錯誤: {e}")

def run_pre_checks():
    """
    執行所有前置檢查，包括檔案與資料夾是否存在、格式是否正確。
    """
    logging.info("--- 開始執行前置環境與檔案檢查 ---")
    
    # 1. 檢查必要檔案是否存在
    for key, file_path in REQUIRED_DATA_FILES.items():
        if not file_path.is_file():
            pause_and_exit(f"找不到必要的輸入檔案: {file_path}")
    logging.info("[OK] 所有必要的輸入檔案都存在。")

    # 2. 檢查 Netlist 樣板格式
    try:
        with open(NETLIST_TEMPLATE_PATH, 'r') as f:
            content = f.read()
            if '.SUBCKT' not in content.upper() or '.ENDS' not in content.upper():
                pause_and_exit(f"電路樣板檔案 '{NETLIST_TEMPLATE_PATH.name}' 格式不正確，缺少 '.SUBCKT' 或 '.ENDS'。")
    except Exception as e:
        pause_and_exit(f"讀取電路樣板檔案 '{NETLIST_TEMPLATE_PATH.name}' 時發生錯誤: {e}")
    logging.info(f"[OK] 電路樣板 '{NETLIST_TEMPLATE_PATH.name}' 格式基本正確。")

    # 3. 檢查目標曲線檔案的格式與頻率
    logging.info("... 正在檢查目標曲線檔案內容 ...")
    _validate_data_file(REQUIRED_DATA_FILES['CM_CURVE'])
    _validate_data_file(REQUIRED_DATA_FILES['NM_CURVE'])
    logging.info("[OK] 目標曲線檔案格式與頻率範圍檢查通過。")

    # 4. 檢查輸出資料夾
    dirs_to_create = [p for p in REQUIRED_DIRS if not p.is_dir()]
    if dirs_to_create:
        logging.warning("以下必要的輸出資料夾不存在:")
        for p in dirs_to_create: print(f" - {p}")
        
        answer = input("是否要自動建立這些資料夾？(y/n): ").lower()
        if answer == 'y':
            for p in dirs_to_create:
                p.mkdir(parents=True, exist_ok=True)
                logging.info(f"... 已建立資料夾: {p}")
        else:
            pause_and_exit("使用者取消操作，程式已終止。")
    logging.info("[OK] 所有輸出資料夾都已存在。")
    
    logging.info("--- 前置檢查完畢，一切就緒！ ---")
    return True

if __name__ == '__main__':
    run_pre_checks()
    print("\nm00_pre_check.py 模組獨立測試成功。")
    input("\n... 按下 Enter 鍵以結束 ...")
