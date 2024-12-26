from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.IslHoppingModel import IslHopping

class IslHoppingSimJob(models.Model):
    id = models.AutoField(primary_key=True)
    islHoppingSimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    islHoppingSimJob_process_id = models.IntegerField(null=True, blank=True)
    islHoppingSimJob_start_time = models.DateTimeField(default=timezone.now)
    islHoppingSimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_islHopping_uid = models.ForeignKey(
        IslHopping,
        on_delete=models.CASCADE,
        to_field='islHopping_uid',
        db_column='f_islHopping_uid'
    )

    class Meta:
        db_table = 'islHoppingSimJob'
