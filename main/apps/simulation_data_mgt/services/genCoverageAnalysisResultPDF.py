from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import os

@log_trigger('INFO')
def genCoverageAnalysisResultPDF(handover):
    # 1. 取得當下時間（用在第一頁右上角的時間戳記）
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. 生成 PDF 路徑
    pdf_path = os.path.join(handover.coverage_analysis_data_path, 'handover_simulation_report.pdf')
    pdf_pages = PdfPages(pdf_path)

    try:
        # ========== 第一頁：實驗條件 ========== #
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.axis('off')

        # 第一頁右上角顯示時間戳記
        plt.figtext(0.95, 0.95, f'Generated: {timestamp}',
                    ha='right', va='top', fontsize=10)

        # 將 handover.handover_parameter 轉為表格
        condition_data = [
            [k, str(v)]  # 若要替換字串，可自行在這裡 .replace(...)
            for k, v in handover.handover_parameter.items()
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

        # 強調標題列
        for (row, col), cell in table1.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#E6E6E6')
            cell.set_text_props(ha='center')

        plt.title('Simulation Conditions', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # ========== 第二頁：Coverage 圖表 ========== #
        # 假設 CSV 檔案與其他模擬結果放在同一個資料夾
        coverage_csv = os.path.join(
            handover.handover_data_path,
            'satCoverageLatitude--50-50-TLE_6P_22Sats_29deg_F1-3.csv'
        )

        # 檔案存在才進行繪圖
        if os.path.exists(coverage_csv):
            try:
                # 讀取 Coverage CSV
                df = pd.read_csv(coverage_csv)

                # coverage 轉換為秒數 (1 天 = 86400 秒)
                df['coverage_seconds'] = df['coverage'] * 86400

                # 設定繪圖風格
                sns.set_style("whitegrid")

                # 建立圖表
                fig2, ax1 = plt.subplots(figsize=(16, 10))

                # 主圖 (Coverage 秒數)
                line1, = ax1.plot(
                    df['latitude'],
                    df['coverage_seconds'],
                    color='blue', linewidth=2, label='Coverage Time'
                )

                # X / Y 軸設定
                ax1.set_xlabel('Latitude (°)', fontsize=14)
                ax1.set_ylabel('Daily Coverage Time (seconds)', fontsize=14)
                ax1.tick_params(axis='both', labelsize=12)
                ax1.set_xticks(np.arange(-50, 51, 2))

                # 台灣緯度範圍
                taiwan_south = 22
                taiwan_north = 25.3
                ax1.axvline(x=taiwan_south, color='red', linestyle='--', alpha=0.5)
                ax1.axvline(x=taiwan_north, color='red', linestyle='--', alpha=0.5)
                ax1.axvspan(taiwan_south, taiwan_north, alpha=0.1, color='red')

                # 顯示台灣範圍標註文字
                y_pos = ax1.get_ylim()[1] * 0.95
                ax1.annotate('Taiwan\nLatitude\nRange',
                             xy=((taiwan_south + taiwan_north)/2, y_pos),
                             xytext=(0, 10), textcoords='offset points',
                             ha='center', va='bottom',
                             color='red',
                             fontsize=12)

                # 第二軸（小時）
                ax2 = ax1.twinx()
                ax2.set_ylabel('Time (hours)', fontsize=14)
                ax2.tick_params(axis='y', labelsize=12)
                ax2.set_ylim(0, 24)

                # 圖表標題
                plt.title('Satellite Coverage Time vs Latitude', fontsize=16, pad=15)

                # 圖例
                ax1.legend(
                    [line1],
                    ['Coverage Time'],
                    loc='upper right', fontsize=12
                )

                # 排版
                plt.tight_layout()

                # 存檔到 PDF 的第 2 頁
                pdf_pages.savefig(fig2)
                plt.close(fig2)

            except Exception as e:
                print(f"Warning: Failed to generate coverage chart. Detail: {str(e)}")
        else:
            print(f"Warning: Coverage CSV not found -> {coverage_csv}")

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise
    finally:
        # 關閉 PDF
        pdf_pages.close()
        plt.close('all')

    return pdf_path
