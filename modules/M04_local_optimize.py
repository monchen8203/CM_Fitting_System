# m04_local_optimize.py (完整可測試版)
# -*- coding: utf-8 -*-

import sys
import os
import logging
import time
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any

# --- 路徑修正 ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 導入相依模組 ---
try:
    from modules.m05_ngspice_runner import run_ngspice_simulation
    from modules.m06_netlist_generator import generate_netlist
except ImportError:
    # 在獨立測試模式下，這些模組可能不存在，但我們會在 __main__ 中繞過它們
    pass

# --- 全域設定 (使用 pathlib) ---
PROJECT_ROOT = Path(project_root)
LOG_DIR = PROJECT_ROOT / 'logs'
OUTPUT_DIR = PROJECT_ROOT / 'output'
RESULTS_DIR = PROJECT_ROOT / 'results'
FIGURE_DIR = PROJECT_ROOT / 'figure'

# --- 日誌設定 ---
def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    # 檢查是否已有 handler，避免重複設定
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - (%(module)s) - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_DIR / 'm04_local_optimize.log', mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout) # 將日誌同時輸出到控制台
        ]
    )
setup_logging()

# --- 標準解析器 ---
def parse_full_output(stdout: str) -> Optional[np.ndarray]:
    if not stdout: return None
    lines = stdout.strip().split('\n')
    data = []
    try:
        start_index = next(i for i, line in enumerate(lines) if 'Values' in line) + 1
    except StopIteration:
        logging.error("在 Ngspice 輸出中找不到 'Values' 標頭，無法解析。")
        return None

    for line in lines[start_index:]:
        line = line.strip()
        if not line or 'Total analysis time' in line: break
        try:
            freq_str, complex_val_str = line.split(maxsplit=1)
            real_str, imag_str = complex_val_str.split(',')
            data.append([float(freq_str), float(real_str), float(imag_str)])
        except (ValueError, IndexError): continue
            
    return np.array(data) if data else None

# --- Callback 處理類別 ---
class OptimizationCallback:
    def __init__(self, param_names: List[str], measured_data: pd.DataFrame, mode: str = 'CM'):
        self.param_names_with_headers = ['iteration', 'error'] + param_names
        self.param_names_only = param_names
        self.measured_z = measured_data[f'Z_{mode}'].values
        self.freq_points = measured_data['Frequency_Hz'].values
        self.iteration = 0
        self.start_time = time.time()
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        RESULTS_DIR.mkdir(exist_ok=True)
        self.csv_path = RESULTS_DIR / f'history_params_local_{timestamp}.csv'
        self.npz_path = RESULTS_DIR / f'history_curves_local_{timestamp}.npz'
        
        pd.DataFrame(columns=self.param_names_with_headers).to_csv(self.csv_path, index=False)
        self.curves_data = {}
        logging.info(f"Callback 初始化完成。歷史將儲存至 'results/' 資料夾。")

    def objective_log_scale(self, log_params: np.ndarray) -> float:
        params = 10**log_params
        param_dict = dict(zip(self.param_names_only, params))
        
        netlist_path = generate_netlist(param_dict=param_dict)
        stdout, _ = run_ngspice_simulation(netlist_path)
        if not stdout: return 1e10

        sim_data = parse_full_output(stdout)
        if sim_data is None: return 1e10

        sim_freq = sim_data[:, 0]
        sim_z_complex = sim_data[:, 1] + 1j * sim_data[:, 2]
        
        interp_func_real = interp1d(sim_freq, sim_z_complex.real, bounds_error=False, fill_value="extrapolate")
        interp_func_imag = interp1d(sim_freq, sim_z_complex.imag, bounds_error=False, fill_value="extrapolate")
        aligned_sim_real = interp_func_real(self.freq_points)
        aligned_sim_imag = interp_func_imag(self.freq_points)
        aligned_sim_z = np.abs(aligned_sim_real + 1j * aligned_sim_imag)
        
        self.last_curve = sim_data
        error = np.sqrt(np.mean((np.log10(aligned_sim_z) - np.log10(self.measured_z))**2))
        return error

    def callback(self, xk: np.ndarray):
        current_error = self.objective_log_scale(xk)
        real_params = 10**xk
        
        row = pd.DataFrame([[self.iteration, current_error] + list(real_params)], columns=self.param_names_with_headers)
        row.to_csv(self.csv_path, mode='a', header=False, index=False)
        
        self.curves_data[f'iter_{self.iteration}'] = self.last_curve
        
        # 不在 callback 中 print，改由 minimize 的 disp 選項顯示
        self.iteration += 1

    def save_and_close(self):
        np.savez_compressed(self.npz_path, **self.curves_data)
        logging.info("NPZ 檔案已儲存。歷史紀錄儲存完畢。")

