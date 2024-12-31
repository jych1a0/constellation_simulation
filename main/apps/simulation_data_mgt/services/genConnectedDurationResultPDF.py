from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

# (選擇性) 定義一個函式將秒數轉成 HH:MM:SS
def sec_to_hms(seconds):
    hh = seconds // 3600
    mm = (seconds % 3600) // 60
    ss = seconds % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

@log_trigger('INFO')
def genConnectedDurationResultPDF(connectedDuration):
    """
    產生 PDF：
      - 第一頁：顯示 connectedDuration_parameter 表格
      - 第二頁：讀取該路徑底下某個 CSV（包含 time, coverSatCount），並繪製折線圖
    """
    # 決定要輸出的 PDF 路徑
    pdf_path = os.path.join(connectedDuration.connectedDuration_data_path, "connectedDuration_report.pdf")
    pdf_pages = PdfPages(pdf_path)

    try:
        # ========== 第 1 頁：connectedDuration_parameter 表格 ========== #
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.axis('off')

        # 將 connectedDuration_parameter 轉為可供 table 顯示的資料
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

        # ========== 第 2 頁：折線圖 (time vs coverSatCount) ========== #
        # 1. 假設要讀取固定檔名：groundStationCoverSat-TLE_6P_22Sats_29deg_F1.csv
        #    如果想改成可配置檔名，請從 connectedDuration_parameter 或其他方式取得
        csv_filename = "groundStationCoverSat-TLE_6P_22Sats_29deg_F1.csv"
        csv_path = os.path.join(connectedDuration.connectedDuration_data_path, csv_filename)

        if os.path.exists(csv_path):
            try:
                # 讀取 CSV
                df = pd.read_csv(csv_path)
                # 檢查必需欄位
                if not {'time', 'coverSatCount'}.issubset(df.columns):
                    print(f"[WARN] CSV columns not match. Need 'time' & 'coverSatCount'. Found: {list(df.columns)}")
                else:
                    # (可選) 只篩選 0 ~ 86399 的資料 (24 小時)
                    max_time = df['time'].max()
                    if max_time > 86399:
                        df = df[(df['time'] >= 0) & (df['time'] <= 86399)]

                    # 將 time 欄位轉成 HH:MM:SS (新增一個欄位 time_hms)
                    df['time_hms'] = df['time'].apply(sec_to_hms)

                    # 開始繪圖
                    sns.set_style("whitegrid")
                    fig2, ax2 = plt.subplots(figsize=(16, 10))

                    # 繪製折線圖
                    ax2.plot(
                        df['time'],  # x 軸直接用 time (秒數)
                        df['coverSatCount'],  # y 軸
                        color='blue',
                        linewidth=2,
                        label='CoverSatCount'
                    )

                    ax2.set_xlabel('Time (HH:MM:SS)', fontsize=14)
                    ax2.set_ylabel('Number of Satellites', fontsize=14)
                    ax2.tick_params(axis='both', labelsize=12)

                    # y 軸從 0 開始
                    ax2.set_ylim(bottom=0)

                    # 只顯示整數刻度
                    max_count = df['coverSatCount'].max()
                    ax2.set_yticks(np.arange(0, max_count + 1, 1))

                    # x 軸刻度：每 3600 秒 (1 小時) 一個
                    x_max = df['time'].max()
                    x_ticks = np.arange(0, x_max + 1, 3600)
                    if x_ticks[-1] < x_max:
                        x_ticks = np.append(x_ticks, x_max)
                    ax2.set_xticks(x_ticks)

                    # x 軸刻度轉換成 HH:MM:SS 文字
                    x_labels = [sec_to_hms(x) for x in x_ticks]
                    ax2.set_xticklabels(x_labels, rotation=90)

                    # 網格線
                    ax2.grid(True, which='major', linestyle='-', alpha=0.6)
                    ax2.grid(True, which='minor', linestyle=':', alpha=0.3)

                    # 圖表標題
                    plt.title('Satellite Count Over Time (HH:MM:SS)', fontsize=16, pad=15)

                    # 圖例
                    ax2.legend(loc='upper left', fontsize=12)

                    plt.tight_layout()
                    pdf_pages.savefig(fig2)
                    plt.close(fig2)
            except Exception as e:
                print(f"[WARN] Failed to generate line chart. Detail: {str(e)}")
        else:
            print(f"[WARN] CSV file not found => {csv_path}")

    except Exception as e:
        print(f"[ERROR] genConnectedDurationResultPDF => {str(e)}")
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
