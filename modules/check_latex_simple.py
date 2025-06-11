# check_latex_simple.py
import matplotlib
import matplotlib.pyplot as plt
import sys

print("--- 開始執行【極簡版】LaTeX 環境測試 ---")

try:
    # 步驟 1: 設定 Matplotlib 使用 LaTeX，並指定一個基礎字體
    matplotlib.rcParams['text.usetex'] = True
    matplotlib.rcParams['font.family'] = 'serif'
    matplotlib.rcParams['font.serif'] = ['Computer Modern Roman'] # 指定 LaTeX 的預設字體
    print("[步驟 1/2] Matplotlib 設定使用 LaTeX... 成功")

    # 步驟 2: 建立一個最簡單的圖表，只包含英文字
    fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
    ax.plot([0, 1], [0, 1])
    ax.set_title('Simple Title')
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    print("[步驟 2/2] 建立極簡圖表... 成功")

    # 步驟 3: 嘗試儲存圖檔
    output_filename = 'latex_test_simple.png'
    print(f"正在嘗試儲存圖檔至 '{output_filename}'...")
    fig.savefig(output_filename)
    
    print("\n【測試成功！】")
    print("您的 LaTeX 環境與 Matplotlib 的基礎整合是正常的。")
    print(f"請檢查專案根目錄下是否產生了 '{output_filename}' 圖片。")

except Exception as e:
    print("\n【測試失敗！】")
    print("即使在最簡化的情況下，您的環境仍然無法正確渲染。")
    print("這可能代表您的 MiKTeX 安裝雖然路徑正確，但缺少了基礎的字型宏包 (font packages)。")
    print("建議的解決方法: 打開 MiKTeX Console，手動執行一次『檢查更新』，讓它自動安裝必要的基礎套件。")
    print(f"\n收到的原始錯誤訊息:\n{e}")
