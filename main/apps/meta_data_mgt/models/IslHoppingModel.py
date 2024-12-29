from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User


class IslHopping(models.Model):
    id = models.AutoField(primary_key=True)
    islHopping_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    islHopping_name = models.CharField(max_length=255)
    islHopping_parameter = models.JSONField()
    islHopping_status = models.CharField(max_length=50)
    islHopping_data_path = models.CharField(max_length=255)
    islHopping_create_time = models.DateTimeField(default=timezone.now)
    islHopping_update_time = models.DateTimeField(auto_now=True)
    islHopping_simulation_result = models.JSONField(null=True, blank=True)

    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'  # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'islHopping'

    def save(self, *args, **kwargs):
        # 如果是新建或 data_path 為空，就自動生成
        if not self.id or not self.islHopping_data_path:
            self.islHopping_data_path = f"islHopping/{{self.f_user_uid.user_uid}}/{{self.islHopping_uid}}"
        super().save(*args, **kwargs)
