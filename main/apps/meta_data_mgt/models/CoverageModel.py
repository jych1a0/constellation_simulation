from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User

class Coverage(models.Model):
    """
    覆蓋範圍資料模型，記錄每個使用者的模擬參數、狀態、結果與資料路徑。
    """
    id = models.AutoField(primary_key=True)
    coverage_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    coverage_name = models.CharField(max_length=255)
    coverage_parameter = models.JSONField()
    coverage_status = models.CharField(max_length=50)
    coverage_data_path = models.CharField(max_length=255)
    coverage_create_time = models.DateTimeField(default=timezone.now)
    coverage_update_time = models.DateTimeField(auto_now=True)
    coverage_simulation_result = models.JSONField(null=True, blank=True)

    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'  # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'coverage'

    def save(self, *args, **kwargs):
        # 如果是新建或 data_path 為空，就自動生成
        if not self.id or not self.coverage_data_path:
            self.coverage_data_path = f"coverage/{self.f_user_uid.user_uid}/{self.coverage_uid}"
        super().save(*args, **kwargs)
