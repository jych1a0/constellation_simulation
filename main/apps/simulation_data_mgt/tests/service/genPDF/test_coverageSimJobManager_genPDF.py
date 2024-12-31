import sys
import os
import uuid
from datetime import datetime

# 將「含有 main/ 的資料夾」加入 sys.path
PROJECT_ROOT = "/root/241124_Constellation_Simulation/constellation_simulation"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main.apps.simulation_data_mgt.services.analyzeCoverageAnalysisResult import analyzeCoverageAnalysisResult
from main.apps.simulation_data_mgt.services.genCoverageAnalysisResultPDF import genCoverageAnalysisResultPDF

def test_run_coverage():
    # (1) 指定模擬結果資料夾 + CSV 檔名
    simulation_result_dir = (
        "/root/241124_Constellation_Simulation/constellation_simulation/"
        "simulation_result/coverage_simulation/"
        "b98e011b-4fed-4ba8-bfbc-e37e6d6b2f7f/8635a462-6baa-4523-9f55-d841f1b297f0"
    )
    coverage_csv_filename = "satCoverageLatitude--50-50-TLE_6P_22Sats_29deg_F1-3.csv"
    
    # 合併成完整檔案路徑
    full_csv_path = os.path.join(simulation_result_dir, coverage_csv_filename)
    
    # (2) 先做 Coverage 分析
    print(">>> Starting analysis...")
    analysis_result = analyzeCoverageAnalysisResult(full_csv_path)
    if analysis_result is None:
        print("[ERROR] Analysis failed or no data found.")
        return
    print(">>> Analysis result:")
    print(analysis_result)

    # (3) 模擬一個與 Coverage Model 相似的物件
    #     - 我們把它命名為 MockCoverage
    #     - 定義與 Coverage Model 近似的屬性：coverage_parameter, coverage_status, coverage_data_path, coverage_simulation_result...
    class MockCoverage:
        def __init__(self, coverage_data_path, coverage_simulation_result):
            # 1) Coverage 核心欄位
            self.coverage_uid = uuid.uuid4()  # 或自訂
            self.coverage_name = "Mock Coverage"
            self.coverage_parameter = {
                "some_param": "value123",
                "other_param": "foo"
            }
            self.coverage_status = "completed"
            self.coverage_data_path = coverage_data_path
            self.coverage_simulation_result = coverage_simulation_result

            # 2) 時間欄位 (若程式內有用到，就加上)
            self.coverage_create_time = datetime.now()
            self.coverage_update_time = datetime.now()

            # 3) 若後續程式要調用 save()，我們可以加一個假的
            #    這樣就不會因沒有這個方法而爆錯
            #    若不需要就可以省略
            # ------------------------------------------------
            # def save(self, *args, **kwargs):
            #     print("[MockCoverage] save() called. (no-op)")

            # 4) 若程式需要 f_user_uid，可以自行 mock
            #    例如：self.f_user_uid = MockUser(...) 
            # ------------------------------------------------

    # 初始化 MockCoverage
    mock_coverage = MockCoverage(
        coverage_data_path=simulation_result_dir,
        coverage_simulation_result=analysis_result
    )

    # (4) 產生 PDF
    print(">>> Generating PDF...")
    pdf_path = genCoverageAnalysisResultPDF(mock_coverage)
    print(f"PDF generated at: {pdf_path}")
    print("Done.")

if __name__ == "__main__":
    test_run_coverage()
