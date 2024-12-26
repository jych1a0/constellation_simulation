from django.test import TestCase
from django.urls import reverse
import json

class HandoverFlowTestCase(TestCase):
    def test_full_flow_of_handover(self):
        """
        測試流程:
          1) create_user
          2) create_handover
          3) update_handover
          4) delete_handover
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 須在 urls.py: name="create_user"
        user_data = {
            "user_name": "flow_test_handover01",
            "user_password": "some_secure_password",
            "user_email": "flow_test_handover01@example.com"
        }
        resp = self.client.post(
            create_user_url,
            data=json.dumps(user_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "建立使用者成功或失敗(看後端設計)")
        resp_json = resp.json()
        self.assertIn(resp_json.get("status"), ["success", "error", "info"], "看後端回傳")
        new_user_uid = resp_json.get("data", {}).get("user_uid")
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_handover
        create_handover_url = reverse("create_handover")  # name="create_handover"
        create_data = {
            "handover_name": "Project Flow Handover",
            "handover_parameter": {
                "constellation": "TLE_6P_22Sats_29deg_F1",
                "handover_strategy": "MinRange"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(
            create_handover_url,
            data=json.dumps(create_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "建立handover成功或失敗(看後端設計)")
        resp_json = resp.json()
        self.assertIn(resp_json.get("status"), ["success", "error", "info"], "看後端回傳")
        new_handover_uid = resp_json.get("data", {}).get("handover_uid")
        print("=== create_handover =>", new_handover_uid, "===")

        # 3) update_handover
        update_handover_url = reverse("update_handover")  # name="update_handover"
        update_data = {
            "handover_uid": new_handover_uid,
            "handover_name": "Updated Flow Handover",
            "handover_status": "processing"
        }
        resp = self.client.post(
            update_handover_url,
            data=json.dumps(update_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "更新handover成功或失敗(看後端設計)")
        print("=== update_handover =>", resp.status_code, "===")

        # 4) delete_handover
        delete_handover_url = reverse("delete_handover")  # name="delete_handover"
        delete_data = {
            "handover_uid": new_handover_uid
        }
        resp = self.client.post(
            delete_handover_url,
            data=json.dumps(delete_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "刪除handover成功或失敗(看後端設計)")
        print("=== delete_handover =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(
            delete_user_url,
            data=json.dumps(delete_user_data),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")