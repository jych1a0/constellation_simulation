# -*- coding: utf-8 -*-
"""
分析 MultiToMulti（多對多路由）模組的模擬結果，提供統計、視覺化等功能。
"""
from main.utils.logger import log_trigger, log_writer
import os
import pandas as pd

@log_trigger('INFO')
def analyzeMultiToMultiResult(simulation_result_dir):
    """
    讀取 multi-to-multi 模式產生的 output_build.csv，並將其轉為 JSON 後回傳。
    最終輸出的 JSON 裡面將不包含 filename 欄位。
    """
    # 如果傳進來的是目錄，就把路徑改成該資料夾下的 output_build.csv
    if os.path.isdir(simulation_result_dir):
        simulation_result_dir = os.path.join(simulation_result_dir, "output_build.csv")

    # 檢查真正要讀的檔案路徑
    csv_path = simulation_result_dir
    if not os.path.exists(csv_path):
        print(f"檔案不存在：{csv_path}")
        return

    try:
        df = pd.read_csv(csv_path)
        
        # 將 DataFrame 轉為 JSON 格式（以 list[dict] 方式呈現）
        result_json = df.to_dict(orient="records")
        
        # 每筆資料都移除 'filename' 欄位
        for record in result_json:
            record.pop('filename', None)

        # 只印出並回傳第一筆資料
        print(result_json[0])
        return result_json[0]
    except Exception as e:
        print(f"讀取或轉換 CSV 時發生錯誤: {str(e)}")
        return