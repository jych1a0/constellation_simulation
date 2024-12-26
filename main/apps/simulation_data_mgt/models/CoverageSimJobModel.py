from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.CoverageModel import Coverage

class CoverageSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    coverageSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    coverageSimJob_process_id = models.IntegerField(null=True, blank=True)
    coverageSimJob_start_time = models.DateTimeField(default=timezone.now)
    coverageSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_coverage_uid = models.ForeignKey(
        Coverage,
        on_delete=models.CASCADE,
        to_field='coverage_uid',
        db_column='f_coverage_uid'
    )

    class Meta:
        db_table = 'coverageSimJob'
