# -*- coding: utf-8 -*-
"""
定義 simulation_data_mgt 應用的 API 路由，負責將 HTTP 請求導向對應的 view 處理函式。
"""
from django.urls import path
from main.apps.simulation_data_mgt.actors.handoverSimJobManager import handoverSimJobManager
from main.apps.simulation_data_mgt.actors.coverageSimJobManager import coverageSimJobManager
from main.apps.simulation_data_mgt.actors.connectedDurationSimJobManager import connectedDurationSimJobManager
from main.apps.simulation_data_mgt.actors.phaseSimJobManager import phaseSimJobManager
from main.apps.simulation_data_mgt.actors.constellationStrategySimJobManager import constellationStrategySimJobManager
from main.apps.simulation_data_mgt.actors.islHoppingSimJobManager import islHoppingSimJobManager
from main.apps.simulation_data_mgt.actors.modifyRegenRoutingSimJobManager import modifyRegenRoutingSimJobManager
from main.apps.simulation_data_mgt.actors.oneToMultiSimJobManager import oneToMultiSimJobManager
from main.apps.simulation_data_mgt.actors.multiToMultiSimJobManager import multiToMultiSimJobManager
from main.apps.simulation_data_mgt.actors.saveErRoutingSimJobManager import saveErRoutingSimJobManager
from main.apps.simulation_data_mgt.actors.endToEndRoutingSimJobManager import endToEndRoutingSimJobManager
from main.apps.simulation_data_mgt.actors.singleBeamSimJobManager import singleBeamSimJobManager
from main.apps.simulation_data_mgt.actors.gsoSimJobManager import gsoSimJobManager

