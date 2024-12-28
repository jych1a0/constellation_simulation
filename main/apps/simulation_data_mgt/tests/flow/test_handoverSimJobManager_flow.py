import requests
import json
import random
import time

# 直接在程式中寫死 IP 與 API 版本，也可改用環境變數或其他設定方式
DJANGO_SERVER = "127.0.0.1"
API_VERSION = "1.0"

def print_response(step_name, response):
    """輔助函式：方便打印每個步驟的回應內容"""
    print(f"\n=== {step_name} ===")
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except json.decoder.JSONDecodeError:
        print("Response is not JSON or is binary data.")
    print("=" * 30)

def main():
    # ---------------------------------------------------------------------
    # Flow 測試：（7步）
    #   1) meta_data_mgt.userManager.create_user
    #   2) meta_data_mgt.handoverManager.create_handover
    #   3) simulation_data_mgt.handoverSimJobManager.run_handover_sim_job
    #   4) simulation_data_mgt.handoverSimJobManager.download_handover_sim_result
    #   5) simulation_data_mgt.handoverSimJobManager.delete_handover_sim_result
    #   6) meta_data_mgt.handoverManager.delete_handover
    #   7) meta_data_mgt.userManager.delete_user
    # ---------------------------------------------------------------------

    # -------------------------------------------------
    # 1) 建立使用者 (create_user)
    # -------------------------------------------------
    create_user_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/userManager/create_user"
    user_payload = {
        "user_name": f"test{random.randint(1000,9999)}",
        "user_password": f"password{random.randint(1000,9999)}",
        "user_email": f"test{random.randint(1000,9999)}@example.com"
    }
    resp_create_user = requests.post(create_user_url, json=user_payload)
    print_response("1) Create User", resp_create_user)

    # 從回傳中取得 user_uid
    user_uid = None
    if resp_create_user.status_code == 200:
        res_json = resp_create_user.json()
        if res_json.get("status") == "success" and "data" in res_json:
            user_uid = res_json["data"].get("user_uid")

    if not user_uid:
        print("無法取得 user_uid，後續流程無法執行。")
        return

    # -------------------------------------------------
    # 2) 建立 handover (create_handover)
    # -------------------------------------------------
    create_handover_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/handoverManager/create_handover"
    handover_payload = {
        "handover_name": "Project A Handover",
        "handover_parameter": {
            "constellation": "TLE_6P_22Sats_29deg_F1",
            "handover_strategy": "MinRange",
            "handover_decision": "Nonpreemptive",
            "gsoProtectionMode": "false",
            "beams_per_satellite": "28",
            "frequencies_per_satellite": "10",
            "cell_ut": "35Cell_300UT",
            "simStartTime": "0",
            "simEndTime": "0",
            "cell_topology_mode": "dynamic",
            "reuse_factor": "None"
        },
        "f_user_uid": user_uid
    }
    resp_create_handover = requests.post(create_handover_url, json=handover_payload)
    print_response("2) Create Handover", resp_create_handover)

    # 從回傳中取得 handover_uid
    handover_uid = None
    if resp_create_handover.status_code == 200:
        res_json = resp_create_handover.json()
        if res_json.get("status") == "success" and "data" in res_json:
            handover_uid = res_json["data"].get("handover_uid")

    if not handover_uid:
        print("無法取得 handover_uid，後續流程無法執行。")
        return

    # -------------------------------------------------
    # 3) 執行 handover 模擬 (run_handover_sim_job)
    # -------------------------------------------------
    run_handover_sim_job_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/handoverSimJobManager/run_handover_sim_job"
    run_handover_payload = {
        "handover_uid": handover_uid
    }
    resp_run_handover = requests.post(run_handover_sim_job_url, json=run_handover_payload)
    print_response("3) Run Handover Sim Job", resp_run_handover)

    # 可能需要等一下讓後端完成或產出檔案
    time.sleep(20)

    # -------------------------------------------------
    # 4) 下載模擬結果 (download_handover_sim_result)
    # -------------------------------------------------
    download_handover_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/handoverSimJobManager/download_handover_sim_result"
    download_handover_payload = {
        "handover_uid": handover_uid
    }
    resp_download_handover = requests.post(download_handover_url, json=download_handover_payload)
    print_response("4) Download Handover Sim Result", resp_download_handover)

    # -------------------------------------------------
    # 5) 刪除模擬結果 (delete_handover_sim_result)
    # -------------------------------------------------
    delete_handover_result_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/handoverSimJobManager/delete_handover_sim_result"
    delete_handover_result_payload = {
        "handover_uid": handover_uid
    }
    resp_delete_handover_result = requests.post(delete_handover_result_url, json=delete_handover_result_payload)
    print_response("5) Delete Handover Sim Result", resp_delete_handover_result)

    # -------------------------------------------------
    # 6) 刪除 handover (delete_handover)
    # -------------------------------------------------
    delete_handover_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/handoverManager/delete_handover"
    delete_handover_payload = {
        "handover_uid": handover_uid
    }
    resp_delete_handover = requests.post(delete_handover_url, json=delete_handover_payload)
    print_response("6) Delete Handover", resp_delete_handover)

    # -------------------------------------------------
    # 7) 刪除使用者 (delete_user)
    # -------------------------------------------------
    delete_user_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/userManager/delete_user"
    delete_user_payload = {
        "user_uid": user_uid
    }
    resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    print_response("7) Delete User", resp_delete_user)


if __name__ == "__main__":
    main()
