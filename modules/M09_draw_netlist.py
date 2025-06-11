# m09_draw_netlist.py (最終完整修正版)
# -*- coding: utf-8 -*-

import sys
import os
import logging
import re
import matplotlib
matplotlib.use('Agg')
import schemdraw
import schemdraw.elements as elm
from pathlib import Path
from typing import Dict, Any

# --- 路徑修正 ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 全域設定 ---
PROJECT_ROOT = Path(project_root)
LOG_DIR = PROJECT_ROOT / 'logs'
FIGURE_DIR = PROJECT_ROOT / 'figure'
NETLIST_DIR = PROJECT_ROOT / 'netlist' / 'runnable'

# --- 日誌設定 ---
def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - (%(module)s) - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', handlers=[
                            logging.FileHandler(LOG_DIR / 'm09_draw_netlist.log', mode='w', encoding='utf-8'),
                            logging.StreamHandler(sys.stdout)
                        ])
setup_logging()

def parse_netlist_for_drawing(netlist_path: Path) -> Dict[str, Any]:
    components = {}
    pattern = re.compile(r"^(?P<name>[a-zA-Z]_[a-zA-Z0-9]+)\s+(?P<n1>\S+)\s+(?P<n2>\S+)\s+(?P<value>\S+)", re.IGNORECASE)
    try:
        with open(netlist_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    data = match.groupdict()
                    try:
                        value_float = float(data['value'])
                        if value_float < 1e-9: formatted_value = f"{value_float*1e12:.2f}p"
                        elif value_float < 1e-6: formatted_value = f"{value_float*1e9:.2f}n"
                        elif value_float < 1e-3: formatted_value = f"{value_float*1e6:.2f}μ"
                        elif value_float < 1: formatted_value = f"{value_float*1e3:.2f}m"
                        else: formatted_value = f"{value_float:.2f}"
                    except ValueError: formatted_value = data['value']
                    components[data['name'].upper()] = {'value': formatted_value, 'name_orig': data['name']}
    except FileNotFoundError:
        logging.error(f"找不到 Netlist 檔案: {netlist_path}")
        return {}
    return components

def draw_schematic(netlist_path: Path, output_filename_base: str):
    components = parse_netlist_for_drawing(netlist_path)
    if not components: return

    logging.info(f"開始使用 Schemdraw 繪製電路圖: {netlist_path.name}")
    
    with schemdraw.Drawing(fontsize=10, lw=1.5) as d:
        d.config(unit=3)
        def get_val(name): return components.get(name.upper(), {}).get('value', '?')
        def get_name(name): return components.get(name.upper(), {}).get('name_orig', name)
        
        def draw_element(elm_type, name, **kwargs):
            return elm_type(**kwargs).label(get_name(name), loc='top', ofst=0.2).label(get_val(name), loc='bottom', ofst=0.2)

        # 繪圖流程
        # 左上角
        IN1 = d.add(elm.Dot(label='IN_1')).at((-1, 6)); d.add(elm.Line().right())
        R1 = d.add(draw_element(elm.Resistor, 'R_R1').right()); N001 = d.add(elm.Dot().label('N001', 'top'))
        C1 = d.add(draw_element(elm.Capacitor, 'C_C1').at(N001.start).right()); N002 = d.add(elm.Dot().label('N002', 'top'))
        
        # 中間垂直部分
        R2 = d.add(draw_element(elm.Resistor, 'R_R2').at(N001.start).down()); N003 = d.add(elm.Dot().at(R2.end).label('N003', 'left'))
        
        # N002 到 N003 的橋接
        R3_start = (N002.start.x + d.unit/2, N001.start.y)
        d.add(elm.Line().at(N002.start).to(R3_start))
        R3 = d.add(draw_element(elm.Resistor, 'R_R3').at(R3_start).down().toy(N003.start)); d.add(elm.Line().to(N003.start))
        
        # 右上角
        d.add(elm.Line().at(N002.start).right().to((R3.end.x + d.unit * 2, N001.start.y))); IN2 = d.add(elm.Dot().label('IN_2', 'right'))
        
        # 左側電感
        L17_start = (N001.start.x - d.unit, N001.start.y)
        d.add(elm.Line().at(N001.start).to(L17_start)); L17 = d.add(draw_element(elm.Inductor, 'L_L17').at(L17_start).down().toy(N003.start)); N009 = d.add(elm.Dot().at(L17.end).label('N009', 'left'))
        L19 = d.add(draw_element(elm.Inductor, 'L_L19').at(N009.start).down(d.unit/2)); OUT1 = d.add(elm.Dot().at(L19.end).label('OUT_1', 'left')); d.add(elm.Line().at(OUT1.start).right().to(N003.start))
        d.add(elm.Ground().at(N009.start))
        
        # 右側電路
        d.add(elm.Line().at(N003.start).right(d.unit/2)); C3 = d.add(draw_element(elm.Capacitor, 'C_C3').down()); N004 = d.add(elm.Dot().at(C3.end).label('N004', 'right')); d.add(elm.Ground().at(N004.start))
        R37 = d.add(draw_element(elm.Resistor, 'R_R37').at(N004.start).right()); N005 = d.add(elm.Dot().at(R37.end).label('N005', 'top'))
        
        # *** 修正 ***: 補上被遺漏的繪圖邏輯
        L1 = d.add(draw_element(elm.Inductor, 'L_L1').at(N005.start).down()); N008 = d.add(elm.Dot().at(L1.end).label('N008', 'left'))
        d.add(draw_element(elm.Resistor, 'R_R43').at(N008.start).right())

        L3 = d.add(draw_element(elm.Inductor, 'L_L3').at(N008.start).down()); N007 = d.add(elm.Dot().at(L3.end).label('N007', 'left'))
        d.add(draw_element(elm.Resistor, 'R_R42').at(N007.start).right())

        L5 = d.add(draw_element(elm.Inductor, 'L_L5').at(N007.start).down()); N006 = d.add(elm.Dot().at(L5.end).label('N006', 'left'))
        d.add(draw_element(elm.Resistor, 'R_R41').at(N006.start).right())

        L7 = d.add(draw_element(elm.Inductor, 'L_L7').at(N006.start).down(d.unit/2)); OUT2 = d.add(elm.Dot().at(L7.end).label('OUT_2', 'left')); d.add(elm.Line().at(OUT2.start).right().to(N004.start))

        # 儲存
        FIGURE_DIR.mkdir(exist_ok=True)
        output_path = FIGURE_DIR / output_filename_base
        d.save(f"{output_path}.png", dpi=300, transparent=False)
        logging.info(f"電路圖已儲存為 PNG 至: {output_path}.png")

if __name__ == '__main__':
    logging.info("="*50)
    logging.info("=== 執行 M09 模組 (Draw Netlist with Schemdraw) 獨立測試 ===")
    logging.info("="*50)
    NETLIST_DIR.mkdir(exist_ok=True)
    test_netlist_path = NETLIST_DIR / 'demo_for_m09.cir'
    netlist_content = """* Demo Netlist for M09 Drawing Test
R_R1 N001 1 0.12
L_L17 N001 N009 3.5e-06
L_L19 N009 N003 3.5e-06
R_R2 N003 N001 15.2
C_C1 N002 N001 5.8e-12
R_R3 N003 N002 210.5
C_C3 N004 N003 1.1e-11
R_R37 N005 N004 5.1
L_L1 N008 N005 1.2e-05
L_L3 N007 N008 2.3e-05
L_L5 N006 N007 3.4e-05
L_L7 N003 N006 4.5e-05
R_R41 N006 N003 0.11
R_R42 N007 N006 0.12
R_R43 N008 N007 0.13
"""
    with open(test_netlist_path, 'w', encoding='utf-8') as f: f.write(netlist_content)
    logging.info(f"已生成示範用的 Netlist 檔案: {test_netlist_path}")
    draw_schematic(netlist_path=test_netlist_path, output_filename_base='M09_Generated_Schematic')
    logging.info("="*50)
    logging.info("=== 獨立測試執行完畢！ ===")
