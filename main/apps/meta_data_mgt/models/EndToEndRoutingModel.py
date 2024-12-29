from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User


class EndToEndRouting(models.Model):
    id = models.AutoField(primary_key=True)
    endToEndRouting_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    endToEndRouting_name = models.CharField(max_length=255)
    endToEndRouting_parameter = models.JSONField()
    endToEndRouting_status = models.CharField(max_length=50)
    endToEndRouting_data_path = models.CharField(max_length=255)
    endToEndRouting_create_time = models.DateTimeField(default=timezone.now)
    endToEndRouting_update_time = models.DateTimeField(auto_now=True)
    endToEndRouting_simulation_result = models.JSONField(null=True, blank=True)

    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'  # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'endToEndRouting'

    def save(self, *args, **kwargs):
        # 如果是新建或 data_path 為空，就自動生成
        if not self.id or not self.endToEndRouting_data_path:
            self.endToEndRouting_data_path = f"endToEndRouting/{self.f_user_uid.user_uid}/{self.endToEndRouting_uid}"
        super().save(*args, **kwargs)
