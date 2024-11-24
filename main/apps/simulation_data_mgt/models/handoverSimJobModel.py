from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.HandoverModel import Handover

class HandoverSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    handoverSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    handoverSimJob_process_id = models.IntegerField(null=True, blank=True)
    handoverSimJob_start_time = models.DateTimeField(default=timezone.now)
    handoverSimJob_end_time = models.DateTimeField(null=True, blank=True)
    f_handover_uid = models.ForeignKey(
        Handover,
        on_delete=models.CASCADE,
        to_field='handover_uid',
        db_column='f_handover_uid'
    )

    class Meta:
        db_table = 'handoverSimJob'