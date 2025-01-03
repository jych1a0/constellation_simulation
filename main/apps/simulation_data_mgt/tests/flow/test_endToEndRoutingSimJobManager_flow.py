#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import random
import time

DJANGO_SERVER = "127.0.0.1"  # 您的 Django 後端 IP 或域名
API_VERSION   = "1.0"       # API 版本

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
    # Flow 測試：（7步）對照原先 saveErRouting 流程，把它改成 endToEndRouting
    #   1) meta_data_mgt.userManager.create_user
    #   2) meta_data_mgt.endToEndRoutingManager.create_endToEndRouting
    #   3) simulation_data_mgt.endToEndRoutingSimJobManager.run_endToEndRouting_sim_job
    #   4) simulation_data_mgt.endToEndRoutingSimJobManager.download_endToEndRouting_sim_result
    #   5) simulation_data_mgt.endToEndRoutingSimJobManager.delete_endToEndRouting_sim_result
    #   6) meta_data_mgt.endToEndRoutingManager.delete_endToEndRouting
    #   7) meta_data_mgt.userManager.delete_user
    # ---------------------------------------------------------------------

    # 1) 建立使用者 (create_user)
    create_user_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/userManager/create_user"
    user_payload = {
        "user_name": f"test{random.randint(1000,9999)}",
        "user_password": f"password{random.randint(1000,9999)}",
        "user_email": f"test{random.randint(1000,9999)}@example.com"
    }
    resp_create_user = requests.post(create_user_url, json=user_payload)
    print_response("1) Create User", resp_create_user)

    # 從回傳內容提取 user_uid
    user_uid = None
    if resp_create_user.status_code == 200:
        res_json = resp_create_user.json()
        if res_json.get("status") == "success" and "data" in res_json:
            user_uid = res_json["data"].get("user_uid")

    if not user_uid:
        print("[Error] 無法取得 user_uid，後續流程無法執行。")
        return

    # 2) 建立 endToEndRouting (create_endToEndRouting)
    create_endToEndRouting_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/endToEndRoutingManager/create_endToEndRouting"

    # 假設後端需要這四個欄位：useCaseVersion, TLE_inputFileName, handoverDecision, beamBandwidth
    # 放在 endToEndRouting_parameter 裡
    endToEndRouting_payload = {
        "endToEndRouting_name": "Project A endToEndRouting",
        "endToEndRouting_parameter": {
            "useCaseVersion": "237UTsSatelliteLB",
            "TLE_inputFileName": "TLE_6P_22Sats_29deg_F1.txt",
            "handoverDecision": "SatelliteLoadBalancing",
            "beamBandwidth": "216000000"
        },
        "f_user_uid": user_uid
    }
    resp_create_endToEndRouting = requests.post(create_endToEndRouting_url, json=endToEndRouting_payload)
    print_response("2) Create endToEndRouting", resp_create_endToEndRouting)

    # 從回傳內容提取 endToEndRouting_uid
    endToEndRouting_uid = None
    if resp_create_endToEndRouting.status_code == 200:
        res_json = resp_create_endToEndRouting.json()
        if res_json.get("status") == "success" and "data" in res_json:
            endToEndRouting_uid = res_json["data"].get("endToEndRouting_uid")

    if not endToEndRouting_uid:
        print("[Error] 無法取得 endToEndRouting_uid，後續流程無法執行。")
        return

    # 3) 執行 endToEndRouting 模擬 (run_endToEndRouting_sim_job)
    run_endToEndRouting_sim_job_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/endToEndRoutingSimJobManager/run_endToEndRouting_sim_job"
    run_endToEndRouting_payload = {
        "endToEndRouting_uid": endToEndRouting_uid
    }
    resp_run_endToEndRouting = requests.post(run_endToEndRouting_sim_job_url, json=run_endToEndRouting_payload)
    print_response("3) Run endToEndRouting Sim Job", resp_run_endToEndRouting)

    # 假設後端執行模擬需要等待一段時間
    time.sleep(20)

    # 4) 下載模擬結果 (download_endToEndRouting_sim_result)
    download_endToEndRouting_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/endToEndRoutingSimJobManager/download_endToEndRouting_sim_result"
    download_endToEndRouting_payload = {
        "endToEndRouting_uid": endToEndRouting_uid
    }
    resp_download_endToEndRouting = requests.post(download_endToEndRouting_url, json=download_endToEndRouting_payload)
    print_response("4) Download endToEndRouting Sim Result", resp_download_endToEndRouting)

    # # 5) 刪除模擬結果 (delete_endToEndRouting_sim_result)
    # delete_endToEndRouting_result_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/endToEndRoutingSimJobManager/delete_endToEndRouting_sim_result"
    # delete_endToEndRouting_result_payload = {
    #     "endToEndRouting_uid": endToEndRouting_uid
    # }
    # resp_delete_endToEndRouting_result = requests.post(delete_endToEndRouting_result_url, json=delete_endToEndRouting_result_payload)
    # print_response("5) Delete endToEndRouting Sim Result", resp_delete_endToEndRouting_result)

    # # 6) 刪除 endToEndRouting (delete_endToEndRouting)
    # delete_endToEndRouting_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/endToEndRoutingManager/delete_endToEndRouting"
    # delete_endToEndRouting_payload = {
    #     "endToEndRouting_uid": endToEndRouting_uid
    # }
    # resp_delete_endToEndRouting = requests.post(delete_endToEndRouting_url, json=delete_endToEndRouting_payload)
    # print_response("6) Delete endToEndRouting", resp_delete_endToEndRouting)

    # # 7) 刪除使用者 (delete_user)
    # delete_user_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/userManager/delete_user"
    # delete_user_payload = {
    #     "user_uid": user_uid
    # }
    # resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    # print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()