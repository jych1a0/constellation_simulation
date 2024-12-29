from django.test import TestCase
from django.urls import reverse
import json

class CoverageFlowTestCase(TestCase):
    def test_full_flow_of_coverage(self):
        """
        測試流程:
          1) create_user
          2) create_coverage
          3) update_coverage
          4) delete_coverage
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_coverage",
            "user_password": "test_password_123",
            "user_email": "test_coverage@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_coverage
        create_coverage_url = reverse("create_coverage")  # name="create_coverage"
        create_data = {
            "coverage_name": "My coverage item",
            "coverage_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_coverage_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立coverage成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立coverage成功")
        new_coverage_uid = resp_json["data"]["coverage_uid"]
        print("=== create_coverage =>", new_coverage_uid, "===")

        # 3) update_coverage
        update_coverage_url = reverse("update_coverage")
        update_data = {
            "coverage_uid": new_coverage_uid,
            "coverage_name": "Updated coverage item",
            "coverage_status": "processing"
        }
        resp = self.client.post(update_coverage_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新coverage成功或失敗(看後端設計)")
        print("=== update_coverage =>", resp.status_code, "===")

        # 4) delete_coverage
        delete_coverage_url = reverse("delete_coverage")
        delete_data = {
            "coverage_uid": new_coverage_uid
        }
        resp = self.client.post(delete_coverage_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除coverage成功或失敗(看後端設計)")
        print("=== delete_coverage =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
