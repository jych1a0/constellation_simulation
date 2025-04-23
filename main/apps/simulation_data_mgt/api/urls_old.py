# -*- coding: utf-8 -*-
"""
（舊版）simulation_data_mgt 應用的 API 路由，保留歷史相容性用。
"""
from django.urls import path
from main.apps.simulation_data_mgt.actors.handoverSimJobManager import handoverSimJobManager

urlpatterns = [
    path('simulation_data_mgt/handoverSimJobManager/run_handover_sim_job',
         handoverSimJobManager.run_handover_sim_job, name="run_handover_sim_job"),
    path('simulation_data_mgt/handoverSimJobManager/delete_handover_sim_result',
         handoverSimJobManager.delete_handover_sim_result, name="delete_handover_sim_result"),
    path('simulation_data_mgt/handoverSimJobManager/download_handover_sim_result',
         handoverSimJobManager.download_handover_sim_result, name="download_handover_sim_result"),
    path('simulation_data_mgt/handoverSimJobManager/download_routing_sim_result_tmp',
         handoverSimJobManager.download_routing_sim_result_tmp, name="download_routing_sim_result_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_isl_sim_result_tmp',
         handoverSimJobManager.download_isl_sim_result_tmp, name="download_isl_sim_result_tmp"),


    path('simulation_data_mgt/handoverSimJobManager/download_coverage_tmp',
         handoverSimJobManager.download_coverage_tmp, name="download_coverage_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_connected_duration_tmp',
         handoverSimJobManager.download_connected_duration_tmp, name="download_connected_duration_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_phase_tmp',
         handoverSimJobManager.download_phase_tmp, name="download_phase_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_constellation_strategy_tmp',
         handoverSimJobManager.download_constellation_strategy_tmp, name="download_constellation_strategy_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_isl_hopping_tmp',
         handoverSimJobManager.download_isl_hopping_tmp, name="download_isl_hopping_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_modify_regen_routing_tmp',
         handoverSimJobManager.download_modify_regen_routing_tmp, name="download_modify_regen_routing_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_one_to_multi_tmp',
         handoverSimJobManager.download_one_to_multi_tmp, name="download_one_to_multi_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_multi_to_multi_tmp',
         handoverSimJobManager.download_multi_to_multi_tmp, name="download_multi_to_multi_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_save_er_routing_tmp',
         handoverSimJobManager.download_save_er_routing_tmp, name="download_save_er_routing_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_end_to_end_routing_tmp',
         handoverSimJobManager.download_end_to_end_routing_tmp, name="download_end_to_end_routing_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_save_er_routing_tmp',
         handoverSimJobManager.download_save_er_routing_tmp, name="download_save_er_routing_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_single_beam_tmp',
         handoverSimJobManager.download_single_beam_tmp, name="download_single_beam_tmp"),
    path('simulation_data_mgt/handoverSimJobManager/download_gso_tmp',
         handoverSimJobManager.download_gso_tmp, name="download_gso_tmp"),
]
