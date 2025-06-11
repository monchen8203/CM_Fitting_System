# m03_global_search.py (多核心修正版)
# -*- coding: utf-8 -*-

import sys
import os

# --- 路徑修正 (維持不變) ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.m06_netlist_generator import generate_netlist
from modules.m05_ngspice_runner import run_ngspice_simulation
from modules.m07_plot_results import parse_ngspice_output # 假設 M07 有此函式
# ... 其他 import 維持不變 ...
import logging
import re
import time
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime

# --- 全域設定與日誌設定 (維持不變) ---
# ... 此處省略 ...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
FIGURE_DIR = os.path.join(BASE_DIR, 'figure')
NETLIST_DIR = os.path.join(BASE_DIR, 'netlist')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
# ... setup_logging() ...
logger = logging.getLogger(__name__) # 假設 setup_logging 已被呼叫

# *** 修改 ***: 調整 Callback 類別以相容多核心
class OptimizationCallback:
    def __init__(self, param_names: List[str], measured_data: pd.DataFrame, mode: str = 'CM'):
        self.param_names_with_headers = ['iteration', 'error'] + param_names
        self.param_names_only = param_names
        self.measured_z = measured_data[f'Z_{mode}'].values
        self.freq_points = measured_data['Frequency_Hz'].values
        self.iteration = 0
        self.start_time = time.time()
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        os.makedirs(RESULTS_DIR, exist_ok=True)
        self.csv_path = os.path.join(RESULTS_DIR, f'history_params_{timestamp}.csv')
        self.npz_path = os.path.join(RESULTS_DIR, f'history_curves_{timestamp}.npz')
        
        # *** 修改 ***: 不再保持檔案開啟。建立檔案並只寫入標頭，然後立刻關閉。
        pd.DataFrame(columns=self.param_names_with_headers).to_csv(self.csv_path, index=False)
        
        self.curves_data = {}
        self.last_params = None
        self.last_error = None
        self.last_curve = None
        
        logger.info(f"Callback 初始化完成。參數歷史將儲存至: {self.csv_path}")
        logger.info(f"曲線歷史將儲存至: {self.npz_path}")

    def objective(self, params: np.ndarray) -> float:
        if self.last_params is not None and np.array_equal(params, self.last_params):
            return self.last_error

        param_dict = dict(zip(self.param_names_only, params))
        netlist_path = generate_netlist(param_dict=param_dict)

        stdout, _ = run_ngspice_simulation(netlist_path)
        if not stdout: return 1e10

        sim_data = parse_ngspice_output(stdout)
        if sim_data is None: return 1e10

        sim_z = np.abs(sim_data[:, 1] + 1j * sim_data[:, 2])
        error = np.sqrt(np.mean((np.log10(sim_z) - np.log10(self.measured_z))**2))
        
        self.last_params = np.copy(params)
        self.last_curve = sim_data
        self.last_error = error
        
        return error

    def callback(self, xk: np.ndarray, convergence: float):
        # *** 修改 ***: 每次 callback 時，以附加模式(append)開啟、寫入、然後立刻關閉檔案。
        row = pd.DataFrame([[self.iteration, self.last_error] + list(xk)], columns=self.param_names_with_headers)
        row.to_csv(self.csv_path, mode='a', header=False, index=False)
        
        self.curves_data[f'iter_{self.iteration}'] = self.last_curve
        
        elapsed_time = time.time() - self.start_time
        print(f"Iteration: {self.iteration:4d}, Error: {self.last_error:.6f}, Convergence: {convergence:.4f}, Time: {elapsed_time:.2f}s")
        
        self.iteration += 1

    def save_and_close(self):
        # *** 修改 ***: 不再需要關閉 CSV 檔案，因為它已經是關閉的。
        np.savez_compressed(self.npz_path, **self.curves_data)
        logger.info("NPZ 檔案已儲存。歷史紀錄儲存完畢。")


# --- 主功能函式 (維持不變) ---
def global_search_optimization(
    param_bounds: Dict[str, Tuple[float, float]],
    mode: str = 'CM',
    maxiter: int = 1000,
    popsize: int = 15,
    tol: float = 0.01
) -> Optional[Dict[str, float]]:
    
    # ... 此函式內部邏輯完全不變，此處省略 ...
    logger.info(f"--- 開始 {mode} 模式全域搜尋 ---")
    
    measured_data_path = os.path.join(OUTPUT_DIR, 'm01_interpolated_data.csv')
    try:
        measured_data = pd.read_csv(measured_data_path)
    except FileNotFoundError:
        logger.error(f"找不到量測數據檔案: {measured_data_path}")
        return None

    param_names = list(param_bounds.keys())
    bounds = list(param_bounds.values())

    callback_handler = OptimizationCallback(param_names, measured_data, mode)

    logger.info(f"開始執行 Differential Evolution... Max iterations: {maxiter}")
    start_t = time.time()
    
    result = differential_evolution(
        func=callback_handler.objective,
        bounds=bounds,
        strategy='best1bin',
        maxiter=maxiter,
        popsize=popsize,
        tol=tol,
        mutation=(0.5, 1),
        recombination=0.7,
        updating='deferred',
        workers=-1,
        callback=callback_handler.callback
    )

    callback_handler.save_and_close()

    end_t = time.time()
    logger.info(f"全域搜尋完成，耗時: {end_t - start_t:.2f} 秒")

    if result.success:
        logger.info(f"成功找到解。最終誤差: {result.fun:.6f}")
        final_params = dict(zip(param_names, result.x))
        logger.info(f"最佳化參數: {final_params}")
        return final_params
    else:
        logger.error(f"全域搜尋未成功收斂。Message: {result.message}")
        return None

# --- 主程式 (if __name__ == '__main__') (維持不變) ---
if __name__ == '__main__':
    # ... (示範區塊維持不變) ...
    print("M03 示範執行前的注意事項：...")
