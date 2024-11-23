from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User



class Handover(models.Model):
    id = models.AutoField(primary_key=True)
    handover_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    handover_name = models.CharField(max_length=255)
    handover_parameter = models.JSONField()  # 使用 JSONField 來儲存 JSON 格式的參數
    handover_status = models.CharField(max_length=50)
    handover_create_time = models.DateTimeField(default=timezone.now)
    handover_update_time = models.DateTimeField(auto_now=True)  # 自動更新時間
    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'  # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'handover'  # 指定資料表名稱