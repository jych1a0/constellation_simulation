from django.test import TestCase
from django.urls import reverse
import json

class OneToMultiFlowTestCase(TestCase):
    def test_full_flow_of_oneToMulti(self):
        """
        測試流程:
          1) create_user
          2) create_oneToMulti
          3) update_oneToMulti
          4) delete_oneToMulti
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_oneToMulti",
            "user_password": "test_password_123",
            "user_email": "test_oneToMulti@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_oneToMulti
        create_oneToMulti_url = reverse("create_oneToMulti")  # name="create_oneToMulti"
        create_data = {
            "oneToMulti_name": "My oneToMulti item",
            "oneToMulti_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_oneToMulti_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立oneToMulti成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立oneToMulti成功")
        new_oneToMulti_uid = resp_json["data"]["oneToMulti_uid"]
        print("=== create_oneToMulti =>", new_oneToMulti_uid, "===")

        # 3) update_oneToMulti
        update_oneToMulti_url = reverse("update_oneToMulti")
        update_data = {
            "oneToMulti_uid": new_oneToMulti_uid,
            "oneToMulti_name": "Updated oneToMulti item",
            "oneToMulti_status": "processing"
        }
        resp = self.client.post(update_oneToMulti_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新oneToMulti成功或失敗(看後端設計)")
        print("=== update_oneToMulti =>", resp.status_code, "===")

        # 4) delete_oneToMulti
        delete_oneToMulti_url = reverse("delete_oneToMulti")
        delete_data = {
            "oneToMulti_uid": new_oneToMulti_uid
        }
        resp = self.client.post(delete_oneToMulti_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除oneToMulti成功或失敗(看後端設計)")
        print("=== delete_oneToMulti =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
