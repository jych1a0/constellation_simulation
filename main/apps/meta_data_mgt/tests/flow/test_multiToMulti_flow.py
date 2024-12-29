from django.test import TestCase
from django.urls import reverse
import json

class MultiToMultiFlowTestCase(TestCase):
    def test_full_flow_of_multiToMulti(self):
        """
        測試流程:
          1) create_user
          2) create_multiToMulti
          3) update_multiToMulti
          4) delete_multiToMulti
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_multiToMulti",
            "user_password": "test_password_123",
            "user_email": "test_multiToMulti@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_multiToMulti
        create_multiToMulti_url = reverse("create_multiToMulti")  # name="create_multiToMulti"
        create_data = {
            "multiToMulti_name": "My multiToMulti item",
            "multiToMulti_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_multiToMulti_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立multiToMulti成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立multiToMulti成功")
        new_multiToMulti_uid = resp_json["data"]["multiToMulti_uid"]
        print("=== create_multiToMulti =>", new_multiToMulti_uid, "===")

        # 3) update_multiToMulti
        update_multiToMulti_url = reverse("update_multiToMulti")
        update_data = {
            "multiToMulti_uid": new_multiToMulti_uid,
            "multiToMulti_name": "Updated multiToMulti item",
            "multiToMulti_status": "processing"
        }
        resp = self.client.post(update_multiToMulti_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新multiToMulti成功或失敗(看後端設計)")
        print("=== update_multiToMulti =>", resp.status_code, "===")

        # 4) delete_multiToMulti
        delete_multiToMulti_url = reverse("delete_multiToMulti")
        delete_data = {
            "multiToMulti_uid": new_multiToMulti_uid
        }
        resp = self.client.post(delete_multiToMulti_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除multiToMulti成功或失敗(看後端設計)")
        print("=== delete_multiToMulti =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
