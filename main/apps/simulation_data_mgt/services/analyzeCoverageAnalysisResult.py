# -*- coding: utf-8 -*-
"""
分析 Coverage（覆蓋範圍）模組的模擬結果，提供統計、視覺化等功能。
"""
from main.utils.logger import log_trigger, log_writer
import os
import pandas as pd

@log_trigger('INFO')
def analyzeCoverageAnalysisResult(simulation_result_dir):
    """
    讀取只有 latitude, coverage 兩欄位的「唯一」CSV，
    並將其轉成參考 analyzeCoverageAnalysisResult 的 JSON 輸出格式
    """
    if not os.path.exists(simulation_result_dir):
        print(f"Path does not exist: {simulation_result_dir}")
        return

    csv_files_fullpath = []

    # 使用 os.walk 遞迴搜尋子目錄中所有 .csv
    for root, dirs, files in os.walk(simulation_result_dir):
        for f in files:
            if f.lower().endswith('.csv'):  # 加 .lower() 以防檔案副檔名是大寫或混合大小寫
                csv_files_fullpath.append(os.path.join(root, f))

    # 檢查搜出來的 CSV
    if len(csv_files_fullpath) == 0:
        print(f"No CSV file found in directory or subdirectories: {simulation_result_dir}")
        return
    elif len(csv_files_fullpath) > 1:
        print(f"More than one CSV file found. Found files: {csv_files_fullpath}")
        return

    # 取得唯一的那個 CSV
    simulation_result_file = csv_files_fullpath[0]

    try:
        df = pd.read_csv(simulation_result_file)
        required_columns = ['latitude', 'coverage']
        if not all(col in df.columns for col in required_columns):
            print(f"CSV should contain columns: {required_columns}")
            return

        coverage_dict = df.set_index('latitude')['coverage'].to_dict()
        result_json = {
            "coverage_analysis_result": coverage_dict
        }

        print(result_json)
        return result_json

    except Exception as e:
        print(f"Error processing coverage data: {str(e)}")
        return
