from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

def sec_to_hms(seconds: float) -> str:
    hh = int(seconds // 3600)
    mm = int((seconds % 3600) // 60)
    ss = int(seconds % 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

@log_trigger('INFO')
def genPhaseResultPDF(phase):
    """
    1. 第一頁：phase.phase_parameter 表格 (size: 10x6)
    2. 第二頁：掃描 phase.phase_data_path 下唯一的 CSV，畫出 orbit vs minDist (散點圖)
       （不再硬寫死檔名）
    """
    pdf_path = os.path.join(phase.phase_data_path, "phase_result_report.pdf")
    pdf_pages = PdfPages(pdf_path)

    try:
        # ========== 第 1 頁：參數表 (10 x 6) ========== #
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.axis('off')

        param_data = [
            [k, str(v)]
            for k, v in phase.phase_parameter.items()
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

        ax1.set_title('Phase - Parameters', fontsize=16, pad=10)
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # ========== 第 2 頁：Orbit vs MinDist 散點圖 (動態讀取 CSV) ========== #
        # 1) 取得目錄下所有 CSV
        csv_files = [f for f in os.listdir(phase.phase_data_path) if f.lower().endswith('.csv')]
        if not csv_files:
            print(f"[WARN] No CSV files found in {phase.phase_data_path}.")
        elif len(csv_files) > 1:
            print(f"[WARN] More than one CSV found, skipping chart. CSV list: {csv_files}")
        else:
            # 剛好唯一 CSV
            csv_filename = csv_files[0]
            csv_path = os.path.join(phase.phase_data_path, csv_filename)
            print(f"[INFO] Using CSV => {csv_path}")

            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    # 假設要用 satId1 // 100 來得到 orbit
                    if 'satId1' in df.columns and 'minDist' in df.columns:
                        df['orbit'] = df['satId1'] // 100

                        # groupby 找 minDist 最小筆
                        idx_min = df.groupby('orbit')['minDist'].idxmin()
                        df_min = df.loc[idx_min].reset_index(drop=True)

                        # 若想轉 observedTime -> HH:MM:SS
                        if 'observedTime' in df_min.columns:
                            df_min['observedTime_hms'] = df_min['observedTime'].apply(sec_to_hms)

                        sns.set_style("whitegrid")
                        fig2, ax2 = plt.subplots(figsize=(10, 6))

                        sns.scatterplot(
                            data=df_min,
                            x='orbit',
                            y='minDist',
                            s=150,
                            alpha=0.9,
                            color='blue',
                            ax=ax2
                        )

                        ax2.set_xlabel("Orbit Number", fontsize=14)
                        ax2.set_ylabel("Min Distance", fontsize=14)
                        ax2.set_title("Minimum Distance per Orbit (Dynamic)", fontsize=16, pad=15)

                        # x 軸刻度依 df_min['orbit'].unique() 而定
                        unique_orbits = sorted(df_min['orbit'].unique())
                        ax2.set_xticks(unique_orbits)

                        # 註解 satId1, time
                        for i, row in df_min.iterrows():
                            label_str = f"satId1={row['satId1']}"
                            if 'observedTime_hms' in row:
                                label_str += f"\nT={row['observedTime_hms']}"
                            ax2.annotate(
                                label_str,
                                xy=(row['orbit'], row['minDist']),
                                xytext=(5, 10),
                                textcoords='offset points',
                                fontsize=10,
                                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5)
                            )

                        plt.tight_layout()
                        pdf_pages.savefig(fig2)
                        plt.close(fig2)
                    else:
                        print("[WARN] CSV missing 'satId1' or 'minDist' columns, cannot plot orbit chart.")
                except Exception as e:
                    print(f"[WARN] Failed to generate Phase scatter chart. Detail: {str(e)}")

    except Exception as e:
        print(f"[ERROR] genPhaseResultPDF => {str(e)}")
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path