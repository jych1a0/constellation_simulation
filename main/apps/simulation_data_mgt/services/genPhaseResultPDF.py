from main.utils.logger import log_trigger, log_writer
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import re
from main.utils.update_parameter import update_parameter

@log_trigger('INFO')
def genPhaseResultPDF(phase):
    """
    1. 第一頁：phase.phase_parameter 表格 (size: 10x6)
    2. 第二頁：從 phase.phase_simulation_result['multiCsvResult'] 取得 {F→MinDist}，
       用折線 (lineplot) + 點 (marker='o') 的方式繪圖，並在每個點上方顯示數值。
    """
    pdf_path = os.path.join(phase.phase_data_path, "phase_simulation_report.pdf")
    pdf_pages = PdfPages(pdf_path)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "update_parameter", "dynamic_config.json")
    phase.phase_parameter = update_parameter(
        phase.phase_parameter,
        config_path=config_path,
        process_name="phase_process"
    )

    try:
        # ========== 第 1 頁：列出參數表 ========== #
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.axis('off')

        param_data = [[k, str(v)] for k, v in phase.phase_parameter.items()]
        
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

        # ========== 第 2 頁：F vs. MinDist - 折線 + 點 + 數值 ========== #
        simulation_result = phase.phase_simulation_result
        if not simulation_result:
            print("[WARN] phase.phase_simulation_result is empty. No chart generated.")
        else:
            f_min_dist_map = simulation_result.get("multiCsvResult", {})
            if not f_min_dist_map:
                print("[WARN] multiCsvResult is empty or not found. No chart generated.")
            else:
                # 將 { "F1": 123.45, "F2": 98.76, ... } 轉為 DataFrame
                df_f = pd.DataFrame(list(f_min_dist_map.items()), columns=["f_key", "min_dist"])

                # 從 f_key (如 'F1') 取出數字部分 (1) 以利排序
                df_f['f_number'] = df_f['f_key'].str.extract(r'(\d+)').astype(int)
                df_f.sort_values(by='f_number', inplace=True)

                sns.set_style("whitegrid")
                fig2, ax2 = plt.subplots(figsize=(10, 6))

                # 折線圖 (lineplot) + marker='o' 顯示每個點
                sns.lineplot(
                    data=df_f,
                    x='f_number',
                    y='min_dist',
                    marker='o',   # 用圓點當 marker
                    ax=ax2
                )

                ax2.set_xlabel("F Value", fontsize=14)
                ax2.set_ylabel("Min Distance", fontsize=14)
                ax2.set_title("Minimum Distance for Each F", fontsize=16, pad=15)

                # x 軸顯示 "F1", "F2", ...
                ax2.set_xticks(df_f['f_number'])
                ax2.set_xticklabels(df_f['f_key'])

                # === 在點上方加註數值 ===
                for i, row in df_f.iterrows():
                    ax2.annotate(
                        # 顯示到小數點後2位，您可視需求調整
                        text=f"{row['min_dist']:.2f}",  
                        xy=(row['f_number'], row['min_dist']),
                        xytext=(0, 6),          # 在 y 軸方向上偏移 6 pt
                        textcoords="offset points",
                        ha='center',
                        va='bottom'
                    )

                plt.tight_layout()
                pdf_pages.savefig(fig2)
                plt.close(fig2)

    except Exception as e:
        print(f"[ERROR] genPhaseResultPDF => {str(e)}")
    finally:
        pdf_pages.close()
        plt.close('all')

    return pdf_path
