# M05_ngspice_runner.py (最終穩健版)
# -*- coding: utf-8 -*-

import os
import logging
import subprocess
import time
from typing import Optional, Tuple

# --- 全域設定 ---
NGSPICE_EXECUTABLE_PATH = r'D:\Ngspice\bin\ngspice.exe'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
NETLIST_DIR = os.path.join(BASE_DIR, 'netlist')
RUNNABLE_DIR = os.path.join(NETLIST_DIR, 'runnable')
LOG_FILE_PATH = os.path.join(LOG_DIR, 'm05_ngspice_runner.log')

# --- 日誌設定 ---
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - (%(module)s) - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logging()

# --- 核心功能 ---
def run_ngspice_simulation(netlist_filename: str, timeout_seconds: int = 60) -> Tuple[Optional[str], Optional[str]]:
    logger.info(f"M05 模組啟動：準備執行 Netlist 檔案 '{netlist_filename}'...")

    if not os.path.exists(NGSPICE_EXECUTABLE_PATH):
        error_msg = f"致命錯誤：找不到 Ngspice 執行檔 -> {NGSPICE_EXECUTABLE_PATH}"
        logger.critical(error_msg)
        return (None, error_msg)

    netlist_path = os.path.join(RUNNABLE_DIR, netlist_filename)
    if not os.path.exists(netlist_path):
        error_msg = f"錯誤：找不到指定的 Netlist 檔案 -> {netlist_path}"
        logger.error(error_msg)
        return (None, error_msg)

    # 【修改】定義一個唯一的暫存輸出檔路徑
    temp_output_filename = f"{netlist_filename}.log"
    temp_output_path = os.path.join(RUNNABLE_DIR, temp_output_filename)

    # 【修改】組合新的指令，使用 -o 參數讓 Ngspice 直接輸出到檔案
    command = [NGSPICE_EXECUTABLE_PATH, "-b", "-o", temp_output_path, netlist_path]
    logger.info(f"組合指令: {' '.join(command)}")

    stdout_content = None
    try:
        # 【修改】不再需要捕捉 stdout，因為結果已導入檔案
        result = subprocess.run(
            command,
            capture_output=True, # 仍然捕捉 stderr
            text=True,
            timeout=timeout_seconds,
            encoding='utf-8',
            check=False
        )
        
        # 模擬結束後，檢查 stderr 是否有內容
        if result.stderr and result.stderr.strip():
            error_msg = f"Netlist '{netlist_filename}' 模擬時 Ngspice 回傳了錯誤或警告。"
            logger.warning(error_msg)
            return (None, result.stderr)
        
        # 【修改】如果模擬程序成功，從暫存檔讀取輸出內容
        if os.path.exists(temp_output_path):
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                stdout_content = f.read()
            logger.info(f"Netlist '{netlist_filename}' 模擬成功，並從暫存檔讀取結果。")
            return (stdout_content, None)
        else:
            # 雖然很少見，但如果程序成功卻沒有產生輸出檔，也視為錯誤
            error_msg = f"錯誤：Ngspice 執行完畢但未產生輸出檔 '{temp_output_filename}'。"
            logger.error(error_msg)
            return (None, error_msg)

    except subprocess.TimeoutExpired:
        error_msg = f"錯誤：模擬 '{netlist_filename}' 超過 {timeout_seconds} 秒，已強制中止。"
        logger.error(error_msg)
        return (None, error_msg)
    except Exception as e:
        error_msg = f"執行 Ngspice 時發生未預期的錯誤: {e}"
        logger.critical(error_msg, exc_info=True)
        return (None, error_msg)
    finally:
        # 【修改】無論成功失敗，最後都嘗試刪除暫存檔
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

# if __name__ == '__main__' 區塊保持不變
if __name__ == '__main__':
    try:
        from m06_netlist_generator import generate_netlist
    except ImportError:
        print("錯誤：無法導入 m06_netlist_generator。請確保 'm06_netlist_generator.py' 檔案與此腳本在同一個 'modules' 資料夾下。")
        exit()
    print("正在執行 M05 模組 (Ngspice Runner) 示範...")
    template_name = 'sample_rlc_template.cir'
    netlist_name_to_run = 'run01_for_m05_test.cir'
    params = {'title': 'M05_Test', 'R1_val': '50', 'L1_val': '1u', 'C1_val': '100p'}
    template_dir = os.path.join(BASE_DIR, 'netlist', 'templates')
    os.makedirs(template_dir, exist_ok=True)
    with open(os.path.join(template_dir, template_name), 'w') as f:
        f.write("* RLC Filter\n* Title: ${title}\nV1 1 0 AC 1V\nR1 1 2 ${R1_val}\nL1 2 3 ${L1_val}\nC1 3 0 ${C1_val}\n.AC DEC 100 1k 100Meg\n.PRINT AC V(3)\n.END")
    if not generate_netlist(template_name, netlist_name_to_run, params):
        print("錯誤：前置步驟 M06 產生 Netlist 失敗，無法繼續執行 M05。")
        exit()
    print(f"\n準備執行模擬: {netlist_name_to_run}")
    stdout_result, stderr_result = run_ngspice_simulation(netlist_filename=netlist_name_to_run, timeout_seconds=30)
    print("\n--- 模擬結果 ---")
    if stderr_result:
        print("模擬失敗或包含警告！")
        print(f"錯誤/警告訊息:\n{stderr_result}")
        if stdout_result:
            print(f"\n標準輸出 (可能不完整):\n{stdout_result}")
    elif stdout_result:
        print("模擬成功！")
        print(f"標準輸出:\n{stdout_result}")
    else:
        print("模擬未能執行。請檢查日誌檔案獲取詳細資訊。")
    print(f"\n詳細日誌已寫入至: {LOG_FILE_PATH}")
