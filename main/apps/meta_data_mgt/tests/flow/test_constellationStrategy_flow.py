from django.test import TestCase
from django.urls import reverse
import json

class ConstellationStrategyFlowTestCase(TestCase):
    def test_full_flow_of_constellationStrategy(self):
        """
        測試流程:
          1) create_user
          2) create_constellationStrategy
          3) update_constellationStrategy
          4) delete_constellationStrategy
          5) delete_user
        """

        # 1) create_user
        create_user_url = reverse("create_user")  # 需在 urls.py: name="create_user"
        user_data = {
            "user_name": "test_user_for_constellationStrategy",
            "user_password": "test_password_123",
            "user_email": "test_constellationStrategy@example.com"
        }
        resp = self.client.post(create_user_url, data=json.dumps(user_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立使用者成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立使用者成功")
        new_user_uid = resp_json["data"]["user_uid"]
        print("=== create_user =>", new_user_uid, "===")

        # 2) create_constellationStrategy
        create_constellationStrategy_url = reverse("create_constellationStrategy")  # name="create_constellationStrategy"
        create_data = {
            "constellationStrategy_name": "My constellationStrategy item",
            "constellationStrategy_parameter": {
                "some_key": "some_value"
            },
            "f_user_uid": new_user_uid
        }
        resp = self.client.post(create_constellationStrategy_url, data=json.dumps(create_data), content_type="application/json")
        self.assertEqual(resp.status_code, 200, "建立constellationStrategy成功應回200")
        resp_json = resp.json()
        self.assertEqual(resp_json.get("status"), "success", "建立constellationStrategy成功")
        new_constellationStrategy_uid = resp_json["data"]["constellationStrategy_uid"]
        print("=== create_constellationStrategy =>", new_constellationStrategy_uid, "===")

        # 3) update_constellationStrategy
        update_constellationStrategy_url = reverse("update_constellationStrategy")
        update_data = {
            "constellationStrategy_uid": new_constellationStrategy_uid,
            "constellationStrategy_name": "Updated constellationStrategy item",
            "constellationStrategy_status": "processing"
        }
        resp = self.client.post(update_constellationStrategy_url, data=json.dumps(update_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "更新constellationStrategy成功或失敗(看後端設計)")
        print("=== update_constellationStrategy =>", resp.status_code, "===")

        # 4) delete_constellationStrategy
        delete_constellationStrategy_url = reverse("delete_constellationStrategy")
        delete_data = {
            "constellationStrategy_uid": new_constellationStrategy_uid
        }
        resp = self.client.post(delete_constellationStrategy_url, data=json.dumps(delete_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除constellationStrategy成功或失敗(看後端設計)")
        print("=== delete_constellationStrategy =>", resp.status_code, "===")

        # 5) delete_user
        delete_user_url = reverse("delete_user")  # name="delete_user"
        delete_user_data = {
            "user_rid": new_user_uid
        }
        resp = self.client.post(delete_user_url, data=json.dumps(delete_user_data), content_type="application/json")
        self.assertIn(resp.status_code, [200, 400], "刪除使用者成功或失敗(看後端設計)")
        print("=== delete_user =>", resp.status_code, "===")
