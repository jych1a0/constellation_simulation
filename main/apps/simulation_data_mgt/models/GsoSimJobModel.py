from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.GsoModel import Gso

class GsoSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    gsoSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    gsoSimJob_process_id = models.IntegerField(null=True, blank=True)
    gsoSimJob_start_time = models.DateTimeField(default=timezone.now)
    gsoSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_gso_uid = models.ForeignKey(
        Gso,
        on_delete=models.CASCADE,
        to_field='gso_uid',
        db_column='f_gso_uid'
    )

    class Meta:
        db_table = 'gsoSimJob'
