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
    # Flow 測試：（7步）對照原先 multiToMulti 流程，把它改成 saveErRouting
    #   1) meta_data_mgt.userManager.create_user
    #   2) meta_data_mgt.saveErRoutingManager.create_saveErRouting
    #   3) simulation_data_mgt.saveErRoutingSimJobManager.run_saveErRouting_sim_job
    #   4) simulation_data_mgt.saveErRoutingSimJobManager.download_saveErRouting_sim_result
    #   5) simulation_data_mgt.saveErRoutingSimJobManager.delete_saveErRouting_sim_result
    #   6) meta_data_mgt.saveErRoutingManager.delete_saveErRouting
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

    # 2) 建立 saveErRouting (create_saveErRouting)
    create_saveErRouting_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/saveErRoutingManager/create_saveErRouting"

    # 假設後端需要這四個欄位：blccVersion, multiPathCriteria, ratio, globalIslPacketDropRate
    # 放在 saveErRouting_parameter 裡
    saveErRouting_payload = {
        "saveErRouting_name": "Project A saveErRouting",
        "saveErRouting_parameter": {
            "blccVersion": "blcc3x22",
            "multiPathCriteria": "blcc",
            "ratio": 0.0001,
            "globalIslPacketDropRate": 0
        },
        "f_user_uid": user_uid
    }
    resp_create_saveErRouting = requests.post(create_saveErRouting_url, json=saveErRouting_payload)
    print_response("2) Create saveErRouting", resp_create_saveErRouting)

    # 從回傳內容提取 saveErRouting_uid
    saveErRouting_uid = None
    if resp_create_saveErRouting.status_code == 200:
        res_json = resp_create_saveErRouting.json()
        if res_json.get("status") == "success" and "data" in res_json:
            saveErRouting_uid = res_json["data"].get("saveErRouting_uid")

    if not saveErRouting_uid:
        print("[Error] 無法取得 saveErRouting_uid，後續流程無法執行。")
        return

    # 3) 執行 saveErRouting 模擬 (run_saveErRouting_sim_job)
    run_saveErRouting_sim_job_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/saveErRoutingSimJobManager/run_saveErRouting_sim_job"
    run_saveErRouting_payload = {
        "saveErRouting_uid": saveErRouting_uid
    }
    resp_run_saveErRouting = requests.post(run_saveErRouting_sim_job_url, json=run_saveErRouting_payload)
    print_response("3) Run saveErRouting Sim Job", resp_run_saveErRouting)

    # 假設後端執行模擬需要等待一段時間
    time.sleep(20)

    # 4) 下載模擬結果 (download_saveErRouting_sim_result)
    download_saveErRouting_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/saveErRoutingSimJobManager/download_saveErRouting_sim_result"
    download_saveErRouting_payload = {
        "saveErRouting_uid": saveErRouting_uid
    }
    resp_download_saveErRouting = requests.post(download_saveErRouting_url, json=download_saveErRouting_payload)
    print_response("4) Download saveErRouting Sim Result", resp_download_saveErRouting)

    # 5) 刪除模擬結果 (delete_saveErRouting_sim_result)
    delete_saveErRouting_result_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/simulation_data_mgt/saveErRoutingSimJobManager/delete_saveErRouting_sim_result"
    delete_saveErRouting_result_payload = {
        "saveErRouting_uid": saveErRouting_uid
    }
    resp_delete_saveErRouting_result = requests.post(delete_saveErRouting_result_url, json=delete_saveErRouting_result_payload)
    print_response("5) Delete saveErRouting Sim Result", resp_delete_saveErRouting_result)

    # 6) 刪除 saveErRouting (delete_saveErRouting)
    delete_saveErRouting_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/saveErRoutingManager/delete_saveErRouting"
    delete_saveErRouting_payload = {
        "saveErRouting_uid": saveErRouting_uid
    }
    resp_delete_saveErRouting = requests.post(delete_saveErRouting_url, json=delete_saveErRouting_payload)
    print_response("6) Delete saveErRouting", resp_delete_saveErRouting)

    # 7) 刪除使用者 (delete_user)
    delete_user_url = f"http://{DJANGO_SERVER}:8000/api/{API_VERSION}/meta_data_mgt/userManager/delete_user"
    delete_user_payload = {
        "user_uid": user_uid
    }
    resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()
