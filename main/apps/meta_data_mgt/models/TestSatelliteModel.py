from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User

class TestSatellite(models.Model):
    id = models.AutoField(primary_key=True)
    test_satellite_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    test_satellite_name = models.CharField(max_length=255)
    test_satellite_parameter = models.JSONField()  # 使用 JSONField 來儲存 JSON 格式的參數
    test_satellite_status = models.CharField(max_length=50)
    test_satellite_data_path = models.CharField(max_length=255)
    test_satellite_create_time = models.DateTimeField(default=timezone.now)
    test_satellite_update_time = models.DateTimeField(auto_now=True)
    test_satellite_result = models.JSONField(null=True, blank=True)

    # 外鍵連至 UserModel
    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',       # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'     # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'TestSatellite'  # 指定資料表名稱

    def save(self, *args, **kwargs):
        # 如果是新建實例（沒有 id）或 test_satellite_data_path 為空，則自動生成
        if not self.id or not self.test_satellite_data_path:
            self.test_satellite_data_path = (
                f"test_satellite/{self.f_user_uid.user_uid}/{self.test_satellite_uid}"
            )
        super().save(*args, **kwargs)
