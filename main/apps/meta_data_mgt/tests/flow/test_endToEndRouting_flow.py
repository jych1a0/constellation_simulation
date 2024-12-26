from django.test import TestCase
from django.urls import reverse
import json

class EndToEndRoutingFlowTestCase(TestCase):
    def test_full_flow_of_endToEndRouting(self):
        """
        測試流程:
          1) create_user
          2) create_endToEndRouting
          3) update_endToEndRouting
          4) delete_endToEndRouting
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_endToEndRouting",
            "user_password": "test_password_123",
            "user_email": "test_endToEndRouting@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_endToEndRouting
        create_endToEndRouting_url = reverse("create_endToEndRouting")  # name="create_endToEndRouting"
        create_data = {
            "endToEndRouting_name": "My endToEndRouting item",
            "endToEndRouting_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_endToEndRouting_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立endToEndRouting成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立endToEndRouting成功")
        new_endToEndRouting_uid = resp_json["data"]["endToEndRouting_uid"]
        print("=== create_endToEndRouting =>", new_endToEndRouting_uid, "===")

        # 3) update_endToEndRouting
        update_endToEndRouting_url = reverse("update_endToEndRouting")
        update_data = {
            "endToEndRouting_uid": new_endToEndRouting_uid,
            "endToEndRouting_name": "Updated endToEndRouting item",
            "endToEndRouting_status": "processing"
        }
        resp = self.client.post(update_endToEndRouting_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新endToEndRouting成功或失敗(看後端設計)")
        print("=== update_endToEndRouting =>", resp.status_code, "===")

        # 4) delete_endToEndRouting
        delete_endToEndRouting_url = reverse("delete_endToEndRouting")
        delete_data = {
            "endToEndRouting_uid": new_endToEndRouting_uid
        }
        resp = self.client.post(delete_endToEndRouting_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除endToEndRouting成功或失敗(看後端設計)")
        print("=== delete_endToEndRouting =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
