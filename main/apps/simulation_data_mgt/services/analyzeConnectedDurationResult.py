from main.utils.logger import log_trigger, log_writer
import pandas as pd
import os

@log_trigger('INFO')
def analyzeConnectedDurationResult(csv_file_path):
    """
    讀取 time,coverSatCount 兩欄位的 CSV，
    並回傳 connectedDuration_simulation_result (dict).
    """
    if not os.path.exists(csv_file_path):
        print(f"[ERROR] CSV does not exist: {csv_file_path}")
        return None

    try:
        df = pd.read_csv(csv_file_path)

        # 確認欄位
        required_cols = ['time', 'coverSatCount']
        for col in required_cols:
            if col not in df.columns:
                print(f"[ERROR] Missing column: {col}")
                return None

        # 做一些簡單的統計 (可依需求調整)
        coverSatCount_mean = df['coverSatCount'].mean()
        coverSatCount_max = df['coverSatCount'].max()
        coverSatCount_min = df['coverSatCount'].min()

        # 回傳的結果可自行設計
        result_json = {
            "connectedDuration_simulation_result": {
                "coverSatCount_mean": coverSatCount_mean,
                "coverSatCount_max": coverSatCount_max,
                "coverSatCount_min": coverSatCount_min,
                "data_count": len(df)
            }
        }
        print(f"[INFO] analyzeConnectedDurationResult => {result_json}")
        return result_json

    except Exception as e:
        print(f"[ERROR] Exception in analyzeConnectedDurationResult: {str(e)}")
        return None
