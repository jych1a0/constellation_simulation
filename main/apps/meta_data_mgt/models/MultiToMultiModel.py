from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User


class MultiToMulti(models.Model):
    id = models.AutoField(primary_key=True)
    multiToMulti_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    multiToMulti_name = models.CharField(max_length=255)
    multiToMulti_parameter = models.JSONField()
    multiToMulti_status = models.CharField(max_length=50)
    multiToMulti_data_path = models.CharField(max_length=255)
    multiToMulti_create_time = models.DateTimeField(default=timezone.now)
    multiToMulti_update_time = models.DateTimeField(auto_now=True)
    multiToMulti_simulation_result = models.JSONField(null=True, blank=True)

    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'  # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'multiToMulti'

    def save(self, *args, **kwargs):
        # 如果是新建或 data_path 為空，就自動生成
        if not self.id or not self.multiToMulti_data_path:
            self.multiToMulti_data_path = f"multiToMulti/{{self.f_user_uid.user_uid}}/{{self.multiToMulti_uid}}"
        super().save(*args, **kwargs)