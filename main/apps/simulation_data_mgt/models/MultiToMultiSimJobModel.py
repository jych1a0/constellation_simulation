from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.MultiToMultiModel import MultiToMulti

class MultiToMultiSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    multiToMultiSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    multiToMultiSimJob_process_id = models.IntegerField(null=True, blank=True)
    multiToMultiSimJob_start_time = models.DateTimeField(default=timezone.now)
    multiToMultiSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_multiToMulti_uid = models.ForeignKey(
        MultiToMulti,
        on_delete=models.CASCADE,
        to_field='multiToMulti_uid',
        db_column='f_multiToMulti_uid'
    )

    class Meta:
        db_table = 'multiToMultiSimJob'
