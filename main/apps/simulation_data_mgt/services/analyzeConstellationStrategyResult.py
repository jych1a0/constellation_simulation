from main.utils.logger import log_trigger, log_writer
import os
import pandas as pd

@log_trigger('INFO')
def analyzeConstellationStrategyResult(simulation_result_dir):
    """
    功能：
      1. 掃描 simulation_result_dir 目錄下，找唯一的 CSV (例如 satToAllRightSatAER-101-xxx.csv)。
      2. 優先檢查是否含 satId, stdDiffA, stdDiffE, stdDiffR 四欄位並進行分析，
         若沒有，則改為檢查 satId, minDist, maxDist, meanDist。
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
        df_cols = set(df.columns)

        # 檢查是否包含原先需要的欄位
        if required_cols.issubset(df_cols):
            # ========== 原邏輯：分析 stdDiffA, stdDiffE, stdDiffR 等 ========== #
            max_stdDiffR = float(df['stdDiffR'].max())
            idx_of_maxR = int(df['stdDiffR'].idxmax())
            satId_of_maxR = int(df.loc[idx_of_maxR, 'satId'])

            mean_stdDiffA = float(df['stdDiffA'].mean())
            mean_stdDiffE = float(df['stdDiffE'].mean())
            mean_stdDiffR = float(df['stdDiffR'].mean())

            result_json = {
                "constellationStrategy_simulation_result": {
                    "csv_used": csv_filename,
                    "count": int(len(df)),
                    "max_stdDiffR": max_stdDiffR,
                    "satId_of_maxR": satId_of_maxR,
                    "mean_stdDiffA": mean_stdDiffA,
                    "mean_stdDiffE": mean_stdDiffE,
                    "mean_stdDiffR": mean_stdDiffR
                }
            }
            print("[INFO] analyzeConstellationStrategyResult =>", result_json)
            return result_json

        else:
            # ========== 新邏輯：換用 minDist, maxDist, meanDist 等資訊 ========== #
            print(f"[ERROR] Missing required columns. Need {required_cols}, found {list(df.columns)}")
            
            alt_required_cols = {'satId', 'minDist', 'maxDist', 'meanDist'}
            if alt_required_cols.issubset(df_cols):
                # 做類似的分析，如最大/最小/平均距離等
                max_maxDist = float(df['maxDist'].max())
                idx_of_maxDist = int(df['maxDist'].idxmax())
                satId_of_maxDist = int(df.loc[idx_of_maxDist, 'satId'])

                min_minDist = float(df['minDist'].min())
                idx_of_minDist = int(df['minDist'].idxmin())
                satId_of_minDist = int(df.loc[idx_of_minDist, 'satId'])

                mean_meanDist = float(df['meanDist'].mean())

                alt_result_json = {
                    "constellationStrategy_simulation_result": {
                        "csv_used": csv_filename,
                        "count": int(len(df)),
                        "max_maxDist": max_maxDist,
                        "satId_of_maxDist": satId_of_maxDist,
                        "min_minDist": min_minDist,
                        "satId_of_minDist": satId_of_minDist,
                        "mean_meanDist": mean_meanDist
                    }
                }
                print("[INFO] analyzeConstellationStrategyResult =>", alt_result_json)
                return alt_result_json
            else:
                # 連替代欄位也不完整的話就直接結束
                print(f"[ERROR] CSV also does not contain the alternate required columns => {alt_required_cols}")
                return None

    except Exception as e:
        print(f"[ERROR] Exception in analyzeConstellationStrategyResult: {str(e)}")
        return None
