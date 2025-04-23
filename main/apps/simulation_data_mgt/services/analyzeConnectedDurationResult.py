# -*- coding: utf-8 -*-
"""
分析 ConnectedDuration（連線時長）模組的模擬結果，提供統計、視覺化等功能。
"""
from main.utils.logger import log_trigger, log_writer
import pandas as pd
import os

@log_trigger('INFO')
def analyzeConnectedDurationResult(simulation_result_dir):
    if not os.path.exists(simulation_result_dir):
        print(f"Path does not exist: {simulation_result_dir}")
        return

    csv_files_fullpath = []
    for root, dirs, files in os.walk(simulation_result_dir):
        for f in files:
            if f.lower().endswith('.csv'):
                csv_files_fullpath.append(os.path.join(root, f))

    if len(csv_files_fullpath) == 0:
        print(f"No CSV file found in directory or subdirectories: {simulation_result_dir}")
        return
    elif len(csv_files_fullpath) > 1:
        print(f"More than one CSV file found. Found files: {csv_files_fullpath}")
        return

    simulation_result_file = csv_files_fullpath[0]

    try:
        df = pd.read_csv(simulation_result_file)

        required_cols = ['time', 'coverSatCount']
        for col in required_cols:
            if col not in df.columns:
                print(f"[ERROR] Missing column: {col}")
                return None

        coverSatCount_mean = float(df['coverSatCount'].mean())
        coverSatCount_max  = int(df['coverSatCount'].max())
        coverSatCount_min  = int(df['coverSatCount'].min())
        data_count         = int(len(df))

        result_json = {
            "connectedDuration_simulation_result": {
                "coverSatCount_mean": coverSatCount_mean,
                "coverSatCount_max": coverSatCount_max,
                "coverSatCount_min": coverSatCount_min,
                "data_count": data_count
            }
        }
        print(f"[INFO] analyzeConnectedDurationResult => {result_json}")
        return result_json

    except Exception as e:
        print(f"[ERROR] Exception in analyzeConnectedDurationResult: {str(e)}")
        return None