urlpatterns = [
    path('simulation_data_mgt/handoverSimJobManager/run_handover_sim_job',
         handoverSimJobManager.run_handover_sim_job, name="run_handover_sim_job"),
    path('simulation_data_mgt/handoverSimJobManager/delete_handover_sim_result',
         handoverSimJobManager.delete_handover_sim_result, name="delete_handover_sim_result"),
    path('simulation_data_mgt/handoverSimJobManager/download_handover_sim_result',
         handoverSimJobManager.download_handover_sim_result, name="download_handover_sim_result"),
    
    path('simulation_data_mgt/coverageSimJobManager/run_coverage_sim_job',
         coverageSimJobManager.run_coverage_sim_job, name='run_coverage_sim_job'),
    path('simulation_data_mgt/coverageSimJobManager/delete_coverage_sim_result',
         coverageSimJobManager.delete_coverage_sim_result, name='delete_coverage_sim_result'),
    path('simulation_data_mgt/coverageSimJobManager/download_coverage_sim_result',
         coverageSimJobManager.download_coverage_sim_result, name='download_coverage_sim_result'),


    path('simulation_data_mgt/connectedDurationSimJobManager/run_connectedDuration_sim_job',
         connectedDurationSimJobManager.run_connectedDuration_sim_job, name='run_connectedDuration_sim_job'),
    path('simulation_data_mgt/connectedDurationSimJobManager/delete_connectedDuration_sim_result',
         connectedDurationSimJobManager.delete_connectedDuration_sim_result, name='delete_connectedDuration_sim_result'),
    path('simulation_data_mgt/connectedDurationSimJobManager/download_connectedDuration_sim_result',
         connectedDurationSimJobManager.download_connectedDuration_sim_result, name='download_connectedDuration_sim_result'),


    path('simulation_data_mgt/phaseSimJobManager/run_phase_sim_job',
         phaseSimJobManager.run_phase_sim_job, name='run_phase_sim_job'),
    path('simulation_data_mgt/phaseSimJobManager/delete_phase_sim_result',
         phaseSimJobManager.delete_phase_sim_result, name='delete_phase_sim_result'),
    path('simulation_data_mgt/phaseSimJobManager/download_phase_sim_result',
         phaseSimJobManager.download_phase_sim_result, name='download_phase_sim_result'),


    path('simulation_data_mgt/constellationStrategySimJobManager/run_constellationStrategy_sim_job',
         constellationStrategySimJobManager.run_constellationStrategy_sim_job, name='run_constellationStrategy_sim_job'),
    path('simulation_data_mgt/constellationStrategySimJobManager/delete_constellationStrategy_sim_result',
         constellationStrategySimJobManager.delete_constellationStrategy_sim_result, name='delete_constellationStrategy_sim_result'),
    path('simulation_data_mgt/constellationStrategySimJobManager/download_constellationStrategy_sim_result',
         constellationStrategySimJobManager.download_constellationStrategy_sim_result, name='download_constellationStrategy_sim_result'),


    path('simulation_data_mgt/islHoppingSimJobManager/run_islHopping_sim_job',
         islHoppingSimJobManager.run_islHopping_sim_job, name='run_islHopping_sim_job'),
    path('simulation_data_mgt/islHoppingSimJobManager/delete_islHopping_sim_result',
         islHoppingSimJobManager.delete_islHopping_sim_result, name='delete_islHopping_sim_result'),
    path('simulation_data_mgt/islHoppingSimJobManager/download_islHopping_sim_result',
         islHoppingSimJobManager.download_islHopping_sim_result, name='download_islHopping_sim_result'),


    path('simulation_data_mgt/modifyRegenRoutingSimJobManager/run_modifyRegenRouting_sim_job',
         modifyRegenRoutingSimJobManager.run_modifyRegenRouting_sim_job, name='run_modifyRegenRouting_sim_job'),
    path('simulation_data_mgt/modifyRegenRoutingSimJobManager/delete_modifyRegenRouting_sim_result',
         modifyRegenRoutingSimJobManager.delete_modifyRegenRouting_sim_result, name='delete_modifyRegenRouting_sim_result'),
    path('simulation_data_mgt/modifyRegenRoutingSimJobManager/download_modifyRegenRouting_sim_result',
         modifyRegenRoutingSimJobManager.download_modifyRegenRouting_sim_result, name='download_modifyRegenRouting_sim_result'),


    path('simulation_data_mgt/oneToMultiSimJobManager/run_oneToMulti_sim_job',
         oneToMultiSimJobManager.run_oneToMulti_sim_job, name='run_oneToMulti_sim_job'),
    path('simulation_data_mgt/oneToMultiSimJobManager/delete_oneToMulti_sim_result',
         oneToMultiSimJobManager.delete_oneToMulti_sim_result, name='delete_oneToMulti_sim_result'),
    path('simulation_data_mgt/oneToMultiSimJobManager/download_oneToMulti_sim_result',
         oneToMultiSimJobManager.download_oneToMulti_sim_result, name='download_oneToMulti_sim_result'),


    path('simulation_data_mgt/multiToMultiSimJobManager/run_multiToMulti_sim_job',
         multiToMultiSimJobManager.run_multiToMulti_sim_job, name='run_multiToMulti_sim_job'),
    path('simulation_data_mgt/multiToMultiSimJobManager/delete_multiToMulti_sim_result',
         multiToMultiSimJobManager.delete_multiToMulti_sim_result, name='delete_multiToMulti_sim_result'),
    path('simulation_data_mgt/multiToMultiSimJobManager/download_multiToMulti_sim_result',
         multiToMultiSimJobManager.download_multiToMulti_sim_result, name='download_multiToMulti_sim_result'),


    path('simulation_data_mgt/saveErRoutingSimJobManager/run_saveErRouting_sim_job',
         saveErRoutingSimJobManager.run_saveErRouting_sim_job, name='run_saveErRouting_sim_job'),
    path('simulation_data_mgt/saveErRoutingSimJobManager/delete_saveErRouting_sim_result',
         saveErRoutingSimJobManager.delete_saveErRouting_sim_result, name='delete_saveErRouting_sim_result'),
    path('simulation_data_mgt/saveErRoutingSimJobManager/download_saveErRouting_sim_result',
         saveErRoutingSimJobManager.download_saveErRouting_sim_result, name='download_saveErRouting_sim_result'),


    path('simulation_data_mgt/endToEndRoutingSimJobManager/run_endToEndRouting_sim_job',
         endToEndRoutingSimJobManager.run_endToEndRouting_sim_job, name='run_endToEndRouting_sim_job'),
    path('simulation_data_mgt/endToEndRoutingSimJobManager/delete_endToEndRouting_sim_result',
         endToEndRoutingSimJobManager.delete_endToEndRouting_sim_result, name='delete_endToEndRouting_sim_result'),
    path('simulation_data_mgt/endToEndRoutingSimJobManager/download_endToEndRouting_sim_result',
         endToEndRoutingSimJobManager.download_endToEndRouting_sim_result, name='download_endToEndRouting_sim_result'),


    path('simulation_data_mgt/singleBeamSimJobManager/run_singleBeam_sim_job',
         singleBeamSimJobManager.run_singleBeam_sim_job, name='run_singleBeam_sim_job'),
    path('simulation_data_mgt/singleBeamSimJobManager/delete_singleBeam_sim_result',
         singleBeamSimJobManager.delete_singleBeam_sim_result, name='delete_singleBeam_sim_result'),
    path('simulation_data_mgt/singleBeamSimJobManager/download_singleBeam_sim_result',
         singleBeamSimJobManager.download_singleBeam_sim_result, name='download_singleBeam_sim_result'),


    path('simulation_data_mgt/gsoSimJobManager/run_gso_sim_job',
         gsoSimJobManager.run_gso_sim_job, name='run_gso_sim_job'),
    path('simulation_data_mgt/gsoSimJobManager/delete_gso_sim_result',
         gsoSimJobManager.delete_gso_sim_result, name='delete_gso_sim_result'),
    path('simulation_data_mgt/gsoSimJobManager/download_gso_sim_result',
         gsoSimJobManager.download_gso_sim_result, name='download_gso_sim_result')
]
