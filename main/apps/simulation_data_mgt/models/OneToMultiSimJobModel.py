from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.OneToMultiModel import OneToMulti

class OneToMultiSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    oneToMultiSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    oneToMultiSimJob_process_id = models.IntegerField(null=True, blank=True)
    oneToMultiSimJob_start_time = models.DateTimeField(default=timezone.now)
    oneToMultiSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_oneToMulti_uid = models.ForeignKey(
        OneToMulti,
        on_delete=models.CASCADE,
        to_field='oneToMulti_uid',
        db_column='f_oneToMulti_uid'
    )

    class Meta:
        db_table = 'oneToMultiSimJob'
