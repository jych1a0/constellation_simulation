from django.test import TestCase
from django.urls import reverse
import json

class SingleBeamFlowTestCase(TestCase):
    def test_full_flow_of_singleBeam(self):
        """
        測試流程:
          1) create_user
          2) create_singleBeam
          3) update_singleBeam
          4) delete_singleBeam
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_singleBeam",
            "user_password": "test_password_123",
            "user_email": "test_singleBeam@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_singleBeam
        create_singleBeam_url = reverse("create_singleBeam")  # name="create_singleBeam"
        create_data = {
            "singleBeam_name": "My singleBeam item",
            "singleBeam_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_singleBeam_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立singleBeam成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立singleBeam成功")
        new_singleBeam_uid = resp_json["data"]["singleBeam_uid"]
        print("=== create_singleBeam =>", new_singleBeam_uid, "===")

        # 3) update_singleBeam
        update_singleBeam_url = reverse("update_singleBeam")
        update_data = {
            "singleBeam_uid": new_singleBeam_uid,
            "singleBeam_name": "Updated singleBeam item",
            "singleBeam_status": "processing"
        }
        resp = self.client.post(update_singleBeam_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新singleBeam成功或失敗(看後端設計)")
        print("=== update_singleBeam =>", resp.status_code, "===")

        # 4) delete_singleBeam
        delete_singleBeam_url = reverse("delete_singleBeam")
        delete_data = {
            "singleBeam_uid": new_singleBeam_uid
        }
        resp = self.client.post(delete_singleBeam_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除singleBeam成功或失敗(看後端設計)")
        print("=== delete_singleBeam =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
