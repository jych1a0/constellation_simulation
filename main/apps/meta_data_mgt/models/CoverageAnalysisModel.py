from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User

class CoverageAnalysis(models.Model):
    id = models.AutoField(primary_key=True)
    coverage_analysis_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    coverage_analysis_name = models.CharField(max_length=255)
    coverage_analysis_parameter = models.JSONField()  # 使用 JSONField 來儲存 JSON 格式的參數
    coverage_analysis_status = models.CharField(max_length=50)
    coverage_analysis_data_path = models.CharField(max_length=255)
    coverage_analysis_create_time = models.DateTimeField(default=timezone.now)
    coverage_analysis_update_time = models.DateTimeField(auto_now=True)  # 自動更新時間
    coverage_analysis_simulation_result = models.JSONField(null=True, blank=True)  # 新增的欄位
    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'  # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = 'coverage_analysis'  # 指定資料表名稱

    def save(self, *args, **kwargs):
        # 如果是新建實例（沒有 id）或 coverage_analysis_data_path 為空
        if not self.id or not self.coverage_analysis_data_path:
            # 在儲存前自動生成 coverage_analysis_data_path
            self.coverage_analysis_data_path = f"coverage_analysis/{self.f_user_uid.user_uid}/{self.coverage_analysis_uid}"
        super().save(*args, **kwargs)
