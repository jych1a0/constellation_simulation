from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
import os
from main.utils.update_parameter import update_parameter
@log_trigger('INFO')
def genOneToMultiResultPDF(oneToMulti):
    """
    讀取 oneToMulti 的模擬結果(oneToMulti.oneToMulti_simulation_result)，
    產生 PDF 報告並返回 PDF 路徑。
    """
    # 取得當前時間（做為報表生成時間）
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 取得模擬結果（字典）
    sim_results = oneToMulti.oneToMulti_simulation_result

    # 在此可自由調整要報告的欄位與顯示內容
    # 以下示範列出 throughput, latency, hop, distance, path_switch
    report_metrics = {
        'Metric': [
            'Throughput (bps)',
            'Latency (ms)',
            'Hop (count)',
            'Distance (km)',
            'Path Switch (count)'
        ],
        'Value': [
            f"{float(sim_results['throughput']):.4f}",
            f"{float(sim_results['latency']):.4f}",
            f"{float(sim_results['hop']):.4f}",
            f"{float(sim_results['distance']):.4f}",
            f"{float(sim_results['path_switch']):.4f}"
        ]
    }

    # 將報告數據轉為 DataFrame
    df_metrics = pd.DataFrame(report_metrics)
    
    # 建立 PDF 路徑 (ex: oneToMulti_simulation_report.pdf)
    pdf_path = os.path.join(oneToMulti.oneToMulti_data_path, 'oneToMulti_simulation_report.pdf')
    pdf_pages = PdfPages(pdf_path)
    base_dir = os.path.dirname(os.path.abspath(__file__))  
    config_path = os.path.join(base_dir, "update_parameter", "dynamic_config.json")
    oneToMulti.oneToMulti_parameter = update_parameter(
        oneToMulti.oneToMulti_parameter,
        config_path=config_path,
        process_name="oneToMulti_process"
    )

    try:
        # 第一頁：實驗條件
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.axis('off')

        # 在右上角加上時間戳
        plt.figtext(0.95, 0.95, f'Generated: {timestamp}',
                    ha='right', va='top', fontsize=10)

        # 如果 oneToMulti 中有參數設定 (oneToMulti.oneToMulti_parameter)，可在此顯示
        condition_data = [
            [k, str(v)] for k, v in oneToMulti.oneToMulti_parameter.items()
        ]
        
        table1 = ax1.table(
            cellText=condition_data,
            colLabels=['Parameter', 'Value'],
            cellLoc='center',
            loc='center',
            colWidths=[0.4, 0.4]
        )

        # 設定表格樣式
        table1.auto_set_font_size(False)
        table1.set_fontsize(12)
        table1.scale(1.2, 2)

        # 設定表頭樣式
        for (row, col), cell in table1.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#E6E6E6')
            cell.set_text_props(ha='center')

        plt.title('OneToMulti Simulation Conditions', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # 第二頁：實驗結果
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        ax2.axis('off')

        # 建立實驗結果表格
        table2 = ax2.table(
            cellText=df_metrics.values,
            colLabels=df_metrics.columns,
            cellLoc='center',
            loc='center',
            colWidths=[0.4, 0.4]
        )

        # 設定表格樣式
        table2.auto_set_font_size(False)
        table2.set_fontsize(12)
        table2.scale(1.2, 2)

        # 設定表頭樣式
        for (row, col), cell in table2.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#E6E6E6')
            cell.set_text_props(ha='center')

        plt.title('OneToMulti Simulation Results', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig2)
        plt.close(fig2)

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise
    finally:
        # 確保 PDF 正常關閉
        pdf_pages.close()
        plt.close('all')
    
    return pdf_path
