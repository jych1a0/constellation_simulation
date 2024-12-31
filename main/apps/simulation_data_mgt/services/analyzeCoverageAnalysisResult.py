from main.utils.logger import log_trigger, log_writer
import os
import pandas as pd

@log_trigger('INFO')
def analyzeCoverageAnalysisResult(simulation_result_dir):
    """
    讀取只有 latitude, coverage 兩欄位的 CSV，
    並將其轉成參考 analyzeCoverageAnalysisResult 的 JSON 輸出格式
    """

    # 檢查檔案是否存在
    if not os.path.exists(simulation_result_dir):
        print(f"File does not exist: {simulation_result_dir}")
        return
    
    try:
        # 讀取 CSV
        df = pd.read_csv(simulation_result_dir)

        # 確認必要欄位
        required_columns = ['latitude', 'coverage']
        if not all(col in df.columns for col in required_columns):
            print(f"CSV should contain columns: {required_columns}")
            return

        # 將 latitude 當作 key, coverage 當作 value，轉為 dict
        # 如果想輸出成陣列結構，也可以自行調整
        coverage_dict = df.set_index('latitude')['coverage'].to_dict()

        # 參考 analyzeCoverageAnalysisResult 的輸出結構
        result_json = {
            "coverage_analysis_result": coverage_dict
        }

        print(result_json)  # or log_writer.info(result_json)
        return result_json

    except Exception as e:
        print(f"Error processing coverage data: {str(e)}")
        return
