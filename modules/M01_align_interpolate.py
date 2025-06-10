# m01_align_interpolate.py
# -*- coding: utf-8 -*-

"""
模組 M01: 阻抗資料對齊與插值

功能：
1. 讀取兩組原始阻抗資料（CM 和 NM）。
2. 建立一個標準化的對數掃描頻率軸（1 MHz - 3 GHz, 401 點）。
3. 使用線性插值將兩組資料對齊到新的頻率軸上。
4. 將處理完成的資料輸出成單一 CSV 檔案。
5. 記錄所有操作過程至指定的日誌檔案。
"""

import os
import logging
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# --- 全域設定 ---
# 頻率軸規格
FREQ_START = 1e6  # 1 MHz
FREQ_STOP = 3e9   # 3 GHz
NUM_POINTS = 401  # 401 點

# --- 【新增】定義專案根目錄 ---
# 取得此腳本檔案所在的目錄的絕對路徑 (例如: /path/to/project/modules)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 取得上一層目錄，即專案的根目錄 (例如: /path/to/project)
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# --- 【修改】路徑改為相對於專案根目錄 ---
# 檔案路徑
LOG_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
LOG_FILE_PATH = os.path.join(LOG_DIR, 'm01_align_interpolate.log')
INPUT_FILES = {
    'CM': os.path.join(DATA_DIR, '801CM.txt'),
    'NM': os.path.join(DATA_DIR, '801NM.txt')
}
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, 'm01_interpolated_data.csv')

# --- 日誌設定 ---
def setup_logging():
    """設定日誌記錄器"""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 防止重複添加 handler
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # 檔案 handler
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
def align_and_interpolate():
    """
    執行阻抗資料的讀取、對齊與插值。

    Returns:
        pd.DataFrame: 包含標準頻率軸與兩組插值後阻抗資料的 DataFrame，
                      若處理失敗則返回 None。
    """
    logger.info("M01 模組啟動：開始進行阻抗資料對齊與插值...")

    # 1. 建立標準化的目標頻率軸 (對數掃描)
    target_freq_axis = np.logspace(
        np.log10(FREQ_START),
        np.log10(FREQ_STOP),
        NUM_POINTS
    )
    logger.info(f"已建立目標頻率軸: {FREQ_START/1e6:.1f} MHz 至 {FREQ_STOP/1e9:.1f} GHz，共 {NUM_POINTS} 點。")
    
    interpolated_results = {}

    # 2. 讀取並處理各組資料
    for source_type, file_path in INPUT_FILES.items():
        logger.info(f"開始處理來源: {source_type}, 檔案: {file_path}")
        
        try:
            # 檢查檔案是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"找不到指定的輸入檔案: {file_path}")

            # 讀取資料，假設為兩欄：Frequency, Impedance
            source_data = pd.read_csv(
                file_path,
                sep=r'\s+',          # 使用正則表達式匹配一個或多個空白字元
                header=None,
                names=['Frequency', 'Impedance'],
                engine='python'
            )

            if source_data.empty:
                logger.warning(f"檔案 {file_path} 為空，將跳過此來源。")
                continue

            # 3. 建立插值函數
            # bounds_error=False 允許外插，fill_value=np.nan 可標示超出範圍的點
            interp_func = interp1d(
                source_data['Frequency'],
                source_data['Impedance'],
                kind='linear',
                bounds_error=False,
                fill_value=np.nan
            )
            
            # 4. 進行插值
            interpolated_z = interp_func(target_freq_axis)
            interpolated_results[f'Z_{source_type}'] = interpolated_z
            logger.info(f"來源 {source_type} 資料已成功插值到目標頻率軸。")

        except FileNotFoundError as e:
            logger.error(str(e))
            return None
        except Exception as e:
            logger.error(f"處理檔案 {file_path} 時發生未預期的錯誤: {e}", exc_info=True)
            return None
            
    # 5. 組合最終結果
    if not interpolated_results:
        logger.error("沒有任何資料成功處理，無法產生輸出檔案。")
        return None
        
    final_df = pd.DataFrame(interpolated_results)
    final_df.insert(0, 'Frequency_Hz', target_freq_axis)

    # 檢查是否有因外插產生的 NaN 值
    nan_count = final_df.isnull().sum().sum()
    if nan_count > 0:
        logger.warning(f"輸出資料中包含 {nan_count} 個 NaN 值。這表示目標頻率點超出了原始資料的頻率範圍。")
    
    # 6. 儲存結果
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        final_df.to_csv(OUTPUT_CSV_PATH, index=False, float_format='%.6e')
        logger.info(f"已成功將結果儲存至: {OUTPUT_CSV_PATH}")
    except Exception as e:
        logger.error(f"儲存輸出檔案時發生錯誤: {e}", exc_info=True)
        return None
        
    logger.info("M01 模組執行成功。")
    return final_df


if __name__ == '__main__':
    print("正在執行 M01 模組 (align_interpolate)...")
    
    # 為了方便測試，手動建立假的資料檔案
    # 現在會在專案根目錄下建立 data 資料夾
    os.makedirs(DATA_DIR, exist_ok=True)
    # 假 CM 資料 (100kHz - 1GHz)
    freq_cm = np.logspace(5, 9, 200)
    z_cm = 50 * np.log10(freq_cm/1e5) + np.random.rand(200) * 5
    np.savetxt(INPUT_FILES['CM'], np.c_[freq_cm, z_cm], fmt='%.6e')
    # 假 NM 資料 (500kHz - 2GHz)
    freq_nm = np.logspace(5.7, 9.3, 250)
    z_nm = 20 * np.log10(freq_nm/1e5) + np.random.rand(250) * 3
    np.savetxt(INPUT_FILES['NM'], np.c_[freq_nm, z_nm], fmt='%.6e')
    print(f"已在 '{DATA_DIR}' 目錄下建立測試用的 801CM.txt 與 801NM.txt。")
    
    # 執行主功能
    result_dataframe = align_and_interpolate()
    
    if result_dataframe is not None:
        print("\n處理完成！結果預覽：")
        print(result_dataframe.head())
        print(f"\n日誌檔案已寫入至: {LOG_FILE_PATH}")
        print(f"輸出資料已儲存至: {OUTPUT_CSV_PATH}")
    else:
        print("\n處理失敗，請檢查日誌檔案獲取詳細資訊。")
        print(f"日誌檔案路徑: {LOG_FILE_PATH}")
