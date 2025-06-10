# m03_global_search.py (字型終極修正版)
# -*- coding: utf-8 -*-

import os
import logging
import re
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.optimize import differential_evolution
from typing import Optional, List, Dict, Tuple, Any

try:
    from m06_netlist_generator import generate_netlist
    from m05_ngspice_runner import run_ngspice_simulation
except ImportError as e:
    print(f"錯誤：無法導入相依模組。請確保 m06, m05 模組與此腳本在同一個資料夾下。 {e}")
    exit()

# --- 全域設定 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
FIGURE_DIR = os.path.join(BASE_DIR, 'figure')
NETLIST_DIR = os.path.join(BASE_DIR, 'netlist')
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'NotoSansCJKtc-Regular.otf')

# --- 日誌設定 ---
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    handler = logging.FileHandler(os.path.join(LOG_DIR, 'm03_global_search.log'), mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logging()

# --- 【修改】字型函式，不再設定全域變數，而是直接回傳字型物件 ---
def get_chinese_font_prop() -> Optional[fm.FontProperties]:
    """取得專案內的中文字型物件"""
    if os.path.exists(FONT_PATH):
        logger.info(f"成功找到專案字型檔: {FONT_PATH}")
        return fm.FontProperties(fname=FONT_PATH)
    else:
        # 在控制台印出明確的錯誤，因為這是執行此腳本的關鍵步驟
        print(f"\n*** 警告：找不到必要的字型檔！***")
        print(f"請確認 '{FONT_PATH}' 這個檔案存在。")
        logger.warning(f"在指定路徑找不到字型檔: {FONT_PATH}")
        return None

# --- 輔助函式與核心功能 (維持不變) ---
def parse_ngspice_output(stdout: str) -> Optional[pd.DataFrame]:
    if not stdout or not isinstance(stdout, str): return None
    try:
        lines = stdout.splitlines()
        data_lines = []
        is_data_section = False
        for line in lines:
            if 'Index' in line and 'frequency' in line:
                is_data_section = True
                continue
            if is_data_section and line.strip() and (line.strip()[0].isdigit() or line.strip()[0] == '-'):
                line_no_comma = line.replace(',', ' ')
                parts = line_no_comma.split()
                if len(parts) == 4: data_lines.append(parts)
        if not data_lines: return None
        df = pd.DataFrame(data_lines, columns=['Index', 'Frequency', 'V_real', 'V_imag'])
        df = df.astype({'Frequency': float, 'V_real': float, 'V_imag': float})
        df['Impedance'] = np.sqrt(df['V_real']**2 + df['V_imag']**2)
        return df[['Frequency', 'Impedance']]
    except Exception as e:
        logger.error(f"Ngspice 資料解析過程中發生異常: {e}", exc_info=True)
        return None

best_error_so_far = float('inf')
total_evaluations = 0
def objective_function(params: List[float], *args) -> float:
    global best_error_so_far, total_evaluations
    param_names, template_filename, freq_axis, baseline_z, mode = args
    current_params = {name: value for name, value in zip(param_names, params)}
    log_str = ", ".join([f"{k}={v:.4e}" for k, v in current_params.items()])
    netlist_name = f"temp_optim_{mode}_{int(time.time()*1000)}.cir"
    params_for_netlist = {k: str(v) for k, v in current_params.items()}
    if not generate_netlist(template_filename, netlist_name, params_for_netlist): return 1e10
    stdout, stderr = run_ngspice_simulation(netlist_name)
    runnable_netlist_path = os.path.join(NETLIST_DIR, 'runnable', netlist_name)
    if os.path.exists(runnable_netlist_path): os.remove(runnable_netlist_path)
    if stderr: return 1e10
    if not stdout: return 1e10
    sim_df = parse_ngspice_output(stdout)
    if sim_df is None: return 1e10
    interp_z = np.interp(freq_axis, sim_df['Frequency'], sim_df['Impedance'])
    error = np.sqrt(np.mean((interp_z - baseline_z)**2))
    total_evaluations += 1
    if error < best_error_so_far:
        best_error_so_far = error
        logger.info(f"[Eval: {total_evaluations}] New best solution! Error={error:.4f}, Params=[{log_str}]")
    return error

# --- 主流程 ---
def run_global_search(mode: str, param_bounds: Dict[str, Tuple[float, float]], template_filename: str, max_iterations: int = 100):
    global best_error_so_far, total_evaluations
    best_error_so_far = float('inf')
    total_evaluations = 0
    logger.info(f"========== 開始 {mode} 模式全域搜尋最佳化 ==========")
    logger.info(f"參數邊界: {param_bounds}")
    baseline_data_path = os.path.join(OUTPUT_DIR, 'm01_interpolated_data.csv')
    try:
        baseline_df = pd.read_csv(baseline_data_path)
        freq_axis = baseline_df['Frequency_Hz'].values
        baseline_z = baseline_df[f'Z_{mode}'].values
        logger.info("成功讀取 M01 基準資料。")
    except Exception as e:
        logger.critical(f"無法讀取 M01 基準資料，分析中止。錯誤: {e}")
        return
    param_names = list(param_bounds.keys())
    bounds = list(param_bounds.values())
    args_for_optimizer = (param_names, os.path.join(NETLIST_DIR, 'templates', template_filename), freq_axis, baseline_z, mode)
    iteration_counter = 0
    def progress_callback(xk, convergence):
        nonlocal iteration_counter
        iteration_counter += 1
        print(f"  -> 進度: [迭代 {iteration_counter} / {max_iterations}]，目前收斂值: {convergence:.6f}", end='\r')
    logger.info("Differential Evolution 演算法啟動...")
    result = differential_evolution(objective_function, bounds, args=args_for_optimizer, strategy='best1bin', maxiter=max_iterations, popsize=15, tol=0.01, mutation=(0.5, 1), recombination=0.7, disp=False, callback=progress_callback)
    print("\n最佳化程序完成。")

    logger.info(f"========== {mode} 模式最佳化完成 ==========")
    final_params_vals = result.x
    final_error = result.fun
    final_params_dict = {name: value for name, value in zip(param_names, final_params_vals)}
    param_str = ", ".join([f"{name}={val:.4e}" for name, val in final_params_dict.items()])
    logger.info(f"最終最佳化結果 - Error: {final_error:.4f}")
    logger.info(f"最終最佳化參數: [{param_str}]")

    logger.info("正在產生最終結果比較圖...")
    final_params_for_netlist = {k: str(v) for k, v in final_params_dict.items()}
    final_netlist_name = f"final_result_{mode}.cir"
    generate_netlist(template_filename, final_netlist_name, final_params_for_netlist)
    
    stdout, _ = run_ngspice_simulation(final_netlist_name)
    if stdout:
        final_sim_df = parse_ngspice_output(stdout)
        if final_sim_df is not None:
            # --- 【修改】繪圖區塊 ---
            # 1. 取得字型物件
            font_prop = get_chinese_font_prop()
            # 2. 如果找不到字型，後續的 fontproperties 參數會是 None，使用預設字型
            
            plt.style.use('seaborn-v0_8-whitegrid')
            plt.figure(figsize=(12, 7))
            plt.plot(freq_axis / 1e6, baseline_z, label='量測目標 (M01)', color='red', linestyle='--')
            plt.plot(final_sim_df['Frequency'] / 1e6, final_sim_df['Impedance'], label=f'最佳化模擬結果 (Error={final_error:.2f})', color='blue')
            plt.xscale('log')
            plt.yscale('log')
            
            # 3. 在每一個需要顯示中文的地方，明確傳入字型物件
            plt.xlabel('頻率 (MHz)', fontproperties=font_prop)
            plt.ylabel('阻抗 (Ohm)', fontproperties=font_prop)
            plt.title(f'{mode} 模式 - 全域搜尋最佳化結果比較', fontproperties=font_prop)
            plt.legend(prop=font_prop)
            
            os.makedirs(FIGURE_DIR, exist_ok=True)
            chart_path = os.path.join(FIGURE_DIR, f'm03_global_search_result_{mode}.png')
            plt.savefig(chart_path)
            plt.close()
            logger.info(f"比較圖已儲存至: {chart_path}")
            
# --- 主程式 (維持不變) ---
if __name__ == '__main__':
    # ... (此區塊維持不變) ...
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(NETLIST_DIR, 'templates'), exist_ok=True)
    freq = np.logspace(6, 9.47, 401)
    z_cm = 20 * np.log10(freq / 1e6) + 50 + np.random.randn(401) * 0.5 
    pd.DataFrame({'Frequency_Hz': freq, 'Z_CM': z_cm}).to_csv(os.path.join(OUTPUT_DIR, 'm01_interpolated_data.csv'), index=False)
    cm_template = """
* CM Template
V1 1 0 AC 1
R1 1 2 ${R1}
L1 2 3 ${L1}
C1 3 0 ${C1}
.AC DEC 100 1e6 3e9
.PRINT AC V(3)
.END
"""
    with open(os.path.join(NETLIST_DIR, 'templates', 'cm_template.cir'), 'w') as f:
        f.write(cm_template)
    cm_param_bounds = {'R1': (10.0, 100.0), 'L1': (1e-7, 1e-5), 'C1': (1e-11, 1e-9)}
    run_global_search(mode='CM', param_bounds=cm_param_bounds, template_filename='cm_template.cir', max_iterations=50)
    print(f"分析完成，請查看 '{LOG_DIR}/m03_global_search.log' 和 '{FIGURE_DIR}' 資料夾中的圖檔。")
