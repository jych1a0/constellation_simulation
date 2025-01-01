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
    #   2) meta_data_mgt.constellationStrategyManager.create_constellationStrategy
    #   3) simulation_data_mgt.constellationStrategySimJobManager.run_constellationStrategy_sim_job
    #   4) simulation_data_mgt.constellationStrategySimJobManager.download_constellationStrategy_sim_result
    #   5) simulation_data_mgt.constellationStrategySimJobManager.delete_constellationStrategy_sim_result
    #   6) meta_data_mgt.constellationStrategyManager.delete_constellationStrategy
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

    # 2) 建立 constellationStrategy (create_constellationStrategy)
    create_cs_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/constellationStrategyManager/create_constellationStrategy"
    cs_payload = {
        "constellationStrategy_name": "Project A ConstellationStrategy",
        "constellationStrategy_parameter": {
            "observerId":"102",
            "TLE_inputFileName":"TLE_12P_22Sats_29deg_F7.txt",
            "ISLLinkMethod":"minAERRange"},
        "f_user_uid": user_uid
    }
    resp_create_cs = requests.post(create_cs_url, json=cs_payload)
    print_response("2) Create ConstellationStrategy", resp_create_cs)

    constellationStrategy_uid = None
    if resp_create_cs.status_code == 200:
        res_json = resp_create_cs.json()
        if res_json.get("status") == "success" and "data" in res_json:
            constellationStrategy_uid = res_json["data"].get("constellationStrategy_uid")

    if not constellationStrategy_uid:
        print(f"無法取得 constellationStrategy_uid，後續流程無法執行。")
        return

    # 3) 執行 constellationStrategy 模擬 (run_constellationStrategy_sim_job)
    run_cs_sim_job_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/constellationStrategySimJobManager/run_constellationStrategy_sim_job"
    run_cs_payload = {
        "constellationStrategy_uid": constellationStrategy_uid
    }
    resp_run_cs = requests.post(run_cs_sim_job_url, json=run_cs_payload)
    print_response("3) Run ConstellationStrategy Sim Job", resp_run_cs)

    time.sleep(20)  # 後端執行需要等待時間，可自行調整

    # 4) 下載模擬結果 (download_constellationStrategy_sim_result)
    # download_cs_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/constellationStrategySimJobManager/download_constellationStrategy_sim_result"
    # download_cs_payload = {
    #     "constellationStrategy_uid": constellationStrategy_uid
    # }
    # resp_download_cs = requests.post(download_cs_url, json=download_cs_payload)
    # print_response("4) Download ConstellationStrategy Sim Result", resp_download_cs)

    # # 5) 刪除模擬結果 (delete_constellationStrategy_sim_result)
    # delete_cs_result_url = f"http://127.0.0.1:8000/api/{API_VERSION}/simulation_data_mgt/constellationStrategySimJobManager/delete_constellationStrategy_sim_result"
    # delete_cs_result_payload = {
    #     "constellationStrategy_uid": constellationStrategy_uid
    # }
    # resp_delete_cs_result = requests.post(delete_cs_result_url, json=delete_cs_result_payload)
    # print_response("5) Delete ConstellationStrategy Sim Result", resp_delete_cs_result)

    # # 6) 刪除 constellationStrategy (delete_constellationStrategy)
    # delete_cs_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/constellationStrategyManager/delete_constellationStrategy"
    # delete_cs_payload = {
    #     "constellationStrategy_uid": constellationStrategy_uid
    # }
    # resp_delete_cs = requests.post(delete_cs_url, json=delete_cs_payload)
    # print_response("6) Delete ConstellationStrategy", resp_delete_cs)

    # # 7) 刪除使用者 (delete_user)
    # delete_user_url = f"http://127.0.0.1:8000/api/{API_VERSION}/meta_data_mgt/userManager/delete_user"
    # delete_user_payload = {
    #     "user_uid": user_uid
    # }
    # resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    # print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()
