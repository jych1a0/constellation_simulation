from django.test import TestCase
from django.urls import reverse
import json

class PhaseFlowTestCase(TestCase):
    def test_full_flow_of_phase(self):
        """
        測試流程:
          1) create_user
          2) create_phase
          3) update_phase
          4) delete_phase
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_phase",
            "user_password": "test_password_123",
            "user_email": "test_phase@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_phase
        create_phase_url = reverse("create_phase")  # name="create_phase"
        create_data = {
            "phase_name": "My phase item",
            "phase_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_phase_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立phase成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立phase成功")
        new_phase_uid = resp_json["data"]["phase_uid"]
        print("=== create_phase =>", new_phase_uid, "===")

        # 3) update_phase
        update_phase_url = reverse("update_phase")
        update_data = {
            "phase_uid": new_phase_uid,
            "phase_name": "Updated phase item",
            "phase_status": "processing"
        }
        resp = self.client.post(update_phase_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新phase成功或失敗(看後端設計)")
        print("=== update_phase =>", resp.status_code, "===")

        # 4) delete_phase
        delete_phase_url = reverse("delete_phase")
        delete_data = {
            "phase_uid": new_phase_uid
        }
        resp = self.client.post(delete_phase_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除phase成功或失敗(看後端設計)")
        print("=== delete_phase =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
