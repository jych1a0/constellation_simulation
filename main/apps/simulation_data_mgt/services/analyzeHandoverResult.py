from main.utils.logger import log_trigger, log_writer
import os
import pandas as pd

@log_trigger('INFO')
def analyzeHandoverResult(simulation_result_dir):
    ideal_path = os.path.join(simulation_result_dir, 'ideal', 'cell_analysis')
    actual_path = os.path.join(simulation_result_dir, 'actual', 'cell_analysis')

    columns_to_analyze = [
        'handover_count', 'handover_fail_count',
        'remaining_duration_to_first', 'remaining_start_to_first', 'remaining_end_to_first',
        'remaining_duration_from_last', 'remaining_start_from_last', 'remaining_end_from_last',
        'valid_interval_count',
        'sum_score_max', 'sum_score_min', 'sum_score_mean',
        'distance_of_available_gs_of_cell_mean_max', 'distance_of_available_gs_of_cell_mean_min', 'distance_of_available_gs_of_cell_mean_mean',
        'elevation_of_available_gs_of_cell_mean_max', 'elevation_of_available_gs_of_cell_mean_min', 'elevation_of_available_gs_of_cell_mean_mean',
        'ul_snr_of_available_gs_of_cell_mean_max', 'ul_snr_of_available_gs_of_cell_mean_min', 'ul_snr_of_available_gs_of_cell_mean_mean',
        'ul_code_rate_of_available_gs_of_cell_mean_max', 'ul_code_rate_of_available_gs_of_cell_mean_min', 'ul_code_rate_of_available_gs_of_cell_mean_mean',
        'dl_snr_of_available_gs_of_cell_mean_max', 'dl_snr_of_available_gs_of_cell_mean_min', 'dl_snr_of_available_gs_of_cell_mean_mean',
        'dl_code_rate_of_available_gs_of_cell_mean_max', 'dl_code_rate_of_available_gs_of_cell_mean_min', 'dl_code_rate_of_available_gs_of_cell_mean_mean',
        'connection_duration_max', 'connection_duration_min', 'connection_duration_mean', 'connection_duration_count',
        'disconnect_duration_max', 'disconnect_duration_min', 'disconnect_duration_mean', 'disconnect_duration_count'
    ]

    # 定義欄位名稱映射
    column_name_mapping = {
        # DL Code Rate 相關
        'dl_code_rate_of_available_gs_of_cell_mean_max': 'avg_cells_dl_code_rate_of_available_gs_of_cell_mean_max',
        'dl_code_rate_of_available_gs_of_cell_mean_min': 'avg_cells_dl_code_rate_of_available_gs_of_cell_mean_min',
        'dl_code_rate_of_available_gs_of_cell_mean_mean': 'avg_cells_dl_code_rate_of_available_gs_of_cell_mean_avg',
        
        # UL Code Rate 相關
        'ul_code_rate_of_available_gs_of_cell_mean_max': 'avg_cells_ul_code_rate_of_available_gs_of_cell_mean_max',
        'ul_code_rate_of_available_gs_of_cell_mean_min': 'avg_cells_ul_code_rate_of_available_gs_of_cell_mean_min',
        'ul_code_rate_of_available_gs_of_cell_mean_mean': 'avg_cells_ul_code_rate_of_available_gs_of_cell_mean_avg',
        
        # DL SNR 相關
        'dl_snr_of_available_gs_of_cell_mean_max': 'avg_cells_dl_snr_of_available_gs_of_cell_mean_max',
        'dl_snr_of_available_gs_of_cell_mean_min': 'avg_cells_dl_snr_of_available_gs_of_cell_mean_min',
        'dl_snr_of_available_gs_of_cell_mean_mean': 'avg_cells_dl_snr_of_available_gs_of_cell_mean_avg',
        
        # UL SNR 相關
        'ul_snr_of_available_gs_of_cell_mean_max': 'avg_cells_ul_snr_of_available_gs_of_cell_mean_max',
        'ul_snr_of_available_gs_of_cell_mean_min': 'avg_cells_ul_snr_of_available_gs_of_cell_mean_min',
        'ul_snr_of_available_gs_of_cell_mean_mean': 'avg_cells_ul_snr_of_available_gs_of_cell_mean_avg',
        
        # Distance 相關
        'distance_of_available_gs_of_cell_mean_max': 'avg_cells_distance_of_available_gs_of_cell_mean_max',
        'distance_of_available_gs_of_cell_mean_min': 'avg_cells_distance_of_available_gs_of_cell_mean_min',
        'distance_of_available_gs_of_cell_mean_mean': 'avg_cells_distance_of_available_gs_of_cell_mean_avg',
        
        # Elevation 相關
        'elevation_of_available_gs_of_cell_mean_max': 'avg_cells_elevation_of_available_gs_of_cell_mean_max',
        'elevation_of_available_gs_of_cell_mean_min': 'avg_cells_elevation_of_available_gs_of_cell_mean_min',
        'elevation_of_available_gs_of_cell_mean_mean': 'avg_cells_elevation_of_available_gs_of_cell_mean_avg',
        
        # 基本計數相關
        'handover_count': 'avg_cells_handover_count',
        'handover_fail_count': 'avg_cells_handover_fail_count',
        'valid_interval_count': 'avg_cells_valid_interval_count',
        
        # Score 相關
        'sum_score_max': 'avg_cells_sum_score_max',
        'sum_score_min': 'avg_cells_sum_score_min',
        'sum_score_mean': 'avg_cells_sum_score_mean',
        
        # Remaining time 相關
        'remaining_duration_to_first': 'avg_cells_remaining_duration_to_first',
        'remaining_start_to_first': 'avg_cells_remaining_start_to_first',
        'remaining_end_to_first': 'avg_cells_remaining_end_to_first',
        'remaining_duration_from_last': 'avg_cells_remaining_duration_from_last',
        'remaining_start_from_last': 'avg_cells_remaining_start_from_last',
        'remaining_end_from_last': 'avg_cells_remaining_end_from_last',
        
        # Connection Duration 相關
        'connection_duration_max': 'avg_cells_connection_duration_max',
        'connection_duration_min': 'avg_cells_connection_duration_min',
        'connection_duration_mean': 'avg_cells_connection_duration_mean',
        'connection_duration_count': 'avg_cells_connection_duration_count',
        
        # Disconnect Duration 相關
        'disconnect_duration_max': 'avg_cells_disconnect_duration_max',
        'disconnect_duration_min': 'avg_cells_disconnect_duration_min',
        'disconnect_duration_mean': 'avg_cells_disconnect_duration_mean',
        'disconnect_duration_count': 'avg_cells_disconnect_duration_count'
    }


    # 儲存每個Cell的數據和對應的Cell名稱
    ideal_data = []  # 改為列表而不是字典
    actual_data = []  # 改為列表而不是字典
    
    # 檢查目錄是否存在
    if not os.path.exists(ideal_path) or not os.path.exists(actual_path):
        print(f"One or both directories do not exist: {ideal_path}, {actual_path}")
        return
    
    # 處理理想情況
    try:
        for cell_folder in os.listdir(ideal_path):
            cell_path = os.path.join(ideal_path, cell_folder, 'statistics.csv')
            if os.path.exists(cell_path):
                df = pd.read_csv(cell_path)
                if all(col in df.columns for col in columns_to_analyze):  # 確保所有需要的列都存在
                    ideal_data.append(df[columns_to_analyze])
    except Exception as e:
        print(f"Error processing ideal data: {str(e)}")
        return

    # 處理實際情況
    try:
        for cell_folder in os.listdir(actual_path):
            cell_path = os.path.join(actual_path, cell_folder, 'statistics.csv')
            if os.path.exists(cell_path):
                df = pd.read_csv(cell_path)
                if all(col in df.columns for col in columns_to_analyze):  # 確保所有需要的列都存在
                    actual_data.append(df[columns_to_analyze])
    except Exception as e:
        print(f"Error processing actual data: {str(e)}")
        return

    # 檢查是否有數據
    if not ideal_data or not actual_data:
        print("No data found in one or both directories.")
        return
    
    try:
        # 計算平均值
        ideal_avg = pd.concat(ideal_data).mean()
        actual_avg = pd.concat(actual_data).mean()
        
        # 計算 Cell 數量
        ideal_cell_count = len(ideal_data)
        actual_cell_count = len(actual_data)

        # 創建結果DataFrame
        result = pd.DataFrame({
            'Ideal': ideal_avg,
            'Actual': actual_avg
        })

        # 輸出結果
        # print(f"Comparison of Ideal ({ideal_cell_count} cells) and Actual ({actual_cell_count} cells) Situations:")
        # print(result['Actual'])
        # 將 Actual 列轉換為 JSON 格式

        # 重命名索引
        result.rename(index=column_name_mapping, inplace=True)

        result_json = {
            "handover_simulation_result": result['Actual'].to_dict()
        }
        print(result_json)
        
        return result_json  # 返回結果供後續使用
        
    except Exception as e:
        print(f"Error calculating results: {str(e)}")
        return

