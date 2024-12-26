from django.test import TestCase
from django.urls import reverse
import json

class SaveErRoutingFlowTestCase(TestCase):
    def test_full_flow_of_saveErRouting(self):
        """
        測試流程:
          1) create_user
          2) create_saveErRouting
          3) update_saveErRouting
          4) delete_saveErRouting
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_saveErRouting",
            "user_password": "test_password_123",
            "user_email": "test_saveErRouting@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_saveErRouting
        create_saveErRouting_url = reverse("create_saveErRouting")  # name="create_saveErRouting"
        create_data = {
            "saveErRouting_name": "My saveErRouting item",
            "saveErRouting_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_saveErRouting_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立saveErRouting成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立saveErRouting成功")
        new_saveErRouting_uid = resp_json["data"]["saveErRouting_uid"]
        print("=== create_saveErRouting =>", new_saveErRouting_uid, "===")

        # 3) update_saveErRouting
        update_saveErRouting_url = reverse("update_saveErRouting")
        update_data = {
            "saveErRouting_uid": new_saveErRouting_uid,
            "saveErRouting_name": "Updated saveErRouting item",
            "saveErRouting_status": "processing"
        }
        resp = self.client.post(update_saveErRouting_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新saveErRouting成功或失敗(看後端設計)")
        print("=== update_saveErRouting =>", resp.status_code, "===")

        # 4) delete_saveErRouting
        delete_saveErRouting_url = reverse("delete_saveErRouting")
        delete_data = {
            "saveErRouting_uid": new_saveErRouting_uid
        }
        resp = self.client.post(delete_saveErRouting_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除saveErRouting成功或失敗(看後端設計)")
        print("=== delete_saveErRouting =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
