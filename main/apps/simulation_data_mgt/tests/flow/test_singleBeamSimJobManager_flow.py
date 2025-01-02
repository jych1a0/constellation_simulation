#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import random
import time

DJANGO_SERVER = "127.0.0.1"
API_VERSION   = "1.0"

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
    #   2) meta_data_mgt.singleBeamManager.create_singleBeam
    #   3) simulation_data_mgt.singleBeamSimJobManager.run_singleBeam_sim_job
    #   4) simulation_data_mgt.singleBeamSimJobManager.download_singleBeam_sim_result
    #   5) simulation_data_mgt.singleBeamSimJobManager.delete_singleBeam_sim_result
    #   6) meta_data_mgt.singleBeamManager.delete_singleBeam
    #   7) meta_data_mgt.userManager.delete_user
    # ---------------------------------------------------------------------

    # 1) 建立使用者 (create_user)
    create_user_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/userManager/create_user"
    user_payload = {
        "user_name": f"test{random.randint(1000,9999)}",
        "user_password": f"password{random.randint(1000,9999)}",
        "user_email": f"test{random.randint(1000,9999)}@example.com"
    }
    resp_create_user = requests.post(create_user_url, json=user_payload)
    print_response("1) Create User", resp_create_user)

    user_uid = None
    if resp_create_user.status_code == 200:
        res_json = resp_create_user.json()
        if res_json.get("status") == "success" and "data" in res_json:
            user_uid = res_json["data"].get("user_uid")

    if not user_uid:
        print("無法取得 user_uid，後續流程無法執行。")
        return

    # 2) 建立 singleBeam (create_singleBeam)
    create_sb_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/singleBeamManager/create_singleBeam"
    sb_payload = {
        "singleBeam_name": "Project A SingleBeam",
        "singleBeam_parameter": {
            "areaStationLatitudes": "22.6645",
            "areaStationLongitudes": "120.3012",
            "areaStationAltitudes": "0.01",
            "handoverStrategy": "MinRange",
            "handoverDecision": "Nonpreemptive",
            "TLE_inputFileName": "TLE_6P_22Sats_29deg_F1.txt"
    },
        "f_user_uid": user_uid
    }
    resp_create_sb = requests.post(create_sb_url, json=sb_payload)
    print_response("2) Create SingleBeam", resp_create_sb)

    singleBeam_uid = None
    if resp_create_sb.status_code == 200:
        res_json = resp_create_sb.json()
        if res_json.get("status") == "success" and "data" in res_json:
            singleBeam_uid = res_json["data"].get("singleBeam_uid")

    if not singleBeam_uid:
        print(f"無法取得 singleBeam_uid，後續流程無法執行。")
        return

    # 3) 執行 singleBeam 模擬 (run_singleBeam_sim_job)
    run_sb_sim_job_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/singleBeamSimJobManager/run_singleBeam_sim_job"
    run_sb_payload = {
        "singleBeam_uid": singleBeam_uid
    }
    resp_run_sb = requests.post(run_sb_sim_job_url, json=run_sb_payload)
    print_response("3) Run SingleBeam Sim Job", resp_run_sb)

    time.sleep(20)  # 後端執行需要等待時間，可自行調整

    # 4) 下載模擬結果 (download_singleBeam_sim_result)
    download_sb_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/singleBeamSimJobManager/download_singleBeam_sim_result"
    download_sb_payload = {
        "singleBeam_uid": singleBeam_uid
    }
    resp_download_sb = requests.post(download_sb_url, json=download_sb_payload)
    print_response("4) Download SingleBeam Sim Result", resp_download_sb)

    # # 5) 刪除模擬結果 (delete_singleBeam_sim_result)
    # delete_sb_result_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/singleBeamSimJobManager/delete_singleBeam_sim_result"
    # delete_sb_result_payload = {
    #     "singleBeam_uid": singleBeam_uid
    # }
    # resp_delete_sb_result = requests.post(delete_sb_result_url, json=delete_sb_result_payload)
    # print_response("5) Delete SingleBeam Sim Result", resp_delete_sb_result)

    # # 6) 刪除 singleBeam (delete_singleBeam)
    # delete_sb_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/singleBeamManager/delete_singleBeam"
    # delete_sb_payload = {
    #     "singleBeam_uid": singleBeam_uid
    # }
    # resp_delete_sb = requests.post(delete_sb_url, json=delete_sb_payload)
    # print_response("6) Delete SingleBeam", resp_delete_sb)

    # # 7) 刪除使用者 (delete_user)
    # delete_user_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/userManager/delete_user"
    # delete_user_payload = {
    #     "user_uid": user_uid
    # }
    # resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    # print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()
