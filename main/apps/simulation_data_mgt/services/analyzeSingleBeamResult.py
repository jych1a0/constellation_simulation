from main.utils.logger import log_trigger, log_writer
import os
import pandas as pd

@log_trigger('INFO')
def analyzeSingleBeamResult(simulation_result_dir):
    """
    讀取 singleBeam 模式產生的 statistics.csv，並將其轉為 JSON 後回傳。
    最終輸出的 JSON 裡面將不包含 filename 欄位。
    預期結構:
      simulation_result_dir/
        ideal/
          gs_analysis/
            <some_subdir>/
              statistics.csv
            ...
    """
    if not os.path.isdir(simulation_result_dir):
        print(f"路徑不是資料夾或不存在: {simulation_result_dir}")
        return

    # 構建 "ideal/gs_analysis" 路徑
    gs_analysis_path = os.path.join(simulation_result_dir, "ideal", "gs_analysis")
    if not os.path.isdir(gs_analysis_path):
        print(f"找不到 ideal/gs_analysis 目錄: {gs_analysis_path}")
        return

    # 在 gs_analysis 裡，可能會有多個座標資料夾，例如 22.6645_120.301_0.01
    # 以下範例只讀取第一個找到的子目錄
    subdirs = [d for d in os.listdir(gs_analysis_path) 
               if os.path.isdir(os.path.join(gs_analysis_path, d))]
    if not subdirs:
        print(f"在 {gs_analysis_path} 下沒有任何子資料夾，找不到 statistics.csv。")
        return

    # 假設只處理第一個子目錄
    target_subdir = subdirs[0]
    statistics_csv_path = os.path.join(gs_analysis_path, target_subdir, "statistics.csv")

    if not os.path.exists(statistics_csv_path):
        print(f"找不到 statistics.csv 檔案: {statistics_csv_path}")
        return

    try:
        df = pd.read_csv(statistics_csv_path)
        
        # 將 DataFrame 轉為 JSON 格式（list[dict]）
        result_json = df.to_dict(orient="records")
        
        # 移除 'filename' 欄位（如有的話）
        for record in result_json:
            record.pop('filename', None)

        if result_json:
            print(result_json[0])   # 印出第一筆
            return result_json[0]   # 回傳第一筆
        else:
            print("statistics.csv 為空，沒有任何記錄。")
            return
    except Exception as e:
        print(f"讀取或轉換 CSV 時發生錯誤: {str(e)}")
        return
