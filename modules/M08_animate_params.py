# m08_animate_params.py (最終除錯版)
# -*- coding: utf-8 -*-

import sys
import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pathlib import Path
from typing import Optional

# --- 路徑修正 ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 全域設定 ---
PROJECT_ROOT = Path(project_root)
LOG_DIR = PROJECT_ROOT / 'logs'
OUTPUT_DIR = PROJECT_ROOT / 'output'
RESULTS_DIR = PROJECT_ROOT / 'results'
FIGURE_DIR = PROJECT_ROOT / 'figure'

# --- 日誌設定 ---
def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - (%(module)s) - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_DIR / 'm08_animate_params.log', mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
setup_logging()

# --- 主功能函式 ---
def create_animation(
    history_csv_path: Path,
    history_npz_path: Path,
    measured_data_path: Path,
    output_gif_path: Path,
    animation_step: int = 1,
    fps: int = 15
):
    logging.info("--- 開始建立最佳化過程動畫 ---")
    
    try:
        df_history = pd.read_csv(history_csv_path)
        curves_history = np.load(history_npz_path)
        df_measured = pd.read_csv(measured_data_path)
        logging.info("所有歷史紀錄與量測數據載入成功。")
    except FileNotFoundError as e:
        logging.error(f"找不到必要的檔案: {e}")
        return

    total_iterations = len(df_history)
    param_names = [col for col in df_history.columns if col not in ['iteration', 'error']]
    frame_indices = np.arange(0, total_iterations, animation_step)
    
    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[2, 1])
    ax_main = fig.add_subplot(gs[:, 0])
    ax_err = fig.add_subplot(gs[0, 1])
    ax_param = fig.add_subplot(gs[1, 1])
    
    ax_main.plot(df_measured['Frequency_Hz'], df_measured['Z_CM'], color='blue', label='Measured', lw=2)
    ax_main.set_xscale('log'); ax_main.set_yscale('log')
    ax_main.set_title('Impedance vs. Frequency', fontsize=14); ax_main.set_xlabel('Frequency (Hz)'); ax_main.set_ylabel('Impedance (Ohm)')
    ax_main.grid(True, which="both", ls="--", alpha=0.6)

    ax_err.plot(df_history['iteration'], df_history['error'], color='gray', lw=1, alpha=0.8)
    ax_err.set_yscale('log'); ax_err.set_title('Error Convergence'); ax_err.set_xlabel('Iteration'); ax_err.set_ylabel('RMSE Error (log scale)')
    ax_err.grid(True, which="both", ls="--", alpha=0.6)

    for param in param_names:
        ax_param.plot(df_history['iteration'], df_history[param], lw=1, alpha=0.8, label=param)
    ax_param.set_yscale('log'); ax_param.set_title('Parameter Evolution'); ax_param.set_xlabel('Iteration'); ax_param.set_ylabel('Parameter Value (log scale)')
    ax_param.legend(fontsize='small', ncol=2)
    ax_param.grid(True, which="both", ls="--", alpha=0.6)
    
    sim_curve_line, = ax_main.plot([], [], color='red', linestyle='--', lw=2, label='Simulated')
    error_dot, = ax_err.plot([], [], 'ro', markersize=8)
    title_text = ax_main.text(0.05, 0.05, '', transform=ax_main.transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.8))
    ax_main.legend()

    def update(frame_num):
        iter_index = frame_indices[frame_num]
        curve_data = curves_history[f'iter_{iter_index}']
        sim_mag = np.abs(curve_data[:, 1] + 1j * curve_data[:, 2])
        sim_curve_line.set_data(curve_data[:, 0], sim_mag)
        
        current_iter = df_history.loc[iter_index, 'iteration']
        current_error = df_history.loc[iter_index, 'error']
        error_dot.set_data([current_iter], [current_error])
        title_text.set_text(f'Iteration: {current_iter}\nError: {current_error:.4e}')
        
        return sim_curve_line, error_dot, title_text

    logging.info(f"正在生成動畫，總共 {len(frame_indices)} 幀... 這可能需要幾分鐘時間。")
    anim = FuncAnimation(fig, update, frames=len(frame_indices), blit=True, interval=50)
    
    try:
        output_gif_path.parent.mkdir(exist_ok=True)
        anim.save(str(output_gif_path), writer='pillow', fps=fps)
        logging.info(f"動畫成功儲存至: {output_gif_path}")
    except Exception as e:
        logging.error(f"儲存動畫失敗。請確保已安裝 'pillow' 函式庫 (`pip install pillow`)。錯誤訊息: {e}")
    plt.close(fig)

# --- 主程式 (if __name__ == '__main__') ---
if __name__ == '__main__':
    logging.info("="*50)
    logging.info("=== 執行 M08 模組 (Animate Params) 獨立測試 ===")
    logging.info("="*50)

    logging.info("正在生成假的歷史檔案以供 M08 測試...")
    
    param_names = ['R1', 'L1', 'C1']
    true_params = [50.0, 2.2e-6, 4.7e-12]
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    measured_data_path = OUTPUT_DIR / 'm01_interpolated_data.csv'
    freq_points = np.logspace(6, 9, 401)
    w = 2 * np.pi * freq_points
    Z_ideal_complex = 1 / (1/true_params[0] + 1j*(w*true_params[2] - 1/(w*true_params[1])))
    pd.DataFrame({'Frequency_Hz': freq_points, 'Z_CM': np.abs(Z_ideal_complex)}).to_csv(measured_data_path, index=False)
    
    RESULTS_DIR.mkdir(exist_ok=True)
    history_csv_path = RESULTS_DIR / 'demo_history_params.csv'
    history_npz_path = RESULTS_DIR / 'demo_history_curves.npz'
    
    total_iters = 100
    curves_history_dict = {}
    current_params = np.array([100.0, 5e-6, 1e-12])
    
    with open(history_csv_path, 'w', newline='') as f:
        df_header = pd.DataFrame(columns=['iteration', 'error'] + param_names)
        df_header.to_csv(f, index=False)
        for i in range(total_iters):
            progress = (i / (total_iters - 1))**2 if total_iters > 1 else 1
            params_for_iter = current_params * (1 - progress) + np.array(true_params) * progress
            sim_z_complex = 1 / (1/params_for_iter[0] + 1j*(w*params_for_iter[2] - 1/(w*params_for_iter[1])))
            error = np.sqrt(np.mean((np.log10(np.abs(sim_z_complex)) - np.log10(np.abs(Z_ideal_complex)))**2))
            row = pd.DataFrame([[i, error] + list(params_for_iter)], columns=df_header.columns)
            row.to_csv(f, header=False, index=False)
            curves_history_dict[f'iter_{i}'] = np.vstack([freq_points, sim_z_complex.real, sim_z_complex.imag]).T
    np.savez_compressed(history_npz_path, **curves_history_dict)
    logging.info("假的歷史檔案生成完畢。")
    
    # 呼叫主函式來生成動畫
    output_gif_path = FIGURE_DIR / 'M08_optimization_animation.gif'
    create_animation(
        history_csv_path=history_csv_path,
        history_npz_path=history_npz_path,
        measured_data_path=measured_data_path,
        output_gif_path=output_gif_path,
        animation_step=2,
        fps=15
    )
    
    logging.info("="*50)
    logging.info("=== 獨立測試執行成功！ ===")
    logging.info(f"動畫已儲存至: {output_gif_path}")
    logging.info("="*50)
