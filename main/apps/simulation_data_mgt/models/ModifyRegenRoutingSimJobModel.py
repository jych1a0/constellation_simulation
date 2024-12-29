from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.ModifyRegenRoutingModel import ModifyRegenRouting

class ModifyRegenRoutingSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    modifyRegenRoutingSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    modifyRegenRoutingSimJob_process_id = models.IntegerField(null=True, blank=True)
    modifyRegenRoutingSimJob_start_time = models.DateTimeField(default=timezone.now)
    modifyRegenRoutingSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_modifyRegenRouting_uid = models.ForeignKey(
        ModifyRegenRouting,
        on_delete=models.CASCADE,
        to_field='modifyRegenRouting_uid',
        db_column='f_modifyRegenRouting_uid'
    )

    class Meta:
        db_table = 'modifyRegenRoutingSimJob'