# --- 主功能函式 ---
def local_optimization_log_scale(initial_guess: Dict[str, float], mode: str = 'CM', maxiter: int = 500) -> Optional[Dict[str, float]]:
    logging.info(f"--- 開始 {mode} 模式局部優化 (Log Scale) ---")
    
    measured_data_path = OUTPUT_DIR / 'm01_interpolated_data.csv'
    try:
        measured_data = pd.read_csv(measured_data_path)
    except FileNotFoundError:
        logging.error(f"找不到量測數據檔案: {measured_data_path}")
        return None
    # 為了與 M03 的歷史紀錄格式統一，我們使用相同的欄位名
    if 'Impedance' in measured_data.columns:
        measured_data = measured_data.rename(columns={'Impedance': f'Z_{mode}', 'Frequency': 'Frequency_Hz'})

    param_names = list(initial_guess.keys())
    log_initial_guess = np.log10(np.array(list(initial_guess.values())))
    
    callback_handler = OptimizationCallback(param_names, measured_data, mode)
    
    logging.info(f"開始執行 SLSQP... Max iterations: {maxiter}")
    start_t = time.time()

    result = minimize(
        fun=callback_handler.objective_log_scale,
        x0=log_initial_guess,
        method='SLSQP',
        options={'maxiter': maxiter, 'disp': True, 'ftol': 1e-6},
        callback=callback_handler.callback
    )

    callback_handler.save_and_close()
    
    end_t = time.time()
    logging.info(f"局部優化完成，耗時: {end_t - start_t:.2f} 秒")

    if result.success:
        final_params = dict(zip(param_names, 10**result.x))
        logging.info(f"成功找到解。最終誤差: {result.fun:.6f}")
        logging.info(f"最佳化參數: {final_params}")
        return final_params
    else:
        logging.error(f"局部優化未成功收斂。Message: {result.message}")
        return None

# --- 主程式 (if __name__ == '__main__') ---
if __name__ == '__main__':
    logging.info("="*50)
    logging.info("=== 執行 M04 模組 (Local Optimize) 獨立測試 ===")
    logging.info("="*50)

    # 1. 準備示範環境
    R_true, L_true, C_true = 50.0, 2.2e-6, 4.7e-12
    true_params = {'R1': R_true, 'L1': L_true, 'C1': C_true}
    logging.info(f"示範目標：真實參數為 {true_params}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    measured_data_path = OUTPUT_DIR / 'm01_interpolated_data.csv'
    freq_points = np.logspace(6, 9, 401)
    w = 2 * np.pi * freq_points
    Z_ideal_complex = 1 / (1/R_true + 1j*(w*C_true - 1/(w*L_true)))
    Z_ideal_mag = np.abs(Z_ideal_complex)
    noise = 1 + np.random.normal(0, 0.05, size=freq_points.shape)
    pd.DataFrame({'Frequency_Hz': freq_points, 'Z_CM': Z_ideal_mag * noise}).to_csv(measured_data_path, index=False)
    logging.info(f"已生成示範用的量測數據: {measured_data_path}")

    # 2. 建立示範用的 Callback 類別 (繞過 M05/M06)
    class DemoOptimizationCallback(OptimizationCallback):
        def objective_log_scale(self, log_params: np.ndarray) -> float:
            R, L, C = 10**log_params
            w = 2 * np.pi * self.freq_points
            sim_z_complex = 1 / (1/R + 1j*(w*C - 1/(w*L)))
            sim_z_mag = np.abs(sim_z_complex)
            self.last_curve = np.vstack([self.freq_points, sim_z_complex.real, sim_z_complex.imag]).T
            error = np.sqrt(np.mean((np.log10(sim_z_mag) - np.log10(self.measured_z))**2))
            return error

    # 3. 執行局部優化
    initial_guess = {'R1': 40.0, 'L1': 3.0e-6, 'C1': 4.0e-12}
    logging.info(f"優化起始點：初始猜測為 {initial_guess}")

    measured_data = pd.read_csv(measured_data_path)
    param_names = list(initial_guess.keys())
    demo_callback_handler = DemoOptimizationCallback(param_names, measured_data, mode='CM')
    log_initial_guess = np.log10(np.array(list(initial_guess.values())))
    
    result = minimize(
        fun=demo_callback_handler.objective_log_scale,
        x0=log_initial_guess,
        method='SLSQP',
        options={'maxiter': 100, 'disp': True},
        callback=demo_callback_handler.callback
    )
    
    demo_callback_handler.save_and_close()

    # 4. 輸出結果
    if result.success:
        final_params = dict(zip(param_names, 10**result.x))
        logging.info("="*50)
        logging.info("=== 獨立測試執行成功！ ===")
        logging.info(f"最終誤差: {result.fun:.6f}")
        logging.info(f"找到的參數: {final_params}")
        logging.info(f"真實的參數: {true_params}")
        logging.info(f"歷史紀錄檔案已儲存至 '{RESULTS_DIR}' 資料夾。")
    else:
        logging.error("局部優化在示範模式下執行失敗。")