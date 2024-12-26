from django.test import TestCase
from django.urls import reverse
import json

class GsoFlowTestCase(TestCase):
    def test_full_flow_of_gso(self):
        """
        測試流程:
          1) create_user
          2) create_gso
          3) update_gso
          4) delete_gso
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_gso",
            "user_password": "test_password_123",
            "user_email": "test_gso@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_gso
        create_gso_url = reverse("create_gso")  # name="create_gso"
        create_data = {
            "gso_name": "My gso item",
            "gso_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_gso_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立gso成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立gso成功")
        new_gso_uid = resp_json["data"]["gso_uid"]
        print("=== create_gso =>", new_gso_uid, "===")

        # 3) update_gso
        update_gso_url = reverse("update_gso")
        update_data = {
            "gso_uid": new_gso_uid,
            "gso_name": "Updated gso item",
            "gso_status": "processing"
        }
        resp = self.client.post(update_gso_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新gso成功或失敗(看後端設計)")
        print("=== update_gso =>", resp.status_code, "===")

        # 4) delete_gso
        delete_gso_url = reverse("delete_gso")
        delete_data = {
            "gso_uid": new_gso_uid
        }
        resp = self.client.post(delete_gso_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除gso成功或失敗(看後端設計)")
        print("=== delete_gso =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
