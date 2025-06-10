# check_ngspice_format.py
# -*- coding: utf-8 -*-

"""
獨立驗證腳本：
此腳本的唯一目的，是執行一次最簡單的 Ngspice 模擬，
並將其最原始、未經過濾的標準輸出 (stdout) 印出來，
讓我們可以清楚地看到其欄位分隔方式。
"""

import os
import re

# 假設此腳本在專案根目錄，而 m05 在 modules 資料夾下
try:
    from modules.m05_ngspice_runner import run_ngspice_simulation
except ImportError:
    print("錯誤：無法導入 M05 模組。請確保此腳本位於專案根目錄下。")
    exit()

# --- 腳本設定 ---
NETLIST_DIR = os.path.join(os.getcwd(), 'netlist', 'runnable')
TEST_NETLIST_NAME = "format_check.cir"
TEST_NETLIST_PATH = os.path.join(NETLIST_DIR, TEST_NETLIST_NAME)

# 定義一個最簡單的 Netlist 內容
netlist_content = """
* Format Check Netlist
V1 1 0 AC 1
R1 1 0 50
.AC DEC 10 1k 10k
.PRINT AC V(1)
.END
"""

# --- 執行流程 ---
def main():
    print("--- Ngspice 輸出格式驗證工具 ---")

    # 1. 確保目錄存在並建立測試用的 Netlist
    os.makedirs(NETLIST_DIR, exist_ok=True)
    with open(TEST_NETLIST_PATH, 'w', encoding='utf-8') as f:
        f.write(netlist_content)
    print(f"[1] 已建立測試用 Netlist: {TEST_NETLIST_PATH}")

    # 2. 呼叫 M05 執行模擬
    print("[2] 正在呼叫 M05 執行 Ngspice...")
    stdout, stderr = run_ngspice_simulation(TEST_NETLIST_NAME)

    # 3. 刪除測試檔案
    if os.path.exists(TEST_NETLIST_PATH):
        os.remove(TEST_NETLIST_PATH)
    print("[3] 已刪除測試用 Netlist。")

    # 4. 顯示結果
    if stderr:
        print("\n--- Ngspice 執行出錯 ---")
        print(stderr)
        return

    if not stdout:
        print("\n--- Ngspice 執行完畢，但沒有任何輸出 (stdout) ---")
        return

    print("\n" + "="*15 + " Ngspice 原始輸出 (stdout) " + "="*15)
    print(stdout.strip())
    print("="*52)

    # 5. 程式化分析第一行數據
    print("\n--- 格式分析 ---")
    lines = stdout.strip().splitlines()
    first_data_line = ""
    is_data_section = False
    for line in lines:
        if 'Index' in line and 'frequency' in line:
            is_data_section = True
            continue
        if is_data_section and line.strip():
            first_data_line = line.strip()
            break
    
    if first_data_line:
        print(f"找到的第一行數據為: '{first_data_line}'")
        if ',' in first_data_line:
            print("分析結果：偵測到「逗號」作為分隔符。")
        else:
            print("分析結果：未偵測到「逗號」，主要為「空白」分隔。")
        
        parts = re.split(r'\s+|,', first_data_line)
        print(f"若用「空白或逗號」分割，可將其分為 {len(parts)} 個部分。")
    else:
        print("分析結果：無法在輸出中找到有效的數據行。")

if __name__ == '__main__':
    main()