# m02_sensitivity_analysis.py
# -*- coding: utf-8 -*-

"""
模組 M02: 敏感度分析
"""

import os
import logging
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from typing import Optional

# 導入相依的自訂模組
try:
    from m06_netlist_generator import generate_netlist
    from m05_ngspice_runner import run_ngspice_simulation
except ImportError as e:
    print(f"錯誤：無法導入相依模組。請確保 m06, m05 模組與此腳本在同一個資料夾下。 {e}")
    exit()

# --- 全域設定 ---
# 定義專案根目錄
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# 定義相關目錄路徑
LOG_DIR = os.path.join(BASE_DIR, 'logs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output') # 用於存放數據類型的輸出
FIGURE_DIR = os.path.join(BASE_DIR, 'figure') # 【修改】新增 figure 目錄用於存放圖表
DATA_DIR = os.path.join(BASE_DIR, 'data')

# --- 日誌設定 ---
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'm02_sensitivity_analysis.log'), mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logging()

# --- 輔助功能：解析 Ngspice 輸出 ---
def parse_ngspice_output(stdout: str) -> Optional[pd.DataFrame]:
    try:
        lines = stdout.splitlines()
        data_start_index = -1
        for i, line in enumerate(lines):
            if 'Index' in line and 'frequency' in line:
                data_start_index = i + 1
                break
        if data_start_index == -1:
            logger.error("在 Ngspice 輸出中找不到數據起始行 'Index'。")
            return None
        data_block = "\n".join(lines[data_start_index:])
        df = pd.read_csv(io.StringIO(data_block), delim_whitespace=True)
        df.columns = ['Index', 'Frequency', 'V_real', 'V_imag']
        df['Impedance'] = np.sqrt(df['V_real']**2 + df['V_imag']**2)
        return df[['Frequency', 'Impedance']]
    except Exception as e:
        logger.error(f"解析 Ngspice 輸出時發生錯誤: {e}", exc_info=True)
        return None

# --- 核心功能 ---
def run_sensitivity_analysis(mode: str, base_params: dict, template_filename: str):
    logger.info(f"========== 開始 {mode} 模式敏感度分析 ==========")

    baseline_data_path = os.path.join(OUTPUT_DIR, 'm01_interpolated_data.csv')
    try:
        baseline_df = pd.read_csv(baseline_data_path)
        baseline_z = baseline_df[f'Z_{mode}']
        freq_axis = baseline_df['Frequency_Hz']
        logger.info(f"成功讀取基準資料: {baseline_data_path}")
    except Exception as e:
        logger.critical(f"無法讀取 M01 基準資料 '{baseline_data_path}'，分析中止。錯誤: {e}")
        return

    sensitivities = {}
    variation_factor = 1.05

    for param, base_value in base_params.items():
        logger.info(f"--- 正在分析參數: {param} ---")
        varied_params = base_params.copy()
        try:
            varied_value = float(base_value) * variation_factor
            varied_params[param] = str(varied_value)
        except ValueError:
             logger.warning(f"參數 '{param}' 的值 '{base_value}' 非純數字，暫時跳過。")
             continue

        temp_netlist_name = f"temp_sensitivity_{mode}_{param}.cir"
        if not generate_netlist(template_filename, temp_netlist_name, varied_params):
            logger.error(f"為參數 '{param}' 產生 Netlist 失敗，跳過此參數。")
            continue
        
        stdout, stderr = run_ngspice_simulation(temp_netlist_name, timeout_seconds=30)
        if stderr or not stdout:
            logger.error(f"執行參數 '{param}' 的模擬失敗，跳過此參數。")
            continue

        sim_df = parse_ngspice_output(stdout)
        if sim_df is None:
            logger.error(f"解析參數 '{param}' 的模擬結果失敗，跳過此參數。")
            continue
            
        sim_z_interp = np.interp(freq_axis, sim_df['Frequency'], sim_df['Impedance'])
        mae = np.mean(np.abs(sim_z_interp - baseline_z))
        sensitivities[param] = mae
        logger.info(f"參數 '{param}' 的敏感度 (MAE) 為: {mae:.4f}")

    if not sensitivities:
        logger.error("沒有任何參數成功完成分析，無法產生圖表。")
        return

    try:
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False

        params_sorted = sorted(sensitivities.items(), key=lambda item: item[1], reverse=True)
        names = [item[0] for item in params_sorted]
        values = [item[1] for item in params_sorted]

        plt.figure(figsize=(10, 6))
        bars = plt.bar(names, values, color='deepskyblue')
        plt.bar_label(bars, fmt='%.4f')
        plt.xlabel('元件參數')
        plt.ylabel('敏感度指標 (平均絕對誤差)')
        plt.title(f'{mode} 模式：各元件參數對阻抗影響之敏感度分析')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # 【修改】確保 figure 目錄存在並儲存圖表
        os.makedirs(FIGURE_DIR, exist_ok=True)
        chart_path = os.path.join(FIGURE_DIR, f'm02_sensitivity_analysis_{mode}.png')
        plt.savefig(chart_path)
        plt.close()
        logger.info(f"敏感度分析圖表已儲存至: {chart_path}")
    except Exception as e:
        logger.error(f"繪製或儲存圖表時發生錯誤: {e}")

    logger.info(f"========== {mode} 模式敏感度分析完成 ==========")

# --- 主程式 (用於示範) ---
if __name__ == '__main__':
    logger.info("M02 模組以獨立模式執行...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'netlist', 'templates'), exist_ok=True)
    
    freq = np.logspace(6, 9.47, 401)
    z_cm = 20 * np.log10(freq/1e6) + 50
    z_nm = 5 * np.log10(freq/1e6) + 10
    pd.DataFrame({'Frequency_Hz': freq, 'Z_CM': z_cm, 'Z_NM': z_nm}).to_csv(
        os.path.join(OUTPUT_DIR, 'm01_interpolated_data.csv'), index=False
    )
    
    cm_base_params = {'R1': '50', 'L1': '1E-6', 'C1': '1E-10'}
    cm_template = "* CM Template\nV1 1 0 AC 1\nR1 1 2 ${R1}\nL1 2 3 ${L1}\nC1 3 0 ${C1}\n.AC DEC 100 1e6 3e9\n.PRINT AC V(3)\n.END"
    with open(os.path.join(BASE_DIR, 'netlist', 'templates', 'cm_template.cir'), 'w') as f:
        f.write(cm_template)

    nm_base_params = {'R2': '10', 'L2': '5E-7', 'C2': '2E-10'}
    nm_template = "* NM Template\nV1 1 0 AC 1\nR2 1 2 ${R2}\nL2 2 3 ${L2}\nC2 3 0 ${C2}\n.AC DEC 100 1e6 3e9\n.PRINT AC V(3)\n.END"
    with open(os.path.join(BASE_DIR, 'netlist', 'templates', 'nm_template.cir'), 'w') as f:
        f.write(nm_template)
    
    run_sensitivity_analysis(
        mode='CM',
        base_params=cm_base_params,
        template_filename='cm_template.cir'
    )
    run_sensitivity_analysis(
        mode='NM',
        base_params=nm_base_params,
        template_filename='nm_template.cir'
    )
    # 【修改】更新最終的提示訊息
    print(f"分析完成，請查看 '{LOG_DIR}/m02_sensitivity_analysis.log' 和 '{FIGURE_DIR}' 資料夾中的圖檔。")
