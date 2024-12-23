from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.ConnectionTimeSimulationModel import ConnectionTimeSimulation

class ConnectionTimeSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    connectionTimeSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    connectionTimeSimJob_process_id = models.IntegerField(null=True, blank=True)
    connectionTimeSimJob_start_time = models.DateTimeField(default=timezone.now)
    connectionTimeSimJob_end_time = models.DateTimeField(null=True, blank=True)
    # 新增「結果」欄位，作為 JSON 格式
    connectionTimeSimJob_result = models.JSONField(null=True, blank=True)

    # 外鍵關聯到 Connection_Time_Simulation（對應 connection_time_simulation_uid）
    f_connection_time_simulation_uid = models.ForeignKey(
        ConnectionTimeSimulation,
        on_delete=models.CASCADE,
        to_field='connection_time_simulation_uid',
        db_column='f_connection_time_simulation_uid'
    )

    class Meta:
        db_table = 'connectionTimeSimJob'

    def __str__(self):
        return f'ConnectionTimeSimJob(uid={self.connectionTimeSimJob_uid})'
