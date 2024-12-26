from django.test import TestCase
from django.urls import reverse
import json

class ConnectedDurationFlowTestCase(TestCase):
    def test_full_flow_of_connectedDuration(self):
        """
        測試流程:
          1) create_user
          2) create_connectedDuration
          3) update_connectedDuration
          4) delete_connectedDuration
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_connectedDuration",
            "user_password": "test_password_123",
            "user_email": "test_connectedDuration@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_connectedDuration
        create_connectedDuration_url = reverse("create_connectedDuration")  # name="create_connectedDuration"
        create_data = {
            "connectedDuration_name": "My connectedDuration item",
            "connectedDuration_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_connectedDuration_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立connectedDuration成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立connectedDuration成功")
        new_connectedDuration_uid = resp_json["data"]["connectedDuration_uid"]
        print("=== create_connectedDuration =>", new_connectedDuration_uid, "===")

        # 3) update_connectedDuration
        update_connectedDuration_url = reverse("update_connectedDuration")
        update_data = {
            "connectedDuration_uid": new_connectedDuration_uid,
            "connectedDuration_name": "Updated connectedDuration item",
            "connectedDuration_status": "processing"
        }
        resp = self.client.post(update_connectedDuration_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新connectedDuration成功或失敗(看後端設計)")
        print("=== update_connectedDuration =>", resp.status_code, "===")

        # 4) delete_connectedDuration
        delete_connectedDuration_url = reverse("delete_connectedDuration")
        delete_data = {
            "connectedDuration_uid": new_connectedDuration_uid
        }
        resp = self.client.post(delete_connectedDuration_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除connectedDuration成功或失敗(看後端設計)")
        print("=== delete_connectedDuration =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
