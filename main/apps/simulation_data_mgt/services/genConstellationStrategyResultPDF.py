from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
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

        # ========== 第 2 頁：Adjacent Orbit Satellites AER Variation Range ========== #
        csv_path = os.path.join(
            constellationStrategy.constellationStrategy_data_path,
            "satToAllRightSatAER-101-TLE_6P_22Sats_29deg_F1.csv"
        )
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)

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

            except Exception as e:
                print(f"[WARN] Failed to plot AER Variation Range. Error: {str(e)}")
        else:
            print(f"[WARN] CSV not found => {csv_path}")

    except Exception as e:
        print(f"[ERROR] genConstellationStrategyResultPDF => {str(e)}")
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
