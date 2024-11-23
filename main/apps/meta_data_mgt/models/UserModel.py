from django.db import models
import uuid
from django.utils import timezone

class User(models.Model):
    id = models.AutoField(primary_key=True)
    user_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    user_name = models.CharField(max_length=255, unique=True)
    user_password = models.CharField(max_length=255)
    user_email = models.EmailField(unique=True)
    create_time = models.DateTimeField(default=timezone.now)
    last_login_time = models.DateTimeField(null=True, blank=True)  # 新增最近登入時間欄位

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.user_name