import os
import pandas as pd

def analyzeIslHoppingResult(simulation_result_dir):
    """
    在 simulation_result_dir 路徑下，搜尋唯一的 .csv 檔，
    讀取後僅擷取 `ISLBreak`、`avgHopCount` 兩欄位並將其轉成單一 dict:
        {
          "1": 6.30862,
          "2": 6.36131,
          "3": 6.39907,
          ...
        }
    """

    # 1. 確認 simulation_result_dir 是否為資料夾
    if not os.path.isdir(simulation_result_dir):
        print(f"[ERROR] {simulation_result_dir} 不是資料夾，無法進行 .csv 搜尋。")
        return None

    # 2. 在該資料夾下找所有 .csv
    csv_files = [f for f in os.listdir(simulation_result_dir) if f.lower().endswith('.csv')]
    if not csv_files:
        print(f"[WARN] 在目錄中找不到任何 CSV 檔：{simulation_result_dir}")
        return None
    elif len(csv_files) > 1:
        print(f"[WARN] 在目錄中找到多個 CSV，不確定要讀哪個：{csv_files}")
        return None

    # 3. 剛好只找到一個 CSV
    csv_path = os.path.join(simulation_result_dir, csv_files[0])
    print(f"[INFO] 使用 CSV: {csv_path}")

    # 4. 開始讀取並處理
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV 檔案不存在：{csv_path}")
        return None

    try:
        df = pd.read_csv(csv_path)

        # 檢查 CSV 是否包含所需欄位
        required_cols = {"ISLBreak", "avgHopCount"}
        if not required_cols.issubset(df.columns):
            print(f"[ERROR] CSV 欄位不足，需要 {required_cols}，實際為 {list(df.columns)}")
            return None

        # 只保留 `ISLBreak` 和 `avgHopCount` 這兩欄
        df_filtered = df[["ISLBreak", "avgHopCount"]]

        # 將 DataFrame 轉為 list[dict] 格式
        list_of_dict = df_filtered.to_dict(orient="records")

        # 轉成單一 dict：key = ISLBreak (字串), value = avgHopCount
        dict_data = {}
        for row in list_of_dict:
            isl_break = str(row["ISLBreak"])  # 轉字串以作為 dict key
            avg_hop = row["avgHopCount"]
            dict_data[isl_break] = avg_hop

        print("[INFO] 轉換後結構:", dict_data)
        return dict_data

    except Exception as e:
        print(f"[ERROR] 讀取或轉換 CSV 時發生錯誤: {str(e)}")
        return None