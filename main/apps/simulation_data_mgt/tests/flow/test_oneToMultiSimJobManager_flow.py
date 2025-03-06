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
    # Flow 測試：（7步）對照原先 islHopping 流程，把它改成 oneToMulti
    #   1) meta_data_mgt.userManager.create_user
    #   2) meta_data_mgt.oneToMultiManager.create_oneToMulti
    #   3) simulation_data_mgt.oneToMultiSimJobManager.run_oneToMulti_sim_job
    #   4) simulation_data_mgt.oneToMultiSimJobManager.download_oneToMulti_sim_result
    #   5) simulation_data_mgt.oneToMultiSimJobManager.delete_oneToMulti_sim_result
    #   6) meta_data_mgt.oneToMultiManager.delete_oneToMulti
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

    # 2) 建立 oneToMulti (create_oneToMulti)
    create_oneToMulti_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/oneToMultiManager/create_oneToMulti"
    oneToMulti_payload = {
        "oneToMulti_name": "Project A oneToMulti",  # 自行決定一個名稱
        "oneToMulti_parameter": {
            "constellation": "3x22",
            "multiPathCriteria": "throughput",
            "ratio": 0.0001
        },
        "f_user_uid": user_uid
    }
    resp_create_oneToMulti = requests.post(create_oneToMulti_url, json=oneToMulti_payload)
    print_response("2) Create oneToMulti", resp_create_oneToMulti)

    # 從回傳內容提取 oneToMulti_uid
    oneToMulti_uid = None
    if resp_create_oneToMulti.status_code == 200:
        res_json = resp_create_oneToMulti.json()
        if res_json.get("status") == "success" and "data" in res_json:
            oneToMulti_uid = res_json["data"].get("oneToMulti_uid")

    if not oneToMulti_uid:
        print("[Error] 無法取得 oneToMulti_uid，後續流程無法執行。")
        return

    # 3) 執行 oneToMulti 模擬 (run_oneToMulti_sim_job)
    run_oneToMulti_sim_job_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/oneToMultiSimJobManager/run_oneToMulti_sim_job"
    run_oneToMulti_payload = {
        "oneToMulti_uid": oneToMulti_uid
    }
    resp_run_oneToMulti = requests.post(run_oneToMulti_sim_job_url, json=run_oneToMulti_payload)
    print_response("3) Run oneToMulti Sim Job", resp_run_oneToMulti)

    # 假設後端執行模擬需要等待一段時間
    # 視需求調整：可能 10 秒、20 秒或更長
    time.sleep(20)

    # ---------------------------------------------------------------------
    # 4) 下載模擬結果 (download_oneToMulti_sim_result)
    # ---------------------------------------------------------------------
    download_oneToMulti_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/oneToMultiSimJobManager/download_oneToMulti_sim_result"
    download_oneToMulti_payload = {
        "oneToMulti_uid": oneToMulti_uid
    }
    resp_download_oneToMulti = requests.post(download_oneToMulti_url, json=download_oneToMulti_payload)
    print_response("4) Download oneToMulti Sim Result", resp_download_oneToMulti)

    # # ---------------------------------------------------------------------
    # # 5) 刪除模擬結果 (delete_oneToMulti_sim_result)
    # # ---------------------------------------------------------------------
    # delete_oneToMulti_result_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/oneToMultiSimJobManager/delete_oneToMulti_sim_result"
    # delete_oneToMulti_result_payload = {
    #     "oneToMulti_uid": oneToMulti_uid
    # }
    # resp_delete_oneToMulti_result = requests.post(delete_oneToMulti_result_url, json=delete_oneToMulti_result_payload)
    # print_response("5) Delete oneToMulti Sim Result", resp_delete_oneToMulti_result)

    # # ---------------------------------------------------------------------
    # # 6) 刪除 oneToMulti (delete_oneToMulti)
    # # ---------------------------------------------------------------------
    # delete_oneToMulti_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/oneToMultiManager/delete_oneToMulti"
    # delete_oneToMulti_payload = {
    #     "oneToMulti_uid": oneToMulti_uid
    # }
    # resp_delete_oneToMulti = requests.post(delete_oneToMulti_url, json=delete_oneToMulti_payload)
    # print_response("6) Delete oneToMulti", resp_delete_oneToMulti)

    # # ---------------------------------------------------------------------
    # # 7) 刪除使用者 (delete_user)
    # # ---------------------------------------------------------------------
    # delete_user_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/userManager/delete_user"
    # delete_user_payload = {
    #     "user_uid": user_uid
    # }
    # resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    # print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()
