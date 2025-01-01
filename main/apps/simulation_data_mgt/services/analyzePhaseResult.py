from main.utils.logger import log_trigger, log_writer
import pandas as pd
import os

def sec_to_hms(seconds: float) -> str:
    """將秒數轉為 HH:MM:SS 字串。"""
    hh = int(seconds // 3600)
    mm = int((seconds % 3600) // 60)
    ss = int(seconds % 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

@log_trigger('INFO')
def analyzePhaseResult(simulation_result_dir):
    """
    1. 掃描 simulation_result_dir 下唯一的 CSV (例如: minDist-TLE_6P_22Sats_29deg_F1-minMaxR.csv)。
    2. 讀取並執行「每軌道 minDist」的分析 (不限制軌道數量)。
    3. 回傳 {"phase_simulation_result": {...}} 格式，並將所有數值轉為原生 int/float。
    """

    # 1) 在資料夾中找 CSV
    csv_files = [f for f in os.listdir(simulation_result_dir) if f.lower().endswith('.csv')]
    if not csv_files:
        print(f"[WARN] No CSV files found in {simulation_result_dir}")
        return None
    elif len(csv_files) > 1:
        print(f"[WARN] More than one CSV found, skipping. CSV list: {csv_files}")
        return None

    # 2) 取得唯一 CSV
    csv_filename = csv_files[0]
    csv_path = os.path.join(simulation_result_dir, csv_filename)
    print(f"[INFO] Using CSV => {csv_path}")

    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV not exist => {csv_path}")
        return None

    try:
        # 3) 讀取 CSV
        df = pd.read_csv(csv_path)
        required_cols = {'satId1', 'observedTime', 'minDist'}
        if not required_cols.issubset(df.columns):
            print(f"[ERROR] Missing columns. Need {required_cols}, found {list(df.columns)}")
            return None
        
        # 4) 建立 orbit 欄位 (動態) -> e.g. satId1 // 100
        df['orbit'] = df['satId1'] // 100

        # 5) 找出每條「實際出現」的軌道中，minDist 最小的一筆
        idx_min_orbit = df.groupby('orbit')['minDist'].idxmin()
        df_min_each_orbit = df.loc[idx_min_orbit].reset_index(drop=True)

        # 6) 若需要把 observedTime 轉成 HH:MM:SS
        df_min_each_orbit['observedTime_hms'] = df_min_each_orbit['observedTime'].apply(sec_to_hms)

        # 7) 取出欄位並轉為 list of dict
        #    先用 to_dict(orient='records') 取得結果，再逐一轉成 Python int/float
        raw_list = df_min_each_orbit[['orbit','satId1','observedTime','observedTime_hms','minDist']] \
                   .to_dict(orient='records')

        # 8) 轉換成原生 Python 數值 (int/float)
        min_data_list = []
        for item in raw_list:
            new_item = {}
            new_item['orbit'] = int(item['orbit'])  # orbit -> int
            new_item['satId1'] = int(item['satId1'])  # satId1 -> int
            new_item['observedTime'] = int(item['observedTime'])  # observedTime -> int
            new_item['observedTime_hms'] = str(item['observedTime_hms'])  # 文字就不用轉
            new_item['minDist'] = float(item['minDist'])  # minDist -> float
            min_data_list.append(new_item)

        # 9) 取得軌道清單 (df['orbit'].unique()) 並轉為 Python int
        unique_orbits_raw = df['orbit'].unique().tolist()  # e.g. numpy array 變 list
        unique_orbits = [int(o) for o in unique_orbits_raw]  # 轉為 Python int
        unique_orbits.sort()
        count_orbits = int(len(unique_orbits))  # 保險起見，轉 int

        # 10) 組裝最終 JSON
        #     count_minPoints = df_min_each_orbit.shape[0] -> int
        count_min_points = int(df_min_each_orbit.shape[0])

        result_json = {
            "phase_simulation_result": {
                "csv_used": csv_filename,
                "min_each_orbit": min_data_list,
                "count_minPoints": count_min_points,
                "unique_orbits": unique_orbits,
                "count_orbits": count_orbits
            }
        }
        print("[INFO] analyzePhaseResult =>", result_json)
        return result_json

    except Exception as e:
        print(f"[ERROR] Exception in analyzePhaseResult: {str(e)}")
        return None
