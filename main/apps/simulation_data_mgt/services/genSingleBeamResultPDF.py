from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
import os

@log_trigger('INFO')
def genSingleBeamResultPDF(singleBeam):
    """
    讀取 singleBeam 的模擬結果(singleBeam.singleBeam_simulation_result)，
    產生 PDF 報告並返回 PDF 路徑。
    """
    # 獲取當前時間
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 解析模擬結果 (從字串轉換為字典)
    sim_results = singleBeam.singleBeam_simulation_result

    # 整理報告數據，並格式化數值
    # （同時將報表中的文字 "Handover" 改為 "SingleBeam"）
    report_metrics = {
        'Metric': [
            'Handover Count',
            'Handover Failure Count',
            'Average Connection Duration (s)',
            'Average Disconnection Duration (s)',
            'Average Distance (km)'
        ],
        'Value': [
            f"{float(sim_results['handover_count']):.4f}",
            f"{float(sim_results['handover_fail_count']):.4f}",
            f"{float(sim_results['connection_duration_mean']):.4f}",
            f"{float(sim_results['disconnect_duration_mean']):.4f}",
            f"{float(sim_results['distance_mean']):.4f}"
        ]
    }

    # 轉換為 DataFrame 以便後續使用
    df_metrics = pd.DataFrame(report_metrics)
    
    # 使用 os.path.join 處理路徑
    pdf_path = os.path.join(singleBeam.singleBeam_data_path, 'singleBeam_simulation_report.pdf')
    pdf_pages = PdfPages(pdf_path)

    try:
        # 第一頁：實驗條件
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.axis('off')

        # 在右上角添加時間戳記
        plt.figtext(0.95, 0.95, f'Generated: {timestamp}',
                    ha='right', va='top', fontsize=10)

        # 創建實驗條件表格 (將 handover_parameter 換成 singleBeam_parameter)
        condition_data = [[k, str(v).replace('TLE_6P_22Sats_29deg_F1.txt', '6x22')
                                     .replace('TLE_3P_22Sats_29deg_F1.txt', '3x22')
                                     .replace('TLE_12P_22Sats_29deg_F7.txt', '12x22')]
                          for k, v in singleBeam.singleBeam_parameter.items()]
        
        table1 = ax1.table(
            cellText=condition_data,
            colLabels=['Parameter', 'Value'],
            cellLoc='center',
            loc='center',
            colWidths=[0.4, 0.4]
        )

        # 設置表格樣式
        table1.auto_set_font_size(False)
        table1.set_fontsize(12)
        table1.scale(1.2, 2)

        # 為標題行設置特殊樣式
        for (row, col), cell in table1.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#E6E6E6')
            cell.set_text_props(ha='center')

        plt.title('Simulation Conditions (SingleBeam)', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # 若有需要，可保留或刪除關於 Cell Topology 的頁面
        # # 第二頁：Cell Topology
        # cell_ut = singleBeam.singleBeam_parameter.get('cell_ut', '')
        # if cell_ut in ['28Cell_1UT', '38Cell_1UT']:
        #     fig2, ax2 = plt.subplots(figsize=(12, 8))
        #     assets_dir = 'main/apps/simulation_data_mgt/services/assets'
        #     cell_image = f'{assets_dir}/28cell.png' if cell_ut == '28Cell_1UT' else f'{assets_dir}/38cell.png'
        #     try:
        #         img = mpimg.imread(cell_image)
        #         ax2.imshow(img)
        #         ax2.axis('off')
        #         plt.title(f'Cell Topology ({cell_ut})', pad=20, size=14, weight='bold')
        #         plt.tight_layout()
        #         pdf_pages.savefig(fig2)
        #     except FileNotFoundError:
        #         print(f"Warning: {cell_image} file not found")
        #     finally:
        #         plt.close(fig2)

        # 第三頁：實驗結果
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        ax3.axis('off')

        # 使用之前整理的報告數據
        table2 = ax3.table(
            cellText=df_metrics.values,
            colLabels=df_metrics.columns,
            cellLoc='center',
            loc='center',
            colWidths=[0.4, 0.4]
        )

        # 設置表格樣式
        table2.auto_set_font_size(False)
        table2.set_fontsize(12)
        table2.scale(1.2, 2)

        # 為標題行設置特殊樣式
        for (row, col), cell in table2.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#E6E6E6')
            cell.set_text_props(ha='center')

        plt.title('Simulation Results (SingleBeam)', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig3)
        plt.close(fig3)

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise
    finally:
        # 確保 PDF 文件被正確關閉
        pdf_pages.close()
        plt.close('all')
    
    return pdf_path
