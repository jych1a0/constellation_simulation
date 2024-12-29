from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.EndToEndRoutingModel import EndToEndRouting

class EndToEndRoutingSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    endToEndRoutingSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    endToEndRoutingSimJob_process_id = models.IntegerField(null=True, blank=True)
    endToEndRoutingSimJob_start_time = models.DateTimeField(default=timezone.now)
    endToEndRoutingSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_endToEndRouting_uid = models.ForeignKey(
        EndToEndRouting,
        on_delete=models.CASCADE,
        to_field='endToEndRouting_uid',
        db_column='f_endToEndRouting_uid'
    )

    class Meta:
        db_table = 'endToEndRoutingSimJob'
