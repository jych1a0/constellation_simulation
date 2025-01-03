from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
import math  # 若未使用可移除

@log_trigger('INFO')
def genModifyRegenRoutingResultPDF(modifyRegenRouting):
    """
    產生 ModifyRegenRouting 的報告 PDF：
      - 第一頁：modifyRegenRouting.modifyRegenRouting_parameter 表格 + 右上角時間戳記
      - 第二頁：ISLBreak vs avgHopCount 的折線圖
      - 第三頁：ISLBreak vs avgDistance 的折線圖 (若有該欄位)
      - 第四頁：ISLBreak vs runtime 的折線圖 (若有該欄位)
    """

    # 1. 取得當下時間（用在第一頁右上角的時間戳記）
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. 生成 PDF 路徑
    pdf_path = os.path.join(
        modifyRegenRouting.modifyRegenRouting_data_path,
        'modifyRegenRouting_simulation_report.pdf'
    )
    pdf_pages = PdfPages(pdf_path)

    try:
        # ========== 第一頁：實驗條件（Parameter Table） ========== #
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.axis('off')

        # 在右上角放時間戳記
        plt.figtext(0.95, 0.95, f'Generated: {timestamp}',
                    ha='right', va='top', fontsize=10)

        # 將 modifyRegenRouting.modifyRegenRouting_parameter 做成 (key, value) 表格
        condition_data = [
            [k, str(v)]
            for k, v in modifyRegenRouting.modifyRegenRouting_parameter.items()
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

        plt.title('ModifyRegenRouting - Simulation Conditions', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # ========== 第二頁、第三頁、第四頁：畫圖 ========== #
        csv_list = [f for f in os.listdir(modifyRegenRouting.modifyRegenRouting_data_path) if f.lower().endswith('.csv')]
        if not csv_list:
            print(f"[WARN] No CSV files found in: {modifyRegenRouting.modifyRegenRouting_data_path}")
        else:
            csv_path = os.path.join(modifyRegenRouting.modifyRegenRouting_data_path, csv_list[0])
            print(f"[INFO] Using ModifyRegenRouting CSV: {csv_path}")

            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)

                    # ========== 第 2 頁：ISLBreak vs avgHopCount ========== #
                    required_cols = {"ISLBreak", "avgHopCount"}
                    if required_cols.issubset(df.columns):
                        sns.set_style("whitegrid")
                        fig2, ax2 = plt.subplots(figsize=(10, 6))

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
                    else:
                        print(f"[WARN] CSV 欄位不足，需要 {required_cols}, 實際為 {df.columns.tolist()}")

                    # ========== 第 3 頁：ISLBreak vs avgDistance ========== #
                    required_cols_3 = {"ISLBreak", "avgDistance"}
                    if required_cols_3.issubset(df.columns):
                        fig3, ax3 = plt.subplots(figsize=(10, 6))
                        sns.set_style("whitegrid")

                        ax3.plot(
                            df["ISLBreak"],
                            df["avgDistance"],
                            color='green',
                            marker='o',
                            linewidth=2,
                            label='avgDistance'
                        )
                        ax3.set_xlabel('ISLBreak', fontsize=14)
                        ax3.set_ylabel('Average Distance', fontsize=14)
                        ax3.tick_params(axis='both', labelsize=12)
                        ax3.legend(loc='upper left', fontsize=12)

                        plt.title('ISLBreak vs. avgDistance', fontsize=16, pad=15)
                        plt.tight_layout()
                        pdf_pages.savefig(fig3)
                        plt.close(fig3)
                    else:
                        print(f"[WARN] 缺少欄位: {required_cols_3}, 無法生成第 3 頁圖表。")

                    # ========== 第 4 頁：ISLBreak vs runtime ========== #
                    required_cols_4 = {"ISLBreak", "runtime"}
                    if required_cols_4.issubset(df.columns):
                        fig4, ax4 = plt.subplots(figsize=(10, 6))
                        sns.set_style("whitegrid")

                        ax4.plot(
                            df["ISLBreak"],
                            df["runtime"],
                            color='red',
                            marker='o',
                            linewidth=2,
                            label='runtime'
                        )
                        ax4.set_xlabel('ISLBreak', fontsize=14)
                        ax4.set_ylabel('Runtime', fontsize=14)
                        ax4.tick_params(axis='both', labelsize=12)
                        ax4.legend(loc='upper left', fontsize=12)

                        plt.title('ISLBreak vs. runtime', fontsize=16, pad=15)
                        plt.tight_layout()
                        pdf_pages.savefig(fig4)
                        plt.close(fig4)
                    else:
                        print(f"[WARN] 缺少欄位: {required_cols_4}, 無法生成第 4 頁圖表。")

                except Exception as e:
                    print(f"[WARN] Failed to generate ModifyRegenRouting charts. Detail: {str(e)}")

    except Exception as e:
        print(f"[ERROR] Error generating PDF: {str(e)}")
        raise
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
