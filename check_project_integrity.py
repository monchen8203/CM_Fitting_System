import os

# 預期結構定義
EXPECTED_STRUCTURE = {
    "data": ["Tai_CM.txt", "801CM.txt", "801NM.txt"],
    "docs": [],
    "logs": [],
    "netlists": [],
    "output": [],
    "metadata": [
        "M01_align_interpolate.yaml",
        "M02_sensitivity_analysis.yaml",
        "M03_global_search.yaml",
        "M04_local_optimize.yaml",
        "M05_ngspice_runner.yaml",
        "M06_model_builder.yaml",
        "M07_plot_results.yaml",
        "M08_animate_params.yaml",
        "M09_draw_netlist.yaml",
        "run_align.yaml"
    ],
    "modules": [
        "M01_align_interpolate.py",
        "M02_sensitivity_analysis.py",
        "M03_global_search.py",
        "M04_local_optimize.py",
        "M05_ngspice_runner.py",
        "M06_model_builder.py",
        "M07_plot_results.py",
        "M08_animate_params.py",
        "M09_draw_netlist.py",
        "run_align.py",
    ],
    "": [  # 根目錄檔案
        "requirements.txt",
        "README.md",
        ".gitignore"
    ]
}

def check_structure(base_path="."):
    missing = []
    for folder, files in EXPECTED_STRUCTURE.items():
        full_folder = os.path.join(base_path, folder)
        if not os.path.exists(full_folder):
            print(f"❌ 資料夾不存在: {folder}")
            missing.append(folder + "/")
            continue
        for f in files:
            full_path = os.path.join(full_folder, f)
            if not os.path.isfile(full_path):
                print(f"❌ 缺少檔案: {os.path.join(folder, f)}")
                missing.append(os.path.join(folder, f))
            else:
                print(f"✅ 找到: {os.path.join(folder, f)}")
    if not missing:
        print("\n🎉 所有預期檔案與資料夾都存在。專案結構完整！")
    else:
        print(f"\n⚠️ 缺少 {len(missing)} 個項目，請補齊上面列出的檔案或資料夾。")

if __name__ == "__main__":
    check_structure()
