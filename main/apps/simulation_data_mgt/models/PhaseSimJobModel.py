from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.PhaseModel import Phase

class PhaseSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    phaseSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    phaseSimJob_process_id = models.IntegerField(null=True, blank=True)
    phaseSimJob_start_time = models.DateTimeField(default=timezone.now)
    phaseSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_phase_uid = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        to_field='phase_uid',
        db_column='f_phase_uid'
    )

    class Meta:
        db_table = 'phaseSimJob'
