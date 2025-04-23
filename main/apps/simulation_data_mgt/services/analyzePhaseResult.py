# -*- coding: utf-8 -*-
"""
分析 Phase（相位）模組的模擬結果，提供統計、視覺化等功能。
"""
import os
import re
import pandas as pd
from main.utils.logger import log_trigger, log_writer

def sec_to_hms(seconds: float) -> str:
    """將秒數轉為 HH:MM:SS 字串。"""
    hh = int(seconds // 3600)
    mm = int((seconds % 3600) // 60)
    ss = int(seconds % 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

@log_trigger('INFO')
def analyzePhaseResult(simulation_result_dir):
    """
    不分單/多 CSV，統一：
      1. 掃描資料夾中所有 CSV 檔 (符合 "F<num>" 命名規則)。
      2. 對每個 CSV 執行單檔分析，找出該檔的「最小距離」(所有 orbit 最小值)。
      3. 以 {"multiCsvResult": { "F1": x.xx, "F2": y.yy, ... }} 結構回傳。
    """

    csv_files = [f for f in os.listdir(simulation_result_dir) if f.lower().endswith('.csv')]
    if not csv_files:
        print(f"[WARN] No CSV files found in {simulation_result_dir}")
        return None

    print(f"[INFO] Found CSV files => {csv_files}")

    # 用來彙整 { "F1": 最小距離, "F2": 最小距離, ... }
    f_min_dist_map = {}

    pattern_f = re.compile(r'F(\d+)', re.IGNORECASE)

    for csv_filename in csv_files:
        # 從檔名抓 F 數字
        match = pattern_f.search(csv_filename)
        if not match:
            print(f"[WARN] CSV 檔案未含 F<num> 樣式, 略過 => {csv_filename}")
            continue
        f_str = match.group(1)  # 例如 '1', '2', '12'...
        f_key = f"F{f_str}"

        # 執行單檔分析，回傳該檔中的「每條 orbit 最小距離」清單
        single_result = _analyze_single_csv(simulation_result_dir, csv_filename)
        if not single_result:
            # 若分析失敗就跳過
            continue

        # single_result 結構中: single_result["phase_simulation_result"]["min_each_orbit"]
        min_each_orbit = single_result["phase_simulation_result"]["min_each_orbit"]
        if not min_each_orbit:
            continue

        # 找出整個 CSV (該 F) 所有 orbit 的最小值
        overall_min_dist = min(item["minDist"] for item in min_each_orbit)

        # 存入彙總字典
        f_min_dist_map[f_key] = overall_min_dist

    # 最後回傳統一的多檔格式
    result_json = {
        "multiCsvResult": f_min_dist_map
    }
    print("[INFO] analyzePhaseResult => multiCsvResult:", result_json)
    return result_json


def _analyze_single_csv(simulation_result_dir, csv_filename):
    """
    單檔分析邏輯：讀取 CSV，計算每條 orbit 的最小 minDist，並回傳結構:
    {
      "phase_simulation_result": {
          "csv_used": ...,
          "min_each_orbit": [...],
          ...
      }
    }
    """
    csv_path = os.path.join(simulation_result_dir, csv_filename)
    print(f"[INFO] Using CSV => {csv_path}")

    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV not exist => {csv_path}")
        return None

    try:
        df = pd.read_csv(csv_path)
        required_cols = {'satId1', 'observedTime', 'minDist'}
        if not required_cols.issubset(df.columns):
            print(f"[ERROR] Missing columns. Need {required_cols}, found {list(df.columns)}")
            return None
        
        # 建立 orbit 欄位 (例如: satId1 // 100)
        df['orbit'] = df['satId1'] // 100

        # 找出每條軌道中，minDist 最小的一筆
        idx_min_orbit = df.groupby('orbit')['minDist'].idxmin()
        df_min_each_orbit = df.loc[idx_min_orbit].reset_index(drop=True)

        # 若需要把 observedTime 轉成 HH:MM:SS
        df_min_each_orbit['observedTime_hms'] = df_min_each_orbit['observedTime'].apply(sec_to_hms)

        # 組成 list of dict
        raw_list = df_min_each_orbit[['orbit','satId1','observedTime','observedTime_hms','minDist']] \
                   .to_dict(orient='records')

        # 轉換成原生 Python 數值 (int/float)
        min_data_list = []
        for item in raw_list:
            new_item = {
                'orbit': int(item['orbit']),
                'satId1': int(item['satId1']),
                'observedTime': int(item['observedTime']),
                'observedTime_hms': str(item['observedTime_hms']),
                'minDist': float(item['minDist']),
            }
            min_data_list.append(new_item)

        unique_orbits = sorted(df['orbit'].unique().astype(int))
        count_orbits = len(unique_orbits)
        count_min_points = len(df_min_each_orbit)

        # 回傳與過去相同的資料結構
        result_json = {
            "phase_simulation_result": {
                "csv_used": csv_filename,
                "min_each_orbit": min_data_list,
                "count_minPoints": count_min_points,
                "unique_orbits": unique_orbits,
                "count_orbits": count_orbits
            }
        }
        print("[INFO] _analyze_single_csv =>", result_json)
        return result_json

    except Exception as e:
        print(f"[ERROR] Exception in _analyze_single_csv: {str(e)}")
        return None
