from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
import os

@log_trigger('INFO')
def genEndToEndRoutingResultPDF(endToEndRouting):
    """
    讀取 endToEndRouting 的模擬結果(endToEndRouting.endToEndRouting_simulation_result)，
    產生 PDF 報告並返回 PDF 路徑。
    """
    # 取得當前時間（做為報表生成時間）
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 取得模擬結果（字典）
    sim_results = endToEndRouting.endToEndRouting_simulation_result

    report_metrics = {
        'Metric': [
            'handover_strategy',
            'handover_decision',
            'beam_count',
            'handover_count',
            'throughput',
            'latency',
            'hop',
            'distance',
            'loss',
            'access_loss',
            'feeder_loss',
            'rx_buffer',
            'tx_buffer'
        ],
        'Value': [
            str(sim_results['handover_strategy']),       
            str(sim_results['handover_decision']),       
            str(sim_results['beam_count']),              
            str(sim_results['handover_count']),          
            f"{float(sim_results['throughput']):.4f}",   
            f"{float(sim_results['latency']):.4f}",
            f"{float(sim_results['hop']):.4f}",
            f"{float(sim_results['distance']):.4f}",
            f"{float(sim_results['loss']):.4f}",
            f"{float(sim_results['access_loss']):.4f}",
            f"{float(sim_results['feeder_loss']):.4f}",
            str(sim_results['rx_buffer']),               # 可能為整數
            str(sim_results['tx_buffer'])                # 可能為整數
        ]
    }

    # 將報告數據轉為 DataFrame
    df_metrics = pd.DataFrame(report_metrics)
    
    # 建立 PDF 路徑 (ex: endToEndRouting_simulation_report.pdf)
    pdf_path = os.path.join(endToEndRouting.endToEndRouting_data_path, 'endToEndRouting_simulation_report.pdf')
    pdf_pages = PdfPages(pdf_path)

    try:
        # 第一頁：實驗條件
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.axis('off')

        # 在右上角加上時間戳
        plt.figtext(0.95, 0.95, f'Generated: {timestamp}',
                    ha='right', va='top', fontsize=10)

        # 如果 endToEndRouting 中有參數設定 (endToEndRouting.endToEndRouting_parameter)，可在此顯示
        condition_data = [
            [k, str(v)] for k, v in endToEndRouting.endToEndRouting_parameter.items()
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

        plt.title('EndToEndRouting Simulation Conditions', pad=20, size=14, weight='bold')
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

        plt.title('EndToEndRouting Simulation Results', pad=20, size=14, weight='bold')
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
