from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import os
import math  # <-- 新增 math
from main.utils.update_parameter import update_parameter
@log_trigger('INFO')
def genCoverageAnalysisResultPDF(coverage):
    # 1. 取得當下時間（用在第一頁右上角的時間戳記）
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. 生成 PDF 路徑
    pdf_path = os.path.join(coverage.coverage_data_path, 'coverage_simulation_report.pdf')
    pdf_pages = PdfPages(pdf_path)
    base_dir = os.path.dirname(os.path.abspath(__file__))  
    config_path = os.path.join(base_dir, "update_parameter", "dynamic_config.json")
    coverage.coverage_parameter = update_parameter(
        coverage.coverage_parameter,
        config_path=config_path,
        process_name="coverage_process"
    )
    # 3. 開始生成 PDF 內容
    try:
        # ========== 第一頁：實驗條件 ========== #
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.axis('off')
        plt.figtext(0.95, 0.95, f'Generated: {timestamp}',
                    ha='right', va='top', fontsize=10)

        condition_data = [
            [k, str(v)]
            for k, v in coverage.coverage_parameter.items()
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
            if row == 0:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#E6E6E6')
            cell.set_text_props(ha='center')

        plt.title('Simulation Conditions', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig1)
        plt.close(fig1)

        # ========== 第二頁：Coverage 圖表 ========== #
        csv_list = [f for f in os.listdir(coverage.coverage_data_path) if f.lower().endswith('.csv')]
        if not csv_list:
            print(f"[WARN] No CSV files found in: {coverage.coverage_data_path}")
        else:
            coverage_csv_path = os.path.join(coverage.coverage_data_path, csv_list[0])
            print(f"[INFO] Using coverage CSV: {coverage_csv_path}")

            if os.path.exists(coverage_csv_path):
                try:
                    df = pd.read_csv(coverage_csv_path)
                    df['coverage_seconds'] = df['coverage'] * 86400

                    sns.set_style("whitegrid")

                    fig2, ax2 = plt.subplots(figsize=(10, 6))
                    line1, = ax2.plot(
                        df['latitude'], 
                        df['coverage_seconds'],
                        color='blue', 
                        linewidth=2, 
                        label='Coverage Time'
                    )

                    ax2.set_xlabel('Latitude (°)', fontsize=14)
                    ax2.set_ylabel('Daily Coverage Time (seconds)', fontsize=14)
                    ax2.tick_params(axis='both', labelsize=12)

                    # 1) 根據檔案動態決定刻度範圍
                    min_lat = df['latitude'].min()
                    max_lat = df['latitude'].max()

                    # 2) 以 5 度為刻度，向下/向上取整至最接近的5度倍數
                    tick_start = math.floor(min_lat / 5) * 5
                    tick_end = math.ceil(max_lat / 5) * 5

                    # 3) 設定 x 軸刻度
                    ax2.set_xticks(np.arange(tick_start, tick_end + 1, 5))

                    # 加上台灣緯度範圍
                    taiwan_south = 22
                    taiwan_north = 25.3
                    ax2.axvline(x=taiwan_south, color='red', linestyle='--', alpha=0.5)
                    ax2.axvline(x=taiwan_north, color='red', linestyle='--', alpha=0.5)
                    ax2.axvspan(taiwan_south, taiwan_north, alpha=0.1, color='red')

                    # 標註台灣範圍
                    y_pos = ax2.get_ylim()[1] * 0.95
                    # ax2.annotate('',
                    #              xy=((taiwan_south + taiwan_north)/2, y_pos),
                    #              xytext=(0, 10), textcoords='offset points',
                    #              ha='center', va='bottom',
                    #              color='red', fontsize=12)

                    # 第二軸（小時）
                    ax3 = ax2.twinx()
                    ax3.set_ylabel('Time (hours)', fontsize=14)
                    ax3.tick_params(axis='y', labelsize=12)
                    ax3.set_ylim(0, 24)

                    plt.title('Satellite Coverage Time vs Latitude', fontsize=16, pad=15)
                    ax2.legend([line1], ['Coverage Time'], loc='upper right', fontsize=12)

                    plt.tight_layout()
                    pdf_pages.savefig(fig2)
                    plt.close(fig2)

                except Exception as e:
                    print(f"[WARN] Failed to generate coverage chart. Detail: {str(e)}")

    except Exception as e:
        print(f"[ERROR] Error generating PDF: {str(e)}")
        raise
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
