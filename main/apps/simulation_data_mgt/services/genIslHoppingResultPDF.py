from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
import math  # <-- 如果日後需要以 5 度或類似計算，可留著此匯入

@log_trigger('INFO')
def genIslHoppingResultPDF(islHopping):
    """
    產生 islHopping 的報告 PDF：
      - 第一頁：islHopping.islHopping_parameter 表格 + 右上角時間戳記
      - 第二頁：ISLBreak vs avgHopCount 的折線圖
    """

    # 1. 取得當下時間（用在第一頁右上角的時間戳記）
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. 生成 PDF 路徑
    pdf_path = os.path.join(islHopping.islHopping_data_path, 'islHopping_simulation_report.pdf')
    pdf_pages = PdfPages(pdf_path)

    try:
        # ========== 第一頁：實驗條件（Parameter Table） ========== #
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.axis('off')

        # 在右上角放時間戳記
        plt.figtext(0.95, 0.95, f'Generated: {timestamp}',
                    ha='right', va='top', fontsize=10)

        # 將 islHopping.islHopping_parameter 做成 (key, value) 表格
        condition_data = [
            [k, str(v)]
            for k, v in islHopping.islHopping_parameter.items()
        ]
        table1 = ax1.table(
            cellText=condition_data,
            colLabels=['Parameter', 'Value'],
            cellLoc='center',
            loc='center',
            colWidths=[0.4, 0.4]
        )

        table1.auto_set_font_size(False)
        table1.set_fontsize(12)
        table1.scale(1.2, 2)
        for (row, col), cell in table1.get_celld().items():
            # 設定表格第一列(style)
            if row == 0:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#E6E6E6')
            cell.set_text_props(ha='center')

        plt.title('ISL Hopping - Simulation Conditions', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # ========== 第二頁：ISLBreak vs avgHopCount 折線圖 ========== #
        csv_list = [f for f in os.listdir(islHopping.islHopping_data_path) if f.lower().endswith('.csv')]
        if not csv_list:
            print(f"[WARN] No CSV files found in: {islHopping.islHopping_data_path}")
        else:
            isl_csv_path = os.path.join(islHopping.islHopping_data_path, csv_list[0])
            print(f"[INFO] Using islHopping CSV: {isl_csv_path}")

            if os.path.exists(isl_csv_path):
                try:
                    df = pd.read_csv(isl_csv_path)

                    # 確保必須欄位存在
                    required_cols = {"ISLBreak", "avgHopCount"}
                    if not required_cols.issubset(df.columns):
                        print(f"[WARN] CSV 欄位不足，需要 {required_cols}, 但實際為 {df.columns.tolist()}")
                    else:
                        sns.set_style("whitegrid")

                        fig2, ax2 = plt.subplots(figsize=(10, 6))

                        # 繪製折線圖: x = ISLBreak, y = avgHopCount
                        ax2.plot(
                            df["ISLBreak"],
                            df["avgHopCount"],
                            color='blue',
                            marker='o',
                            linewidth=2,
                            label='avgHopCount'
                        )

                        ax2.set_xlabel('ISLBreak', fontsize=14)
                        ax2.set_ylabel('Average Hop Count', fontsize=14)
                        ax2.tick_params(axis='both', labelsize=12)
                        ax2.legend(loc='upper left', fontsize=12)

                        plt.title('ISLBreak vs. avgHopCount', fontsize=16, pad=15)

                        plt.tight_layout()
                        pdf_pages.savefig(fig2)
                        plt.close(fig2)
                except Exception as e:
                    print(f"[WARN] Failed to generate ISL Hopping chart. Detail: {str(e)}")

    except Exception as e:
        print(f"[ERROR] Error generating PDF: {str(e)}")
        raise
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
