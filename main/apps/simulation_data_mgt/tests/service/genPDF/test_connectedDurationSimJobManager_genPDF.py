import sys
import os
import uuid
from datetime import datetime

# 將「含有 main/ 的資料夾」加入 sys.path (若已在專案根目錄，可視情況省略)
PROJECT_ROOT = "/root/241124_Constellation_Simulation/constellation_simulation"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 匯入你實作的函式 (請確認實際路徑，若有不同檔名或資料夾需調整)
from main.apps.simulation_data_mgt.services.analyzeConnectedDurationResult import analyzeConnectedDurationResult
from main.apps.simulation_data_mgt.services.genConnectedDurationResultPDF import genConnectedDurationResultPDF


def test_run_connectedDuration():
    """
    測試流程：
      1. 指定『模擬結果目錄』，此目錄下應該正好有一個 CSV 檔 (time, coverSatCount)。
      2. 讀取該 CSV，執行 analyzeConnectedDurationResult。
      3. Mock 一個類似 ConnectedDuration 的物件，放入 simulation_result 與 data_path。
      4. 呼叫 genConnectedDurationResultPDF(...) 產生 PDF。
    """

    # (1) 指定模擬結果資料夾 + CSV 檔名
    simulation_result_dir = (
        "/root/241124_Constellation_Simulation/constellation_simulation/"
        "simulation_result/connectedDuration_simulation/"
        "aae8be6b-36a9-4dd2-98fc-97d19e188f42/9e3a560a-c2f4-4afd-b0f1-2485e76309bc"
    )
    connection_csv_filename = "groundStationCoverSat-TLE_6P_22Sats_29deg_F1.csv"
    
    # 合併成完整檔案路徑
    full_csv_path = os.path.join(simulation_result_dir, connection_csv_filename)
    # 注意：如果底下還有多層資料夾，再自行調整 path。 
    # 並確保該目錄底下只有 1 個 CSV（time, coverSatCount），符合需求。

    print(">>> Starting analysis for Connected Duration ...")
    analysis_result = analyzeConnectedDurationResult(full_csv_path)
    if analysis_result is None:
        print("[ERROR] Analysis failed or no data found.")
        return
    print(">>> Analysis result:")
    print(analysis_result)

    # (2) Mock 一個與 ConnectedDuration Model 相似的物件
    class MockConnectedDuration:
        def __init__(self, data_path, sim_result):
            # 基本欄位
            self.connectedDuration_uid = uuid.uuid4()
            self.connectedDuration_name = "Mock Connected Duration"
            self.connectedDuration_parameter = {
                "some_param": "value123",
                "other_param": "foo"
            }
            self.connectedDuration_status = "completed"
            self.connectedDuration_data_path = data_path
            self.connectedDuration_simulation_result = sim_result

            self.connectedDuration_create_time = datetime.now()
            self.connectedDuration_update_time = datetime.now()

            # 如果程式需要 .save()，可加：
            # def save(self, *args, **kwargs):
            #     print("[MockConnectedDuration] save() called. (no-op)")

    # (3) 初始化 MockConnectedDuration
    mock_obj = MockConnectedDuration(simulation_result_dir, analysis_result)

    # (4) 產生 PDF
    print(">>> Generating PDF...")
    pdf_path = genConnectedDurationResultPDF(mock_obj)
    print(f"PDF generated at: {pdf_path}")
    print("Done.")


if __name__ == "__main__":
    test_run_connectedDuration()
