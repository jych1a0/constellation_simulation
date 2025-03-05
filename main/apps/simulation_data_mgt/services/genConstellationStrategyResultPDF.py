from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import pandas as pd
import os
from main.utils.update_parameter import update_parameter

@log_trigger('INFO')
def genConstellationStrategyResultPDF(constellationStrategy):
    pdf_path = os.path.join(
        constellationStrategy.constellationStrategy_data_path,
        "constellationStrategy_simulation_report.pdf"
    )
    pdf_pages = PdfPages(pdf_path)

    base_dir = os.path.dirname(os.path.abspath(__file__))  
    config_path = os.path.join(base_dir, "update_parameter", "dynamic_config.json")

    # 更新動態參數
    constellationStrategy.constellationStrategy_parameter = update_parameter(
        constellationStrategy.constellationStrategy_parameter,
        config_path=config_path,
        process_name="constellationStrategy_process"
    )

    try:
        # ========== Page 1: Parameters ========== #
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

        # 掃描目錄下的 CSV
        csv_list = [f for f in os.listdir(constellationStrategy.constellationStrategy_data_path) 
                    if f.lower().endswith('.csv')]
        if not csv_list:
            print(f"[WARN] No CSV files found in: {constellationStrategy.constellationStrategy_data_path}")
        else:
            print(f"[INFO] Found CSV files: {csv_list}")

        # --------------- Page 2: Max Distance Between Adjacent Orbits --------------- #
        dist_csv_path = None
        for csv_filename in csv_list:
            tmp_path = os.path.join(constellationStrategy.constellationStrategy_data_path, csv_filename)
            try:
                df_temp = pd.read_csv(tmp_path)
                if {'satId', 'maxDist'}.issubset(df_temp.columns):
                    dist_csv_path = tmp_path
                    break  # 只取第一個符合條件的 CSV
            except:
                pass

        if dist_csv_path is not None and os.path.exists(dist_csv_path):
            try:
                df_dist = pd.read_csv(dist_csv_path)
                fig2, ax2 = plt.subplots(figsize=(10, 6))

                ax2.plot(df_dist["satId"], df_dist["maxDist"], marker='o', label='maxDist')
                ax2.set_xlabel("Satellite ID (satId)", fontsize=12)
                ax2.set_ylabel("Max Distance", fontsize=12)
                ax2.set_title("Max Distance Between Adjacent Orbits", fontsize=14)

                # 設置 x 軸刻度
                ax2.set_xticks(df_dist["satId"])
                ax2.set_xticklabels(df_dist["satId"], rotation=0)

                # 在點上標示數值
                for i, val in enumerate(df_dist["maxDist"]):
                    x = df_dist["satId"].iloc[i]
                    ax2.text(x, val, f"{val:.2f}", ha="center", va="bottom", fontsize=9)

                ax2.grid(True, which='major', linestyle='-', alpha=0.6)
                ax2.grid(True, which='minor', linestyle=':', alpha=0.3)
                ax2.legend(loc='best')

                plt.tight_layout()
                pdf_pages.savefig(fig2)
                plt.close(fig2)

            except Exception as e:
                print(f"[WARN] Failed to plot distance data. Error: {str(e)}")
        else:
            print("[INFO] No CSV file found that contains 'satId' and 'maxDist'. Skipping page 2.")

        # --------------- 找 AER CSV (含 diffA/diffE/diffR 與 stdDiffA/stdDiffE/stdDiffR) --------------- #
        aer_csv_path = None
        for csv_filename in csv_list:
            tmp_path = os.path.join(constellationStrategy.constellationStrategy_data_path, csv_filename)
            try:
                df_temp = pd.read_csv(tmp_path)
                # 是否同時具備 diffA, diffE, diffR，以及 stdDiffA, stdDiffE, stdDiffR
                if {'satId', 'diffA', 'diffE', 'diffR', 
                    'stdDiffA', 'stdDiffE', 'stdDiffR'}.issubset(df_temp.columns):
                    aer_csv_path = tmp_path
                    break
            except:
                pass

        # --------------- Page 3: Non-Standardized AER --------------- #
        # --------------- Page 4: Standardized AER --------------- #
        if aer_csv_path is not None and os.path.exists(aer_csv_path):
            try:
                df_aer = pd.read_csv(aer_csv_path)

                # --- 第 3 頁：非標準化 AER (diffA, diffE, diffR) ---
                fig3, ax3 = plt.subplots(figsize=(10, 6))
                ax3.plot(df_aer["satId"], df_aer["diffA"], marker='o', label='diffA')
                ax3.plot(df_aer["satId"], df_aer["diffE"], marker='o', label='diffE')
                ax3.plot(df_aer["satId"], df_aer["diffR"], marker='o', label='diffR')

                ax3.set_xlabel("Satellite ID (satId)", fontsize=12)
                ax3.set_ylabel("AER values (non-standardized)", fontsize=12)
                ax3.set_title("AER Variation Range (Non-Standardized) Between Adjacent Orbits", fontsize=14)

                ax3.set_xticks(df_aer["satId"])
                ax3.set_xticklabels(df_aer["satId"], rotation=0)

                # 在點上標示數值
                for i, val in enumerate(df_aer["diffA"]):
                    x = df_aer["satId"].iloc[i]
                    ax3.text(x, val, f"{val:.2f}", ha="center", va="bottom", fontsize=9)
                for i, val in enumerate(df_aer["diffE"]):
                    x = df_aer["satId"].iloc[i]
                    ax3.text(x, val, f"{val:.2f}", ha="center", va="bottom", fontsize=9)
                for i, val in enumerate(df_aer["diffR"]):
                    x = df_aer["satId"].iloc[i]
                    ax3.text(x, val, f"{val:.2f}", ha="center", va="bottom", fontsize=9)

                ax3.grid(True, which='major', linestyle='-', alpha=0.6)
                ax3.grid(True, which='minor', linestyle=':', alpha=0.3)
                ax3.legend(loc='best')
                plt.tight_layout()
                pdf_pages.savefig(fig3)
                plt.close(fig3)

                # --- 第 4 頁：標準化 AER (stdDiffA, stdDiffE, stdDiffR) ---
                fig4, ax4 = plt.subplots(figsize=(10, 6))
                ax4.plot(df_aer["satId"], df_aer["stdDiffA"], marker='o', label='stdDiffA')
                ax4.plot(df_aer["satId"], df_aer["stdDiffE"], marker='o', label='stdDiffE')
                ax4.plot(df_aer["satId"], df_aer["stdDiffR"], marker='o', label='stdDiffR')

                ax4.set_xlabel("Satellite ID (satId)", fontsize=12)
                ax4.set_ylabel("AER values (standardized)", fontsize=12)
                ax4.set_title("AER Variation Range (Standardized) Between Adjacent Orbits", fontsize=14)

                ax4.set_xticks(df_aer["satId"])
                ax4.set_xticklabels(df_aer["satId"], rotation=0)

                # 在點上標示數值
                for i, val in enumerate(df_aer["stdDiffA"]):
                    x = df_aer["satId"].iloc[i]
                    ax4.text(x, val, f"{val:.2f}", ha="center", va="bottom", fontsize=9)
                for i, val in enumerate(df_aer["stdDiffE"]):
                    x = df_aer["satId"].iloc[i]
                    ax4.text(x, val, f"{val:.2f}", ha="center", va="bottom", fontsize=9)
                for i, val in enumerate(df_aer["stdDiffR"]):
                    x = df_aer["satId"].iloc[i]
                    ax4.text(x, val, f"{val:.2f}", ha="center", va="bottom", fontsize=9)

                ax4.grid(True, which='major', linestyle='-', alpha=0.6)
                ax4.grid(True, which='minor', linestyle=':', alpha=0.3)
                ax4.legend(loc='best')
                plt.tight_layout()
                pdf_pages.savefig(fig4)
                plt.close(fig4)

            except Exception as e:
                print(f"[WARN] Failed to plot AER data. Error: {str(e)}")
        else:
            print("[INFO] No CSV file found that contains both diffA/diffE/diffR and stdDiffA/stdDiffE/stdDiffR. Skipping pages 3 & 4.")

    except Exception as e:
        print(f"[ERROR] genConstellationStrategyResultPDF => {str(e)}")
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
