from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.ConnectedDurationModel import ConnectedDuration

class ConnectedDurationSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    connectedDurationSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    connectedDurationSimJob_process_id = models.IntegerField(null=True, blank=True)
    connectedDurationSimJob_start_time = models.DateTimeField(default=timezone.now)
    connectedDurationSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_connectedDuration_uid = models.ForeignKey(
        ConnectedDuration,
        on_delete=models.CASCADE,
        to_field='connectedDuration_uid',
        db_column='f_connectedDuration_uid'
    )

    class Meta:
        db_table = 'connectedDurationSimJob'
