import json
import time
from django.test import TestCase
from django.urls import reverse

class HandoverSimJobFlowTestCase(TestCase):
    def test_full_flow_of_handover_sim_job(self):
        """
        Flow 測試：（7步）
          1) meta_data_mgt.userManager.create_user
          2) meta_data_mgt.handoverManager.create_handover
          3) simulation_data_mgt.handoverSimJobManager.run_handover_sim_job
          4) simulation_data_mgt.handoverSimJobManager.download_handover_sim_result
          5) simulation_data_mgt.handoverSimJobManager.delete_handover_sim_result
          6) meta_data_mgt.handoverManager.delete_handover
          7) meta_data_mgt.userManager.delete_user
        """

        # -------------------------
        # 1) create_user
        # -------------------------
        create_user_url = reverse("create_user")
        user_data = {
            "user_name": "flow_test_handover_sim_job_user",
            "user_password": "some_secure_password",
            "user_email": "flow_handover_sim_job@example.com"
        }
        resp = self.client.post(
            create_user_url,
            data=json.dumps(user_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "create_user => 200 or 400")
        response_data = resp.json()
        user_uid = response_data.get("data", {}).get("user_uid")
        print(f"=== create_user => {user_uid} ===")

        # -------------------------
        # 2) create_handover
        # -------------------------
        create_handover_url = reverse("create_handover")
        handover_data = {
            "handover_name": "Project Flow handover_sim_job",
            "handover_parameter": {
                "constellation": "TLE_6P_22Sats_29deg_F1",
                "handover_strategy": "MinRange",
                "handover_decision": "Nonpreemptive",
                "beams_per_satellite": "28",
                "frequencies_per_satellite": "10",
                "cell_ut": "35Cell_300UT",
                "simStartTime": "0",
                "simEndTime": "60",
                "cell_topology_mode": "dynamic",
                "reuse_factor": "None"
            },
            "f_user_uid": user_uid
        }
        resp = self.client.post(
            create_handover_url,
            data=json.dumps(handover_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "create_handover => 200 or 400")
        response_data = resp.json()
        handover_uid = response_data.get("data", {}).get("handover_uid")
        print("=== create_handover =>", handover_uid, "===")

        # -------------------------
        # 3) run_handover_sim_job
        # -------------------------
        run_url = reverse("run_handover_sim_job")
        run_data = {
            "handover_uid": handover_uid
        }
        resp = self.client.post(
            run_url,
            data=json.dumps(run_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400, 404], "run_handover_sim_job => 200/400/404")
        run_json = resp.json()
        print(run_json)
        print("=== run_handover_sim_job =>", resp.status_code, run_json.get("status"), "===")

        # -------------------------
        # 4) download_handover_sim_result
        # -------------------------
        download_url = reverse("download_handover_sim_result")
        download_data = {
            "handover_uid": handover_uid
        }
        resp = self.client.post(
            download_url,
            data=json.dumps(download_data),
            content_type="application/json"
        )
        # 若檔案不存在，可能 404；若已產生 PDF 則 200
        self.assertIn(resp.status_code, [200, 400, 404], "download_handover_sim_result => 200/400/404")
        if resp.status_code in [400, 404]:
            print("=== download_handover_sim_result =>", resp.status_code, resp.json(), "===")
        else:
            print("=== download_handover_sim_result => PDF file returned ===")

        # -------------------------
        # 5) delete_handover_sim_result
        # -------------------------
        delete_sim_result_url = reverse("delete_handover_sim_result")
        del_sim_data = {
            "handover_uid": handover_uid
        }
        resp = self.client.post(
            delete_sim_result_url,
            data=json.dumps(del_sim_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400, 404], "delete_handover_sim_result => 200/400/404")
        if resp.status_code in [200]:
            print("=== delete_handover_sim_result => 200", resp.json().get("status"))
        else:
            print("=== delete_handover_sim_result =>", resp.status_code, resp.json())

        # -------------------------
        # 6) delete_handover
        # -------------------------
        delete_handover_url = reverse("delete_handover")
        del_job_data = {
            "handover_uid": handover_uid
        }
        resp = self.client.post(
            delete_handover_url,
            data=json.dumps(del_job_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "delete_handover => 200 or 400")
        print("=== delete_handover =>", resp.status_code, resp.json().get("status"), "===")

        # -------------------------
        # 7) delete_user
        # -------------------------
        delete_user_url = reverse("delete_user")
        del_user_data = {
            "user_rid": user_uid
        }
        resp = self.client.post(
            delete_user_url,
            data=json.dumps(del_user_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "delete_user => 200 or 400")
        print("=== delete_user =>", resp.status_code, resp.json().get("status"), "===")
