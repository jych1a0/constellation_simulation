from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

def sec_to_hms(seconds):
    hh = seconds // 3600
    mm = (seconds % 3600) // 60
    ss = seconds % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

@log_trigger('INFO')
def genConnectedDurationResultPDF(connectedDuration):
    """
    產生 PDF：
      - 第一頁：顯示 connectedDuration_parameter 表格 (10x6)
      - 第二頁：折線圖 (time vs coverSatCount) (10x6)
    """
    pdf_path = os.path.join(
        connectedDuration.connectedDuration_data_path, 
        "connectedDuration_simulation_report.pdf"
    )
    pdf_pages = PdfPages(pdf_path)

    try:
        # ========== 第 1 頁：connectedDuration_parameter 表格 (10x6) ========== #
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.axis('off')

        param_data = [
            [k, str(v)]
            for k, v in connectedDuration.connectedDuration_parameter.items()
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

        plt.title('Connected Duration - Parameters', fontsize=16, pad=10)
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # ========== 第 2 頁：折線圖 (10x6) ========== #
        csv_list = [f for f in os.listdir(connectedDuration.connectedDuration_data_path) if f.lower().endswith('.csv')]
        if not csv_list:
            print(f"[WARN] No CSV files found in: {connectedDuration.connectedDuration_data_path}")
        else:
            connectedDuration_csv_path = os.path.join(connectedDuration.connectedDuration_data_path, csv_list[0])
            print(f"[INFO] Using coverage CSV: {connectedDuration_csv_path}")
        if os.path.exists(connectedDuration_csv_path):
            try:
                df = pd.read_csv(connectedDuration_csv_path)
                if not {'time', 'coverSatCount'}.issubset(df.columns):
                    print(f"[WARN] CSV columns not match. Need 'time' & 'coverSatCount'. Found: {list(df.columns)}")
                else:
                    max_time = df['time'].max()
                    if max_time > 86399:
                        df = df[(df['time'] >= 0) & (df['time'] <= 86399)]

                    df['time_hms'] = df['time'].apply(sec_to_hms)

                    sns.set_style("whitegrid")
                    fig2, ax2 = plt.subplots(figsize=(10, 6))  # 與第一頁保持一致

                    ax2.plot(
                        df['time'],
                        df['coverSatCount'],
                        color='blue',
                        linewidth=2,
                        label='CoverSatCount'
                    )

                    ax2.set_xlabel('Time', fontsize=14)
                    ax2.set_ylabel('Number of Satellites', fontsize=14)
                    ax2.tick_params(axis='both', labelsize=12)
                    ax2.set_ylim(bottom=0)

                    max_count = df['coverSatCount'].max()
                    ax2.set_yticks(np.arange(0, max_count + 1, 1))

                    x_max = df['time'].max()
                    x_ticks = np.arange(0, x_max + 1, 3600)
                    if x_ticks[-1] < x_max:
                        x_ticks = np.append(x_ticks, x_max)
                    ax2.set_xticks(x_ticks)

                    x_labels = [sec_to_hms(x) for x in x_ticks]
                    ax2.set_xticklabels(x_labels, rotation=90)

                    ax2.grid(True, which='major', linestyle='-', alpha=0.6)
                    ax2.grid(True, which='minor', linestyle=':', alpha=0.3)

                    plt.title('Satellite Count Over Time', fontsize=16, pad=15)
                    ax2.legend(loc='upper left', fontsize=12)

                    plt.tight_layout()
                    pdf_pages.savefig(fig2)
                    plt.close(fig2)
            except Exception as e:
                print(f"[WARN] Failed to generate line chart. Detail: {str(e)}")
        else:
            print(f"[WARN] CSV file not found => {connectedDuration_csv_path}")

    except Exception as e:
        print(f"[ERROR] genConnectedDurationResultPDF => {str(e)}")
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
