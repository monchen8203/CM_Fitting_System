from modules.m06_netlist_generator import generate_netlist

# 假設這是從使用者介面或設定檔讀取來的參數
user_parameters = {
    'resistance': '1.5k',
    'capacitance': '22n'
}

# 呼叫 M06 模組功能
is_successful = generate_netlist(
    template_filename='my_model.cir',
    output_filename='simulation_run_001.cir',
    parameters=user_parameters
)

if is_successful:
    print("Netlist 產生成功，準備執行 Ngspice...")
    # 接下來可以呼叫 M07 (Ngspice 執行模組)
else:
    print("Netlist 產生失敗，請查看日誌。")
