# init_config_structure.py
import os
import yaml

modules = [
    "M01_align_interpolate",
    "M02_sensitivity_analysis",
    "M03_global_search",
    "M04_local_optimize",
    "M05_ngspice_runner",
    "M06_model_builder",
    "M07_plot_results",
    "M08_animate_params",
    "M09_draw_netlist",
    "run_align"
]

default_config = {
    "enabled": True,
    "description": "Initial config file.",
    "parameters": {}
}

for mod in modules:
    folder = os.path.join("config", mod)
    os.makedirs(folder, exist_ok=True)
    config_path = os.path.join(folder, "config.yaml")
    
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, sort_keys=False)
        print(f"[✓] Created: {config_path}")
    else:
        print(f"[!] Skipped (already exists): {config_path}")
