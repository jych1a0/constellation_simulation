from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.CoverageAnalysisModel import CoverageAnalysis

class CoverageAnalysisSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    coverageAnalysisSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    coverageAnalysisSimJob_process_id = models.IntegerField(null=True, blank=True)
    coverageAnalysisSimJob_start_time = models.DateTimeField(default=timezone.now)
    coverageAnalysisSimJob_end_time = models.DateTimeField(null=True, blank=True)
    f_coverage_analysis_uid = models.ForeignKey(
        CoverageAnalysis,
        on_delete=models.CASCADE,
        to_field='coverage_analysis_uid',
        db_column='f_coverage_analysis_uid'
    )

    class Meta:
        db_table = 'coverageAnalysisSimJob'
