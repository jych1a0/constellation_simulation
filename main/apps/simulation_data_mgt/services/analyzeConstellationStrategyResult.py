# -*- coding: utf-8 -*-
"""
分析 ConstellationStrategy（星座策略）模組的模擬結果，提供統計、視覺化等功能。
"""
from main.utils.logger import log_trigger, log_writer
import os
import pandas as pd

@log_trigger('INFO')
def analyzeConstellationStrategyResult(simulation_result_dir):
    """
    功能：
      1. 掃描 simulation_result_dir 目錄下所有 .csv 檔 (例如 satToAllRightSatAER*.csv、satToAllRightSatDistance*.csv)。
      2. 若檔案包含 satId, stdDiffA, stdDiffE, stdDiffR 四欄位 => 進行「AER 分析」。
      3. 否則若包含 satId, minDist, maxDist, meanDist 四欄位 => 進行「Distance 分析」。
      4. 逐一分析後，把結果放入同一個 list 中回傳。
      5. 回傳格式示例：
         {
             "constellationStrategy_simulation_result": [
                 {
                     "csv_used": "xxx.csv",
                     "...(分析結果)": ...
                 },
                 ...
             ]
         }
    """

    # 收集所有 .csv 檔
    csv_files = [f for f in os.listdir(simulation_result_dir) if f.lower().endswith('.csv')]
    if not csv_files:
        print(f"[WARN] No CSV files found in {simulation_result_dir}")
        return None

    results_list = []

    for csv_filename in csv_files:
        csv_path = os.path.join(simulation_result_dir, csv_filename)

        if not os.path.exists(csv_path):
            print(f"[ERROR] CSV does not exist: {csv_path}")
            continue  # 找不到檔案就跳過

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"[ERROR] Exception reading CSV ({csv_filename}): {str(e)}")
            continue

        # 判斷欄位
        df_cols = set(df.columns)

        # AER 所需欄位
        aer_required_cols = {'satId', 'stdDiffA', 'stdDiffE', 'stdDiffR'}
        # Distance 所需欄位
        dist_required_cols = {'satId', 'minDist', 'maxDist', 'meanDist'}

        if aer_required_cols.issubset(df_cols):
            # ========== AER 分析邏輯 ========== #
            max_stdDiffR = float(df['stdDiffR'].max())
            idx_of_maxR = int(df['stdDiffR'].idxmax())
            satId_of_maxR = int(df.loc[idx_of_maxR, 'satId'])

            mean_stdDiffA = float(df['stdDiffA'].mean())
            mean_stdDiffE = float(df['stdDiffE'].mean())
            mean_stdDiffR = float(df['stdDiffR'].mean())

            aer_result = {
                "csv_used": csv_filename,
                "count": int(len(df)),
                "analysis_type": "AER",
                "max_stdDiffR": max_stdDiffR,
                "satId_of_maxR": satId_of_maxR,
                "mean_stdDiffA": mean_stdDiffA,
                "mean_stdDiffE": mean_stdDiffE,
                "mean_stdDiffR": mean_stdDiffR
            }
            results_list.append(aer_result)

        elif dist_required_cols.issubset(df_cols):
            # ========== Distance 分析邏輯 ========== #
            max_maxDist = float(df['maxDist'].max())
            idx_of_maxDist = int(df['maxDist'].idxmax())
            satId_of_maxDist = int(df.loc[idx_of_maxDist, 'satId'])

            min_minDist = float(df['minDist'].min())
            idx_of_minDist = int(df['minDist'].idxmin())
            satId_of_minDist = int(df.loc[idx_of_minDist, 'satId'])

            mean_meanDist = float(df['meanDist'].mean())

            dist_result = {
                "csv_used": csv_filename,
                "count": int(len(df)),
                "analysis_type": "Distance",
                "max_maxDist": max_maxDist,
                "satId_of_maxDist": satId_of_maxDist,
                "min_minDist": min_minDist,
                "satId_of_minDist": satId_of_minDist,
                "mean_meanDist": mean_meanDist
            }
            results_list.append(dist_result)
        else:
            # 既非 AER 也非 Distance => 不做任何分析
            print(f"[WARN] {csv_filename} does not contain required columns for AER or Distance analysis.")

    # 若完全沒有任何分析結果 (皆不符合欄位需求或讀取失敗)，就回傳 None
    if not results_list:
        return None

    final_result = {
        "constellationStrategy_simulation_result": results_list
    }

    print("[INFO] analyzeConstellationStrategyResult =>", final_result)
    return final_result
