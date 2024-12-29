from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User


class Phase(models.Model):
    id = models.AutoField(primary_key=True)
    phase_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    phase_name = models.CharField(max_length=255)
    phase_parameter = models.JSONField()
    phase_status = models.CharField(max_length=50)
    phase_data_path = models.CharField(max_length=255)
    phase_create_time = models.DateTimeField(default=timezone.now)
    phase_update_time = models.DateTimeField(auto_now=True)
    phase_simulation_result = models.JSONField(null=True, blank=True)

    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'  # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'phase'

    def save(self, *args, **kwargs):
        # 如果是新建或 data_path 為空，就自動生成
        if not self.id or not self.phase_data_path:
            self.phase_data_path = f"phase/{{self.f_user_uid.user_uid}}/{{self.phase_uid}}"
        super().save(*args, **kwargs)
