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
    #   2) meta_data_mgt.connectedDurationManager.create_connectedDuration
    #   3) simulation_data_mgt.connectedDurationSimJobManager.run_connectedDuration_sim_job
    #   4) simulation_data_mgt.connectedDurationSimJobManager.download_connectedDuration_sim_result
    #   5) simulation_data_mgt.connectedDurationSimJobManager.delete_connectedDuration_sim_result
    #   6) meta_data_mgt.connectedDurationManager.delete_connectedDuration
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

    # 2) 建立 connectedDuration (create_connectedDuration)
    create_cd_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/connectedDurationManager/create_connectedDuration"
    cd_payload = {
        "connectedDuration_name": "Project A ConnectedDuration",
        "connectedDuration_parameter": {
            "TLE_inputFileName":"TLE_12P_22Sats_29deg_F7.txt",
            "stationLatitude":"26.0",
            "stationLongitude":"122.0",
            "stationAltitude":"101"},
        "f_user_uid": user_uid
    }
    resp_create_cd = requests.post(create_cd_url, json=cd_payload)
    print_response("2) Create ConnectedDuration", resp_create_cd)

    connectedDuration_uid = None
    if resp_create_cd.status_code == 200:
        res_json = resp_create_cd.json()
        if res_json.get("status") == "success" and "data" in res_json:
            connectedDuration_uid = res_json["data"].get("connectedDuration_uid")

    if not connectedDuration_uid:
        print(f"無法取得 connectedDuration_uid，後續流程無法執行。")
        return

    # 3) 執行 connectedDuration 模擬 (run_connectedDuration_sim_job)
    run_cd_sim_job_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/connectedDurationSimJobManager/run_connectedDuration_sim_job"
    run_cd_payload = {
        "connectedDuration_uid": connectedDuration_uid
    }
    resp_run_cd = requests.post(run_cd_sim_job_url, json=run_cd_payload)
    print_response("3) Run ConnectedDuration Sim Job", resp_run_cd)

    time.sleep(20)  # 後端執行需要等待時間，可自行調整

    # 4) 下載模擬結果 (download_connectedDuration_sim_result)
    # download_cd_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/connectedDurationSimJobManager/download_connectedDuration_sim_result"
    # download_cd_payload = {
    #     "connectedDuration_uid": connectedDuration_uid
    # }
    # resp_download_cd = requests.post(download_cd_url, json=download_cd_payload)
    # print_response("4) Download ConnectedDuration Sim Result", resp_download_cd)

    # # 5) 刪除模擬結果 (delete_connectedDuration_sim_result)
    # delete_cd_result_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/connectedDurationSimJobManager/delete_connectedDuration_sim_result"
    # delete_cd_result_payload = {
    #     "connectedDuration_uid": connectedDuration_uid
    # }
    # resp_delete_cd_result = requests.post(delete_cd_result_url, json=delete_cd_result_payload)
    # print_response("5) Delete ConnectedDuration Sim Result", resp_delete_cd_result)

    # # 6) 刪除 connectedDuration (delete_connectedDuration)
    # delete_cd_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/connectedDurationManager/delete_connectedDuration"
    # delete_cd_payload = {
    #     "connectedDuration_uid": connectedDuration_uid
    # }
    # resp_delete_cd = requests.post(delete_cd_url, json=delete_cd_payload)
    # print_response("6) Delete ConnectedDuration", resp_delete_cd)

    # # 7) 刪除使用者 (delete_user)
    # delete_user_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/userManager/delete_user"
    # delete_user_payload = {
    #     "user_uid": user_uid
    # }
    # resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    # print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()
