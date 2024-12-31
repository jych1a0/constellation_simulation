from main.utils.logger import log_trigger, log_writer
import os
import pandas as pd

@log_trigger('INFO')
def analyzeConstellationStrategyResult(simulation_result_dir):
    """
    功能：
      1. 掃描 simulation_result_dir 目錄下，找唯一的 CSV (例如 satToAllRightSatAER-101-xxx.csv)。
      2. 讀取後檢查是否含 satId, stdDiffA, stdDiffE, stdDiffR 四欄位。
      3. 進行簡易分析 (max, min, mean ...等)。
      4. 回傳 {"constellationStrategy_simulation_result": {...}} 格式的 JSON (dict)。
    """

    # 先在目錄裡找所有 .csv 檔
    csv_files = [f for f in os.listdir(simulation_result_dir) if f.lower().endswith('.csv')]
    
    if not csv_files:
        print(f"[WARN] No CSV files found in {simulation_result_dir}")
        return None
    elif len(csv_files) > 1:
        print(f"[WARN] More than one CSV found, not sure which to analyze. CSV list: {csv_files}")
        return None

    # 剛好只有一個 CSV
    csv_filename = csv_files[0]
    csv_path = os.path.join(simulation_result_dir, csv_filename)
    print(f"[INFO] Using CSV => {csv_path}")

    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV does not exist: {csv_path}")
        return None

    try:
        df = pd.read_csv(csv_path)
        required_cols = {'satId', 'stdDiffA', 'stdDiffE', 'stdDiffR'}
        
        # 檢查是否有缺漏欄位
        if not required_cols.issubset(df.columns):
            print(f"[ERROR] Missing required columns. Need {required_cols}, found {list(df.columns)}")
            return None

        # 找最大值
        max_stdDiffR = float(df['stdDiffR'].max())  # 轉 float
        idx_of_maxR = int(df['stdDiffR'].idxmax())  # 轉 int
        satId_of_maxR = int(df.loc[idx_of_maxR, 'satId'])  # 轉 int

        mean_stdDiffA = float(df['stdDiffA'].mean())
        mean_stdDiffE = float(df['stdDiffE'].mean())
        mean_stdDiffR = float(df['stdDiffR'].mean())

        result_json = {
            "constellationStrategy_simulation_result": {
                "csv_used": csv_filename,
                "count": int(len(df)),  # 轉 int
                "max_stdDiffR": max_stdDiffR,
                "satId_of_maxR": satId_of_maxR,
                "mean_stdDiffA": mean_stdDiffA,
                "mean_stdDiffE": mean_stdDiffE,
                "mean_stdDiffR": mean_stdDiffR
            }
        }
        
        print("[INFO] analyzeConstellationStrategyResult =>", result_json)
        return result_json

    except Exception as e:
        print(f"[ERROR] Exception in analyzeConstellationStrategyResult: {str(e)}")
        return None
