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
    #   2) meta_data_mgt.islHoppingManager.create_islHopping
    #   3) simulation_data_mgt.islHoppingSimJobManager.run_islHopping_sim_job
    #   4) simulation_data_mgt.islHoppingSimJobManager.download_islHopping_sim_result
    #   5) simulation_data_mgt.islHoppingSimJobManager.delete_islHopping_sim_result
    #   6) meta_data_mgt.islHoppingManager.delete_islHopping
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

    # 2) 建立 islHopping (create_islHopping)
    create_islHopping_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/islHoppingManager/create_islHopping"
    islHopping_payload = {
        "islHopping_name": "Project A islHopping",
        "islHopping_parameter": {
            "ISLLinkMethod": "minMaxR",
            "TLE_inputFileName": "TLE_3P_22Sats_29deg_F1.txt",
            "avgISLPerSat": "2.5",
            "degreeConstraint": "3"
            },
        "f_user_uid": user_uid
    }
    resp_create_islHopping = requests.post(create_islHopping_url, json=islHopping_payload)
    print_response("2) Create islHopping", resp_create_islHopping)

    islHopping_uid = None
    if resp_create_islHopping.status_code == 200:
        res_json = resp_create_islHopping.json()
        if res_json.get("status") == "success" and "data" in res_json:
            islHopping_uid = res_json["data"].get("islHopping_uid")

    if not islHopping_uid:
        print(f"無法取得 islHopping_uid，後續流程無法執行。")
        return

    # 3) 執行 islHopping 模擬 (run_islHopping_sim_job)
    run_islHopping_sim_job_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/islHoppingSimJobManager/run_islHopping_sim_job"
    run_islHopping_payload = {
        "islHopping_uid": islHopping_uid
    }
    resp_run_islHopping = requests.post(run_islHopping_sim_job_url, json=run_islHopping_payload)
    print_response("3) Run islHopping Sim Job", resp_run_islHopping)

    time.sleep(20)  # 後端執行需要等待時間，可自行調整

    # 4) 下載模擬結果 (download_islHopping_sim_result)
    # download_islHopping_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/islHoppingSimJobManager/download_islHopping_sim_result"
    # download_islHopping_payload = {
    #     "islHopping_uid": islHopping_uid
    # }
    # resp_download_islHopping = requests.post(download_islHopping_url, json=download_islHopping_payload)
    # print_response("4) Download islHopping Sim Result", resp_download_islHopping)

    # # 5) 刪除模擬結果 (delete_islHopping_sim_result)
    # delete_islHopping_result_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/islHoppingSimJobManager/delete_islHopping_sim_result"
    # delete_islHopping_result_payload = {
    #     "islHopping_uid": islHopping_uid
    # }
    # resp_delete_islHopping_result = requests.post(delete_islHopping_result_url, json=delete_islHopping_result_payload)
    # print_response("5) Delete islHopping Sim Result", resp_delete_islHopping_result)

    # # 6) 刪除 islHopping (delete_islHopping)
    # delete_islHopping_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/islHoppingManager/delete_islHopping"
    # delete_islHopping_payload = {
    #     "islHopping_uid": islHopping_uid
    # }
    # resp_delete_islHopping = requests.post(delete_islHopping_url, json=delete_islHopping_payload)
    # print_response("6) Delete islHopping", resp_delete_islHopping)

    # # 7) 刪除使用者 (delete_user)
    # delete_user_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/userManager/delete_user"
    # delete_user_payload = {
    #     "user_uid": user_uid
    # }
    # resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    # print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()
