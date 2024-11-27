import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
from datetime import datetime
from main.utils.logger import log_trigger, log_writer

@log_trigger('INFO')
def genISLResultPDFtmp():
    # 獲取當前時間
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 解析實驗條件
    experiment_conditions = {
        "constellation": "3x22",  
        "isl_link_method": "minMaxR",              
        "execute_function": "simGroundStationCoverSat",  
        "station_location": {
            "latitude": 25.049126147527762,         
            "longitude": 121.51379754215354,        
            "altitude": 0.192742                    
        }}

    # 創建PDF文件
    pdf_pages = PdfPages('./isl_simulation_report.pdf')

    # 第一頁：實驗條件
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    ax1.axis('off')

    # 在右上角添加時間戳記
    plt.figtext(0.95, 0.95, f'Generated: {current_time}', 
                ha='right', va='top', fontsize=10)

    # 處理巢狀字典以便於顯示
    condition_data = []
    for k, v in experiment_conditions.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                condition_data.append([f"{k}_{sub_k}", str(sub_v)])
        else:
            condition_data.append([k, str(v)])

    # 創建實驗條件表格
    table1 = ax1.table(cellText=condition_data,
                    colLabels=['Parameter', 'Value'],
                    cellLoc='center',
                    loc='center',
                    colWidths=[0.4, 0.4])

    # 設置表格樣式
    table1.auto_set_font_size(False)
    table1.set_fontsize(12)
    table1.scale(1.2, 2)

    # 為標題行設置特殊樣式
    for (row, col), cell in table1.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#E6E6E6')
        cell.set_text_props(ha='center')

    plt.title('Simulation Conditions', pad=20, size=14, weight='bold')
    plt.tight_layout()
    pdf_pages.savefig(fig1)

    # 第二頁：結果圖片
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    try:
        assets_dir = 'main/apps/simulation_data_mgt/services/assets'
        img = mpimg.imread(f'{assets_dir}/ISL_Result.png')  # 讀取結果圖片
        ax2.imshow(img)
        ax2.axis('off')
        plt.title('Simulation Results', pad=20, size=14, weight='bold')
        plt.tight_layout()
        pdf_pages.savefig(fig2)
    except FileNotFoundError:
        print("Warning: ISL_Result.png file not found")

    # 關閉PDF文件
    pdf_pages.close()