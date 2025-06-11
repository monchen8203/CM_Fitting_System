# m07_plot_results.py (最終修正版，修正儲存路徑與示範區塊)
# -*- coding: utf-8 -*-

import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, Optional, List

# --- 全域設定 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
FIGURE_DIR = os.path.join(BASE_DIR, 'figure')   # 圖檔儲存路徑
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')   # 處理後數據的儲存路徑 (供示範區塊使用)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE_PATH = os.path.join(LOG_DIR, 'm07_plot_results.log')

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

# --- 核心功能函式 ---

def parse_ngspice_output(stdout: str) -> Optional[np.ndarray]:
    lines = stdout.strip().split('\n')
    data = []
    try:
        start_index = next(i for i, line in enumerate(lines) if 'Values' in line) + 1
    except StopIteration:
        logger.error("在 Ngspice 輸出中找不到 'Values' 標頭，無法解析。")
        return None

    for line in lines[start_index:]:
        line = line.strip()
        if not line or 'Total analysis time' in line:
            break
        try:
            freq_str, complex_val_str = line.split(maxsplit=1)
            real_str, imag_str = complex_val_str.split(',')
            data.append([float(freq_str), float(real_str), float(imag_str)])
        except (ValueError, IndexError) as e:
            logger.warning(f"無法解析此行，已跳過: '{line}'. 錯誤: {e}")
            continue
            
    if not data:
        logger.error("未能從 Ngspice 輸出中解析出任何有效數據。")
        return None
        
    return np.array(data)

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.sqrt(np.mean((y_true - y_pred)**2))

def plot_and_calculate_error(
    simulated_stdout: str,
    measured_csv_path: str,
    output_plot_filename: str = "impedance_comparison.png",
    impedance_type: str = "CM"
) -> Optional[float]:
    logger.info(f"開始解析 Ngspice 模擬數據...")
    sim_data = parse_ngspice_output(simulated_stdout)
    if sim_data is None: return None
    
    sim_freq = sim_data[:, 0]
    sim_impedance_complex = sim_data[:, 1] + 1j * sim_data[:, 2]
    sim_impedance_mag = np.abs(sim_impedance_complex)

    logger.info(f"讀取量測數據從: {measured_csv_path}")
    try:
        measured_df = pd.read_csv(measured_csv_path)
    except FileNotFoundError:
        logger.error(f"找不到量測數據檔案: {measured_csv_path}")
        return None
        
    measured_freq = measured_df['Frequency_Hz'].values
    z_column = 'Z_CM' if impedance_type.upper() == 'CM' else 'Z_NM'
    if z_column not in measured_df.columns:
        logger.error(f"量測數據中找不到 '{z_column}' 欄位。")
        return None
    measured_impedance_mag = measured_df[z_column].values

    measured_impedance_mag[measured_impedance_mag < 1e-9] = 1e-9
    sim_impedance_mag[sim_impedance_mag < 1e-9] = 1e-9
    error_db = 20 * np.log10(sim_impedance_mag) - 20 * np.log10(measured_impedance_mag)
    rmse_log_mag = calculate_rmse(np.log10(measured_impedance_mag), np.log10(sim_impedance_mag))
    logger.info(f"擬合結果的均方根誤差 (Log-Mag RMSE): {rmse_log_mag:.4f}")

    logger.info("開始繪製比較圖與誤差圖...")
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    fig.suptitle(f'{impedance_type} Impedance Comparison & Error', fontsize=16)

    ax1.plot(measured_freq, measured_impedance_mag, label='Measured', color='blue', linewidth=2)
    ax1.plot(sim_freq, sim_impedance_mag, label='Simulated (Fitted)', color='red', linestyle='--', linewidth=2)
    ax1.set_xscale('log'); ax1.set_yscale('log')
    ax1.set_ylabel('Impedance (Ohm)'); ax1.set_title('Impedance Magnitude vs. Frequency')
    ax1.legend(); ax1.grid(True, which="both", ls="-", color='0.85')

    ax2.plot(sim_freq, error_db, color='green', linewidth=1.5)
    ax2.set_xscale('log'); ax2.set_xlabel('Frequency (Hz)'); ax2.set_ylabel('Error (dB)')
    ax2.set_title('Simulation Error (Simulated - Measured)'); ax2.axhline(0, color='black', linestyle=':', linewidth=1)
    ax2.grid(True, which="both", ls="-", color='0.85')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # *** 核心修正：確保儲存到 FIGURE_DIR ***
    os.makedirs(FIGURE_DIR, exist_ok=True)
    full_plot_path = os.path.join(FIGURE_DIR, output_plot_filename)
    try:
        plt.savefig(full_plot_path, dpi=300)
        logger.info(f"圖表已成功儲存至: {full_plot_path}")
    except Exception as e:
        logger.error(f"儲存圖表失敗: {e}")
    plt.close(fig)

    return rmse_log_mag


# --- 獨立執行示範 (已修正路徑) ---
if __name__ == '__main__':
    print("正在執行 M07 模組 (Plot Results) 示範...")
    
    # *** 已修正 ***: 示範用的暫存 CSV 應放置於 output 資料夾
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    demo_measured_csv = os.path.join(OUTPUT_DIR, 'demo_measured_data.csv')
    
    freqs = np.logspace(6, 9, 401)
    R, L, C = 5, 50e-6, 20e-12
    Z_true = np.sqrt(R**2 + (2 * np.pi * freqs * L - 1 / (2 * np.pi * freqs * C))**2)
    Z_measured = Z_true * np.random.normal(1, 0.05, size=freqs.shape)
    pd.DataFrame({
        'Frequency_Hz': freqs, 'Z_CM': Z_measured, 'Z_NM': Z_measured / 10
    }).to_csv(demo_measured_csv, index=False)
    print(f"已生成示範用的量測數據: {demo_measured_csv}")

    R_fit, L_fit, C_fit = 4.8, 52e-6, 19e-12
    Z_sim_complex = R_fit + 1j * (2 * np.pi * freqs * L_fit - 1 / (2 * np.pi * freqs * C_fit))
    ngspice_output_str = "Values\n"
    for i in range(len(freqs)):
        ngspice_output_str += f"{freqs[i]:.6e}\t{Z_sim_complex[i].real:.6e},{Z_sim_complex[i].imag:.6e}\n"
    print("已生成示範用的 Ngspice 輸出內容。")

    rmse_value = plot_and_calculate_error(
        simulated_stdout=ngspice_output_str,
        measured_csv_path=demo_measured_csv,
        output_plot_filename="M07_demo_plot_CM.png",
        impedance_type="CM"
    )

    if rmse_value is not None:
        print(f"\n示範執行成功！")
        print(f"計算出的 Log-Mag RMSE 為: {rmse_value:.4f}")
        # *** 已修正 ***: 這裡的路徑現在會正確指向 figure 資料夾
        final_path = os.path.join(FIGURE_DIR, 'M07_demo_plot_CM.png')
        print(f"比較圖已儲存至: {final_path}")
    else:
        print(f"\n示範執行失敗，請檢查日誌檔案 '{LOG_FILE_PATH}'。")
