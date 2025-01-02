from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os

@log_trigger('INFO')
def genConstellationStrategyResultPDF(constellationStrategy):
    pdf_path = os.path.join(
        constellationStrategy.constellationStrategy_data_path,
        "constellationStrategy_simulation_report.pdf"
    )
    pdf_pages = PdfPages(pdf_path)

    try:
        # ========== 第 1 頁：Parameters ========== #
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.axis('off')

        param_data = [
            [k, str(v)]
            for k, v in constellationStrategy.constellationStrategy_parameter.items()
        ]
        table1 = ax1.table(
            cellText=param_data,
            colLabels=['Parameter', 'Value'],
            cellLoc='center',
            loc='center'
        )
        table1.auto_set_font_size(False)
        table1.set_fontsize(12)
        table1.scale(1.2, 2)

        ax1.set_title("ConstellationStrategy - Parameters", fontsize=14, pad=10)
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # ========== 第 2 頁：處理 CSV 生成圖表 ========== #
        csv_list = [f for f in os.listdir(constellationStrategy.constellationStrategy_data_path) if f.lower().endswith('.csv')]
        if not csv_list:
            print(f"[WARN] No CSV files found in: {constellationStrategy.constellationStrategy_data_path}")
        else:
            constellationStrategy_csv_path = os.path.join(constellationStrategy.constellationStrategy_data_path, csv_list[0])
            print(f"[INFO] Using CSV: {constellationStrategy_csv_path}")

        if os.path.exists(constellationStrategy_csv_path):
            try:
                df = pd.read_csv(constellationStrategy_csv_path)
                
                # 先檢查欄位是否包含預期欄位
                required_cols = {'satId', 'stdDiffA', 'stdDiffE', 'stdDiffR'}
                df_cols = set(df.columns)
                
                if required_cols.issubset(df_cols):
                    # --------- 舊邏輯：繪製 stdDiffA, stdDiffE, stdDiffR --------- #
                    fig2, ax2 = plt.subplots(figsize=(10, 6))
                    sns.set_style("whitegrid")

                    ax2.plot(df["satId"], df["stdDiffA"], marker='o', label='stdDiffA')
                    ax2.plot(df["satId"], df["stdDiffE"], marker='o', label='stdDiffE')
                    ax2.plot(df["satId"], df["stdDiffR"], marker='o', label='stdDiffR')

                    # 找出 stdDiffR 最大的那一筆資料
                    max_r_index = df["stdDiffR"].idxmax()
                    max_r_sat_id = df.loc[max_r_index, "satId"]
                    # (可依需求對 max_r_sat_id 做額外標註)

                    ax2.set_xlabel("Satellite ID (satId)", fontsize=12)
                    ax2.set_ylabel("Standardized Value", fontsize=12)
                    ax2.set_title("Adjacent Orbit Satellites AER Variation Range", fontsize=14)

                    # 設置 x 軸刻度
                    ax2.set_xticks(df["satId"])
                    ax2.set_xticklabels(df["satId"], rotation=0)

                    ax2.grid(True, which='major', linestyle='-', alpha=0.6)
                    ax2.grid(True, which='minor', linestyle=':', alpha=0.3)
                    ax2.legend(loc='best')

                    plt.tight_layout()
                    pdf_pages.savefig(fig2)
                    plt.close(fig2)

                else:
                    # --------- 新邏輯：沒有預期欄位，改用 maxDist vs satId --------- #
                    print(f"[WARN] Missing required columns. Need {required_cols}, found {df.columns.tolist()}")
                    
                    # 檢查是否有 satId, maxDist
                    alt_required_cols = {'satId', 'maxDist'}
                    if alt_required_cols.issubset(df_cols):
                        fig3, ax3 = plt.subplots(figsize=(10, 6))
                        sns.set_style("whitegrid")

                        ax3.plot(df["satId"], df["maxDist"], marker='o', color='red', label='maxDist')

                        ax3.set_xlabel("Satellite ID (satId)", fontsize=12)
                        ax3.set_ylabel("Max Distance", fontsize=12)
                        ax3.set_title("Max Dist Variation Range", fontsize=14)

                        ax3.set_xticks(df["satId"])
                        ax3.set_xticklabels(df["satId"], rotation=0)
                        ax3.grid(True, which='major', linestyle='-', alpha=0.6)
                        ax3.grid(True, which='minor', linestyle=':', alpha=0.3)
                        ax3.legend(loc='best')

                        plt.tight_layout()
                        pdf_pages.savefig(fig3)
                        plt.close(fig3)
                    else:
                        print(f"[WARN] The CSV also does not contain the alternate required columns => {alt_required_cols}")

            except Exception as e:
                print(f"[WARN] Failed to plot data. Error: {str(e)}")
        else:
            print(f"[WARN] CSV not found => {constellationStrategy_csv_path}")

    except Exception as e:
        print(f"[ERROR] genConstellationStrategyResultPDF => {str(e)}")
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
