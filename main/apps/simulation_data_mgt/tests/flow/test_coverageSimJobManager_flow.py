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
    #   2) meta_data_mgt.coverageManager.create_coverage
    #   3) simulation_data_mgt.coverageSimJobManager.run_coverage_sim_job
    #   4) simulation_data_mgt.coverageSimJobManager.download_coverage_sim_result
    #   5) simulation_data_mgt.coverageSimJobManager.delete_coverage_sim_result
    #   6) meta_data_mgt.coverageManager.delete_coverage
    #   7) meta_data_mgt.userManager.delete_user
    # ---------------------------------------------------------------------

    # 1) 建立使用者 (create_user)
    create_user_url = f"http://127.0.0.1:8000/api/1.0/meta_data_mgt/userManager/create_user"
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

    # 2) 建立 coverage (create_coverage)
    create_coverage_url = f"http://127.0.0.1:8000/api/1.0/meta_data_mgt/coverageManager/create_coverage"
    coverage_payload = {
        "coverage_name": "Project A Coverage",
        "coverage_parameter": {
            "TLE_inputFileName": "TLE_6P_22Sats_29deg_F1.txt",
            "minLatitude": "-50",
            "maxLatitude": "50",
            "leastSatCount": "3",
            "simStartTime": "0",
            "simEndTime": "600",
        },
        "f_user_uid": user_uid
    }
    resp_create_coverage = requests.post(create_coverage_url, json=coverage_payload)
    print_response("2) Create Coverage", resp_create_coverage)

    coverage_uid = None
    if resp_create_coverage.status_code == 200:
        res_json = resp_create_coverage.json()
        if res_json.get("status") == "success" and "data" in res_json:
            coverage_uid = res_json["data"].get("coverage_uid")

    if not coverage_uid:
        print(f"無法取得 coverage_uid，後續流程無法執行。")
        return

    # 3) 執行 coverage 模擬 (run_coverage_sim_job)
    run_coverage_sim_job_url = f"http://127.0.0.1:8000/api/1.0/simulation_data_mgt/coverageSimJobManager/run_coverage_sim_job"
    run_coverage_payload = {
        "coverage_uid": coverage_uid
    }
    resp_run_coverage = requests.post(run_coverage_sim_job_url, json=run_coverage_payload)
    print_response("3) Run Coverage Sim Job", resp_run_coverage)

    time.sleep(10)  # 後端執行需要等待時間，可自行調整

    # 4) 下載模擬結果 (download_coverage_sim_result)
    download_coverage_url = f"http://127.0.0.1:8000/api/1.0/simulation_data_mgt/coverageSimJobManager/download_coverage_sim_result"
    download_coverage_payload = {
        "coverage_uid": coverage_uid
    }
    resp_download_coverage = requests.post(download_coverage_url, json=download_coverage_payload)
    print_response("4) Download Coverage Sim Result", resp_download_coverage)

    # 5) 刪除模擬結果 (delete_coverage_sim_result)
    delete_coverage_result_url = f"http://127.0.0.1:8000/api/1.0/simulation_data_mgt/coverageSimJobManager/delete_coverage_sim_result"
    delete_coverage_result_payload = {
        "coverage_uid": coverage_uid
    }
    resp_delete_coverage_result = requests.post(delete_coverage_result_url, json=delete_coverage_result_payload)
    print_response("5) Delete Coverage Sim Result", resp_delete_coverage_result)

    # 6) 刪除 coverage (delete_coverage)
    delete_coverage_url = f"http://127.0.0.1:8000/api/1.0/meta_data_mgt/coverageManager/delete_coverage"
    delete_coverage_payload = {
        "coverage_uid": coverage_uid
    }
    resp_delete_coverage = requests.post(delete_coverage_url, json=delete_coverage_payload)
    print_response("6) Delete Coverage", resp_delete_coverage)

    # 7) 刪除使用者 (delete_user)
    delete_user_url = f"http://127.0.0.1:8000/api/1.0/meta_data_mgt/userManager/delete_user"
    delete_user_payload = {
        "user_uid": user_uid
    }
    resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()
