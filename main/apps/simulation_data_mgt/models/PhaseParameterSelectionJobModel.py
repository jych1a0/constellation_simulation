# main/apps/simulation_data_mgt/models/PhaseParameterSelectionJobModel.py
from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.PhaseParameterSelectionModel import PhaseParameterSelection

class PhaseParameterSelectionJob(models.Model):
    id = models.AutoField(primary_key=True)
    phaseParameterSelectionJob_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    phaseParameterSelectionJob_process_id = models.IntegerField(null=True, blank=True)
    phaseParameterSelectionJob_start_time = models.DateTimeField(default=timezone.now)
    phaseParameterSelectionJob_end_time = models.DateTimeField(null=True, blank=True)
    
    # 與 PhaseParameterSelection 表建立關聯
    f_phase_parameter_selection_uid = models.ForeignKey(
        PhaseParameterSelection,
        on_delete=models.CASCADE,
        to_field='phase_parameter_selection_uid',
        db_column='f_phase_parameter_selection_uid'
    )

    class Meta:
        db_table = 'phaseParameterSelectionJob'
