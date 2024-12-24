from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.TestSatelliteModel import TestSatellite

class TestSatelliteSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    test_satellite_sim_job_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    test_satellite_sim_job_process_id = models.IntegerField(null=True, blank=True)
    test_satellite_sim_job_start_time = models.DateTimeField(default=timezone.now)
    test_satellite_sim_job_end_time = models.DateTimeField(null=True, blank=True)
    test_satellite_sim_job_result = models.JSONField(null=True, blank=True)

    f_test_satellite = models.ForeignKey(
        TestSatellite,
        on_delete=models.CASCADE,
        to_field='test_satellite_uid',
        db_column='f_test_satellite'
    )

    class Meta:
        db_table = 'TestSatelliteSimJob'

    def __str__(self):
        return f'TestSatelliteSimJob(uid={{self.test_satellite_sim_job_uid}})'
