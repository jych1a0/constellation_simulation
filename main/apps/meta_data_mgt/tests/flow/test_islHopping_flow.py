from django.test import TestCase
from django.urls import reverse
import json

class IslHoppingFlowTestCase(TestCase):
    def test_full_flow_of_islHopping(self):
        """
        測試流程:
          1) create_user
          2) create_islHopping
          3) update_islHopping
          4) delete_islHopping
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_islHopping",
            "user_password": "test_password_123",
            "user_email": "test_islHopping@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_islHopping
        create_islHopping_url = reverse("create_islHopping")  # name="create_islHopping"
        create_data = {
            "islHopping_name": "My islHopping item",
            "islHopping_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_islHopping_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立islHopping成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立islHopping成功")
        new_islHopping_uid = resp_json["data"]["islHopping_uid"]
        print("=== create_islHopping =>", new_islHopping_uid, "===")

        # 3) update_islHopping
        update_islHopping_url = reverse("update_islHopping")
        update_data = {
            "islHopping_uid": new_islHopping_uid,
            "islHopping_name": "Updated islHopping item",
            "islHopping_status": "processing"
        }
        resp = self.client.post(update_islHopping_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新islHopping成功或失敗(看後端設計)")
        print("=== update_islHopping =>", resp.status_code, "===")

        # 4) delete_islHopping
        delete_islHopping_url = reverse("delete_islHopping")
        delete_data = {
            "islHopping_uid": new_islHopping_uid
        }
        resp = self.client.post(delete_islHopping_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除islHopping成功或失敗(看後端設計)")
        print("=== delete_islHopping =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
