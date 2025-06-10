# manual_debug.py
# -*- coding: utf-8 -*-

"""
手動除錯腳本：
此腳本只執行一次完整的流程，方便我們查看每一步的詳細輸出。
M06 (產生Netlist) -> M05 (執行模擬) -> 解析結果
"""

import os
import io
import numpy as np
import pandas as pd
from typing import Optional

# 導入我們需要測試的模組
try:
    from modules.m06_netlist_generator import generate_netlist
    from modules.m05_ngspice_runner import run_ngspice_simulation
except ImportError as e:
    print(f"錯誤：無法導入模組。請確保此腳本位於專案根目錄，且 m05, m06 在 modules 資料夾下。")
    print(f"詳細錯誤: {e}")
    exit()

# 我們從 M02/M03 複製一份解析函式過來，以便單獨測試
def parse_ngspice_output(stdout: str) -> Optional[pd.DataFrame]:
    """從 Ngspice 的標準輸出中解析出數據。"""
    if not stdout or not isinstance(stdout, str):
        return None
    try:
        lines = stdout.splitlines()
        data_start_index = next((i for i, line in enumerate(lines) if 'Index' in line and 'frequency' in line), -1)
        if data_start_index == -1:
            print(" -> [解析器] 錯誤：在 stdout 中找不到數據起始行 'Index'。")
            return None
            
        data_block = "\n".join(lines[data_start_index + 1:])
        df = pd.read_csv(io.StringIO(data_block), delim_whitespace=True)
        # 假設 .PRINT 指令的輸出格式
        df.columns = ['Index', 'Frequency', 'V_real', 'V_imag']
        df['Impedance'] = np.sqrt(df['V_real']**2 + df['V_imag']**2)
        return df[['Frequency', 'Impedance']]
    except Exception as e:
        print(f" -> [解析器] 錯誤：解析期間發生未知問題: {e}")
        return None

# --- 手動執行流程 ---
if __name__ == '__main__':
    print("--- 開始手動除錯流程 ---")

    # 1. 設定要測試的參數 (我們從您的日誌中挑一組)
    test_params = {
        'R1': '4.0728e+01', 
        'L1': '3.2454e-06', 
        'C1': '5.5526e-10'
    }
    template_file = 'cm_template.cir'
    output_file = 'manual_test.cir'
    
    print(f"\n[步驟 1/4] 準備使用 M06 產生 Netlist...")
    print(f"  - 範本: {template_file}")
    print(f"  - 參數: {test_params}")
    
    # 2. 呼叫 M06
    success = generate_netlist(template_file, output_file, test_params)
    if not success:
        print("  -> M06 執行失敗！請檢查 netlist/templates/ 目錄下是否有 cm_template.cir。")
        exit()
    print(f"  -> M06 執行成功！已產生檔案: netlist/runnable/{output_file}")
    
    # 3. 呼叫 M05
    print(f"\n[步驟 2/4] 準備使用 M05 執行 Ngspice 模擬...")
    stdout_raw, stderr_raw = run_ngspice_simulation(output_file)
    print("  -> M05 執行完畢。")

    # 4. 顯示最原始的輸出結果 (這是最重要的部分)
    print("\n[步驟 3/4] 顯示 Ngspice 的原始輸出...")
    print("\n" + "="*20 + " RAW STDOUT " + "="*20)
    print(stdout_raw)
    print("="*52)

    print("\n" + "="*20 + " RAW STDERR " + "="*20)
    print(stderr_raw)
    print("="*52)

    # 5. 嘗試解析結果
    print("\n[步驟 4/4] 嘗試解析 STDOUT...")
    parsed_df = parse_ngspice_output(stdout_raw)
    
    if parsed_df is not None:
        print("  -> 解析成功！預覽解析後的數據：")
        print(parsed_df.head())
    else:
        print("  -> 解析失敗！")
        
    print("\n--- 手動除錯流程結束 ---")
