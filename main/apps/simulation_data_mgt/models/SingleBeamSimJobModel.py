from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.SingleBeamModel import SingleBeam

class SingleBeamSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    singleBeamSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    singleBeamSimJob_process_id = models.IntegerField(null=True, blank=True)
    singleBeamSimJob_start_time = models.DateTimeField(default=timezone.now)
    singleBeamSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_singleBeam_uid = models.ForeignKey(
        SingleBeam,
        on_delete=models.CASCADE,
        to_field='singleBeam_uid',
        db_column='f_singleBeam_uid'
    )

    class Meta:
        db_table = 'singleBeamSimJob'
