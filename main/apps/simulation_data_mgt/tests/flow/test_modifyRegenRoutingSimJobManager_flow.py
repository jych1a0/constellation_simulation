#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time
import random

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
    #   2) meta_data_mgt.modifyRegenRoutingManager.create_modifyRegenRouting
    #   3) simulation_data_mgt.modifyRegenRoutingSimJobManager.run_modifyRegenRouting_sim_job
    #   4) simulation_data_mgt.modifyRegenRoutingSimJobManager.download_modifyRegenRouting_sim_result
    #   5) simulation_data_mgt.modifyRegenRoutingSimJobManager.delete_modifyRegenRouting_sim_result
    #   6) meta_data_mgt.modifyRegenRoutingManager.delete_modifyRegenRouting
    #   7) meta_data_mgt.userManager.delete_user
    # ---------------------------------------------------------------------

    # (A) 在程式執行當下動態產生隨機使用者資訊
    user_name     = f"test{random.randint(1000,9999)}"
    user_password = f"password{random.randint(1000,9999)}"
    user_email    = f"test{random.randint(1000,9999)}@example.com"

    # -------------------------------------------------
    # 1) 建立使用者 (create_user)
    # -------------------------------------------------
    create_user_url = "http://127.0.0.1:8000/api/1.0/meta_data_mgt/userManager/create_user"
    user_payload = {
        "user_name": user_name,
        "user_password": user_password,
        "user_email": user_email
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

    # -------------------------------------------------
    # 2) 建立 modifyRegenRouting (create_modifyRegenRouting)
    # -------------------------------------------------
    create_mrr_url = "http://127.0.0.1:8000/api/1.0/meta_data_mgt/modifyRegenRoutingManager/create_modifyRegenRouting"
    mrr_payload = {
        "modifyRegenRouting_name": "Project A MRR",
        "modifyRegenRouting_parameter": {
            "Action":"Recover",
            "ISLLinkMethod":"minMaxR",
            "TLE_inputFileName":"TLE_3P_22Sats_29deg_F1.txt",
            "avgISLPerSat":"2.5", 
            "degreeConstraint":"3" 
        },
        "f_user_uid": user_uid
    }
    resp_create_mrr = requests.post(create_mrr_url, json=mrr_payload)
    print_response("2) Create MRR", resp_create_mrr)

    modifyRegenRouting_uid = None
    if resp_create_mrr.status_code == 200:
        res_json = resp_create_mrr.json()
        if res_json.get("status") == "success" and "data" in res_json:
            modifyRegenRouting_uid = res_json["data"].get("modifyRegenRouting_uid")

    if not modifyRegenRouting_uid:
        print("無法取得 modifyRegenRouting_uid，後續流程無法執行。")
        return

    # -------------------------------------------------
    # 3) 執行 modifyRegenRouting 模擬 (run_modifyRegenRouting_sim_job)
    # -------------------------------------------------
    run_mrr_sim_job_url = "http://127.0.0.1:8000/api/1.0/simulation_data_mgt/modifyRegenRoutingSimJobManager/run_modifyRegenRouting_sim_job"
    run_mrr_payload = {
        "modifyRegenRouting_uid": modifyRegenRouting_uid
    }
    resp_run_mrr = requests.post(run_mrr_sim_job_url, json=run_mrr_payload)
    print_response("3) Run ModifyRegenRouting Sim Job", resp_run_mrr)

    # 可能需要等一下讓後端完成或產出檔案
    time.sleep(20)

    # -------------------------------------------------
    # 4) 下載模擬結果 (download_modifyRegenRouting_sim_result)
    # -------------------------------------------------
    # download_mrr_url = "http://127.0.0.1:8000/api/1.0/simulation_data_mgt/modifyRegenRoutingSimJobManager/download_modifyRegenRouting_sim_result"
    # download_mrr_payload = {
    #     "modifyRegenRouting_uid": modifyRegenRouting_uid
    # }
    # resp_download_mrr = requests.post(download_mrr_url, json=download_mrr_payload)
    # print_response("4) Download ModifyRegenRouting Sim Result", resp_download_mrr)

    # -------------------------------------------------
    # 5) 刪除模擬結果 (delete_modifyRegenRouting_sim_result)
    # -------------------------------------------------
    # delete_mrr_result_url = "http://127.0.0.1:8000/api/1.0/simulation_data_mgt/modifyRegenRoutingSimJobManager/delete_modifyRegenRouting_sim_result"
    # delete_mrr_result_payload = {
    #     "modifyRegenRouting_uid": modifyRegenRouting_uid
    # }
    # resp_delete_mrr_result = requests.post(delete_mrr_result_url, json=delete_mrr_result_payload)
    # print_response("5) Delete ModifyRegenRouting Sim Result", resp_delete_mrr_result)

    # -------------------------------------------------
    # 6) 刪除 modifyRegenRouting (delete_modifyRegenRouting)
    # -------------------------------------------------
    # delete_mrr_url = "http://127.0.0.1:8000/api/1.0/meta_data_mgt/modifyRegenRoutingManager/delete_modifyRegenRouting"
    # delete_mrr_payload = {
    #     "modifyRegenRouting_uid": modifyRegenRouting_uid
    # }
    # resp_delete_mrr = requests.post(delete_mrr_url, json=delete_mrr_payload)
    # print_response("6) Delete ModifyRegenRouting", resp_delete_mrr)

    # -------------------------------------------------
    # 7) 刪除使用者 (delete_user)
    # -------------------------------------------------
    # delete_user_url = "http://127.0.0.1:8000/api/1.0/meta_data_mgt/userManager/delete_user"
    # delete_user_payload = {
    #     "user_uid": user_uid
    # }
    # resp_delete_user = requests.post(delete_user_url, json=delete_user_payload)
    # print_response("7) Delete User", resp_delete_user)

if __name__ == "__main__":
    main()
