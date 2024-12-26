from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.ConstellationStrategyModel import ConstellationStrategy

class ConstellationStrategySimJob(models.Model):
    id = models.AutoField(primary_key=True)
    constellationStrategySimJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    constellationStrategySimJob_process_id = models.IntegerField(null=True, blank=True)
    constellationStrategySimJob_start_time = models.DateTimeField(default=timezone.now)
    constellationStrategySimJob_end_time = models.DateTimeField(null=True, blank=True)

    f_constellationStrategy_uid = models.ForeignKey(
        ConstellationStrategy,
        on_delete=models.CASCADE,
        to_field='constellationStrategy_uid',
        db_column='f_constellationStrategy_uid'
    )

    class Meta:
        db_table = 'constellationStrategySimJob'
