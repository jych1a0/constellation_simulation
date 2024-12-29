from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User


class SaveErRouting(models.Model):
    id = models.AutoField(primary_key=True)
    saveErRouting_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    saveErRouting_name = models.CharField(max_length=255)
    saveErRouting_parameter = models.JSONField()
    saveErRouting_status = models.CharField(max_length=50)
    saveErRouting_data_path = models.CharField(max_length=255)
    saveErRouting_create_time = models.DateTimeField(default=timezone.now)
    saveErRouting_update_time = models.DateTimeField(auto_now=True)
    saveErRouting_simulation_result = models.JSONField(null=True, blank=True)

    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'  # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'saveErRouting'

    def save(self, *args, **kwargs):
        # 如果是新建或 data_path 為空，就自動生成
        if not self.id or not self.saveErRouting_data_path:
            self.saveErRouting_data_path = f"saveErRouting/{self.f_user_uid.user_uid}/{self.saveErRouting_uid}"
        super().save(*args, **kwargs)
