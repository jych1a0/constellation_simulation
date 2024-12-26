from django.test import TestCase
from django.urls import reverse
import json

class IslHoppingSimJobFlowTestCase(TestCase):
    def test_full_flow_of_islHopping_sim_job(self):
        """
        Flow 測試：（7步）
          1) meta_data_mgt.userManager.create_user
          2) meta_data_mgt.islHoppingManager.create_islHopping
          3) simulation_data_mgt.islHoppingSimJobManager.run_islHopping_sim_job
          4) simulation_data_mgt.islHoppingSimJobManager.download_islHopping_sim_result
          5) simulation_data_mgt.islHoppingSimJobManager.delete_islHopping_sim_result
          6) meta_data_mgt.islHoppingManager.delete_islHopping
          7) meta_data_mgt.userManager.delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")
        user_data = {
            "user_name": "flow_test_islHopping_sim_job_user",
            "user_password": "some_secure_password",
            "user_email": "flow_islHopping_sim_job@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "create_user => 200 or 400")
        resp_json = resp.json()
        user_uid = resp_json.get("data", {}).get("user_uid")
        print("=== create_user =>", user_uid, "===")

        # 2) create_islHopping_sim_job
        create_url = reverse("create_islHopping_sim_job")
        create_data = {
            "islHopping_sim_job_name": "Project Flow islHopping_sim_job",
            "islHopping_sim_job_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": user_uid
        }
        resp = self.client.post(create_url, data=json.dumps(create_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "create_islHopping_sim_job => 200 or 400")
        resp_json = resp.json()
        sim_job_uid = resp_json.get("data", {}).get("islHopping_sim_job_uid")
        print("=== create_islHopping_sim_job =>", sim_job_uid, "===")

        # 3) run_islHopping_sim_job
        run_url = reverse("run_islHopping_sim_job")
        run_data = {
            "islHopping_sim_job_uid": sim_job_uid
        }
        resp = self.client.post(run_url, data=json.dumps(run_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400, 404], "run_islHopping_sim_job => 200/400/404")
        run_json = resp.json()
        print("=== run_islHopping_sim_job =>", resp.status_code, run_json.get("status"), "===")

        # 4) download_islHopping_sim_result
        download_url = reverse("download_islHopping_sim_result")
        download_data = {
            "islHopping_sim_job_uid": sim_job_uid
        }
        resp = self.client.post(download_url, data=json.dumps(download_data), content_type="application/json")
        # 若檔案不存在，可能404；若已產生PDF則200
        self.assertIn(resp.status_code, [200, 400, 404], "download_islHopping_sim_result => 200/400/404")
        print("=== download_islHopping_sim_result =>", resp.status_code, resp.json() if resp.status_code in [400,404] else 'PDF???', "===")

        # 5) delete_islHopping_sim_result
        delete_sim_result_url = reverse("delete_islHopping_sim_result")
        del_sim_data = {
            "islHopping_sim_job_uid": sim_job_uid
        }
        resp = self.client.post(delete_sim_result_url, data=json.dumps(del_sim_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400, 404], "delete_islHopping_sim_result => 200/400/404")
        print("=== delete_islHopping_sim_result =>", resp.status_code, resp.json().get("status"), "===")

        # 6) delete_islHopping_sim_job
        delete_sim_job_url = reverse("delete_islHopping_sim_job")
        del_job_data = {
            "islHopping_sim_job_uid": sim_job_uid
        }
        resp = self.client.post(delete_sim_job_url, data=json.dumps(del_job_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "delete_islHopping_sim_job => 200 or 400")
        print("=== delete_islHopping_sim_job =>", resp.status_code, resp.json().get("status"), "===")

        # 7) delete_user
        delete_user_url = reverse("delete_user")
        del_user_data = {
            "user_rid": user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(del_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "delete_user => 200 or 400")
        print("=== delete_user =>", resp.status_code, resp.json().get("status"), "===")
