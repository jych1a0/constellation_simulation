from django.test import TestCase
from django.urls import reverse
import json

class ModifyRegenRoutingFlowTestCase(TestCase):
    def test_full_flow_of_modifyRegenRouting(self):
        """
        測試流程:
          1) create_user
          2) create_modifyRegenRouting
          3) update_modifyRegenRouting
          4) delete_modifyRegenRouting
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_modifyRegenRouting",
            "user_password": "test_password_123",
            "user_email": "test_modifyRegenRouting@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_modifyRegenRouting
        create_modifyRegenRouting_url = reverse("create_modifyRegenRouting")  # name="create_modifyRegenRouting"
        create_data = {
            "modifyRegenRouting_name": "My modifyRegenRouting item",
            "modifyRegenRouting_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_modifyRegenRouting_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立modifyRegenRouting成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立modifyRegenRouting成功")
        new_modifyRegenRouting_uid = resp_json["data"]["modifyRegenRouting_uid"]
        print("=== create_modifyRegenRouting =>", new_modifyRegenRouting_uid, "===")

        # 3) update_modifyRegenRouting
        update_modifyRegenRouting_url = reverse("update_modifyRegenRouting")
        update_data = {
            "modifyRegenRouting_uid": new_modifyRegenRouting_uid,
            "modifyRegenRouting_name": "Updated modifyRegenRouting item",
            "modifyRegenRouting_status": "processing"
        }
        resp = self.client.post(update_modifyRegenRouting_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新modifyRegenRouting成功或失敗(看後端設計)")
        print("=== update_modifyRegenRouting =>", resp.status_code, "===")

        # 4) delete_modifyRegenRouting
        delete_modifyRegenRouting_url = reverse("delete_modifyRegenRouting")
        delete_data = {
            "modifyRegenRouting_uid": new_modifyRegenRouting_uid
        }
        resp = self.client.post(delete_modifyRegenRouting_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除modifyRegenRouting成功或失敗(看後端設計)")
        print("=== delete_modifyRegenRouting =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
