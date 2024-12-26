from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.SaveErRoutingModel import SaveErRouting

class SaveErRoutingSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    saveErRoutingSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    saveErRoutingSimJob_process_id = models.IntegerField(null=True, blank=True)
    saveErRoutingSimJob_start_time = models.DateTimeField(default=timezone.now)
    saveErRoutingSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_saveErRouting_uid = models.ForeignKey(
        SaveErRouting,
        on_delete=models.CASCADE,
        to_field='saveErRouting_uid',
        db_column='f_saveErRouting_uid'
    )

    class Meta:
        db_table = 'saveErRoutingSimJob'
