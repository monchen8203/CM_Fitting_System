# m06_netlist_generator.py
# -*- coding: utf-8 -*-

"""
模組 M06: Netlist 產生器

功能：
1. 讀取指定的 Netlist 範本檔案。
2. 將傳入的參數字典安全地替換掉範本中的佔位符。
3. 產生一個可用於 Ngspice 執行的最終 Netlist 檔案。
4. 記錄完整的操作流程與任何可能的錯誤。
"""

import os
import logging
import string # 導入用於安全範本替換的函式庫

# --- 全域設定 ---
# 定義專案根目錄
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# 定義相關目錄路徑
LOG_DIR = os.path.join(BASE_DIR, 'logs')
NETLIST_DIR = os.path.join(BASE_DIR, 'netlist')
TEMPLATE_DIR = os.path.join(NETLIST_DIR, 'templates') # 存放範本
RUNNABLE_DIR = os.path.join(NETLIST_DIR, 'runnable')  # 存放可執行的 netlist

# 定義日誌檔案路徑
LOG_FILE_PATH = os.path.join(LOG_DIR, 'm06_netlist_generator.log')

# --- 日誌設定 ---
def setup_logging():
    """設定日誌記錄器"""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()
        
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode='w', encoding='utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - (%(module)s) - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# --- 核心功能 ---
def generate_netlist(template_filename: str, output_filename: str, parameters: dict) -> bool:
    """
    根據範本和參數產生 Netlist 檔案。

    Args:
        template_filename (str): 位於 'netlist/templates/' 目錄下的範本檔案名稱。
        output_filename (str): 欲儲存於 'netlist/runnable/' 目錄下的輸出檔案名稱。
        parameters (dict): 包含要替換的參數的字典。

    Returns:
        bool: 如果成功產生檔案則返回 True，否則返回 False。
    """
    logger.info(f"M06 模組啟動：準備從範本 '{template_filename}' 產生 Netlist '{output_filename}'...")

    template_path = os.path.join(TEMPLATE_DIR, template_filename)
    output_path = os.path.join(RUNNABLE_DIR, output_filename)

    # 確保目錄存在
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    os.makedirs(RUNNABLE_DIR, exist_ok=True)

    try:
        # 1. 讀取範本檔案內容
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        logger.info(f"成功讀取範本檔案: {template_path}")

        # 2. 建立安全範本物件
        template = string.Template(template_content)

        # 3. 進行參數替換
        # 使用 substitute()，如果參數缺失會直接拋出 KeyError，更為嚴謹
        final_netlist_content = template.substitute(parameters)
        logger.info("參數已成功替換至範本。")

        # 4. 寫入最終的 Netlist 檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_netlist_content)
        
        logger.info(f"成功產生可執行的 Netlist 檔案: {output_path}")
        return True

    except FileNotFoundError:
        logger.error(f"錯誤：找不到指定的範本檔案 -> {template_path}")
        return False
    except KeyError as e:
        logger.error(f"錯誤：參數字典中缺少範本所需的鍵 (Key) -> {e}")
        return False
    except Exception as e:
        logger.error(f"產生 Netlist 時發生未預期的錯誤: {e}", exc_info=True)
        return False

# --- 主程式 (用於示範與測試) ---
if __name__ == '__main__':
    print("正在執行 M06 模組 (Netlist Generator) 示範...")

    # 1. 建立一個範例用的 Netlist 範本檔案
    sample_template_name = 'sample_rlc_template.cir'
    sample_template_content = """
* RLC Bandpass Filter Analysis
* 標題: ${title}

V1 1 0 AC 1V SIN(0 1V 1k)

R1 1 2 ${R1_val}
L1 2 3 ${L1_val}
C1 3 0 ${C1_val}

.AC DEC 100 1k 100Meg
.PRINT AC REAL(V(3)) IMAG(V(3))

.END
"""
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    with open(os.path.join(TEMPLATE_DIR, sample_template_name), 'w', encoding='utf-8') as f:
        f.write(sample_template_content)
    print(f"已建立範例範本: {os.path.join(TEMPLATE_DIR, sample_template_name)}")

    # 2. 定義要填入的參數
    simulation_params = {
        'title': 'My First RLC Simulation',
        'R1_val': '50',      # 50 Ohms
        'L1_val': '1u',       # 1 micro-Henry
        'C1_val': '100p'      # 100 pico-Farads
    }
    print(f"使用的參數: {simulation_params}")

    # 3. 呼叫核心功能來產生 Netlist
    output_netlist_name = 'run01_rlc.cir'
    success = generate_netlist(
        template_filename=sample_template_name,
        output_filename=output_netlist_name,
        parameters=simulation_params
    )

    if success:
        print("\n處理完成！")
        print(f"  -> 最終 Netlist 已儲存至: {os.path.join(RUNNABLE_DIR, output_netlist_name)}")
        print(f"  -> 詳細日誌已寫入至: {LOG_FILE_PATH}")
    else:
        print("\n處理失敗，請檢查日誌檔案獲取詳細資訊。")
        print(f"  -> 日誌檔案路徑: {LOG_FILE_PATH}")