# -*- coding: utf-8 -*-
"""
定義 meta_data_mgt 應用的 API 路由，負責將 HTTP 請求導向對應的 view 處理函式。
"""
from django.urls import path
from main.apps.meta_data_mgt.actors.UserManager import UserManager
from main.apps.meta_data_mgt.actors.HandoverManager import HandoverManager
from main.apps.meta_data_mgt.actors.CoverageManager import CoverageManager
from main.apps.meta_data_mgt.actors.ConnectedDurationManager import ConnectedDurationManager
from main.apps.meta_data_mgt.actors.PhaseManager import PhaseManager
from main.apps.meta_data_mgt.actors.ConstellationStrategyManager import ConstellationStrategyManager
from main.apps.meta_data_mgt.actors.IslHoppingManager import IslHoppingManager
from main.apps.meta_data_mgt.actors.ModifyRegenRoutingManager import ModifyRegenRoutingManager
from main.apps.meta_data_mgt.actors.OneToMultiManager import OneToMultiManager
from main.apps.meta_data_mgt.actors.MultiToMultiManager import MultiToMultiManager
from main.apps.meta_data_mgt.actors.SaveErRoutingManager import SaveErRoutingManager
from main.apps.meta_data_mgt.actors.EndToEndRoutingManager import EndToEndRoutingManager
from main.apps.meta_data_mgt.actors.SingleBeamManager import SingleBeamManager
from main.apps.meta_data_mgt.actors.GsoManager import GsoManager

urlpatterns = [
    path('meta_data_mgt/userManager/get_hello_world', UserManager.get_hello_world),
    path('meta_data_mgt/userManager/create_user', UserManager.create_user, name="create_user"),
    path('meta_data_mgt/userManager/delete_user', UserManager.delete_user, name="delete_user"),
    path('meta_data_mgt/userManager/login_user', UserManager.login_user, name="login_user"),

    path('meta_data_mgt/handoverManager/create_handover', HandoverManager.create_handover, name="create_handover"),
    path('meta_data_mgt/handoverManager/delete_handover', HandoverManager.delete_handover, name="delete_handover"),
    path('meta_data_mgt/handoverManager/update_handover', HandoverManager.update_handover, name="update_handover"),
    path('meta_data_mgt/handoverManager/query_handoverData_by_user', HandoverManager.query_handoverData_by_user, name="query_handoverData_by_user"),
    
    path('meta_data_mgt/coverageManager/create_coverage', CoverageManager.create_coverage, name="create_coverage"),
    path('meta_data_mgt/coverageManager/delete_coverage', CoverageManager.delete_coverage, name="delete_coverage"),
    path('meta_data_mgt/coverageManager/update_coverage', CoverageManager.update_coverage, name="update_coverage"),
    path('meta_data_mgt/coverageManager/query_coverageData_by_user', CoverageManager.query_coverageData_by_user, name="query_coverageData_by_user"),

    path('meta_data_mgt/connectedDurationManager/create_connectedDuration', ConnectedDurationManager.create_connectedDuration, name="create_connectedDuration"),
    path('meta_data_mgt/connectedDurationManager/delete_connectedDuration', ConnectedDurationManager.delete_connectedDuration, name="delete_connectedDuration"),
    path('meta_data_mgt/connectedDurationManager/update_connectedDuration', ConnectedDurationManager.update_connectedDuration, name="update_connectedDuration"),
    path('meta_data_mgt/connectedDurationManager/query_connectedDurationData_by_user', ConnectedDurationManager.query_connectedDurationData_by_user, name="query_connectedDurationData_by_user"),

    path('meta_data_mgt/phaseManager/create_phase', PhaseManager.create_phase, name="create_phase"),
    path('meta_data_mgt/phaseManager/delete_phase', PhaseManager.delete_phase, name="delete_phase"),
    path('meta_data_mgt/phaseManager/update_phase', PhaseManager.update_phase, name="update_phase"),
    path('meta_data_mgt/phaseManager/query_phaseData_by_user', PhaseManager.query_phaseData_by_user, name="query_phaseData_by_user"),

    path('meta_data_mgt/constellationStrategyManager/create_constellationStrategy', ConstellationStrategyManager.create_constellationStrategy, name="create_constellationStrategy"),
    path('meta_data_mgt/constellationStrategyManager/delete_constellationStrategy', ConstellationStrategyManager.delete_constellationStrategy, name="delete_constellationStrategy"),
    path('meta_data_mgt/constellationStrategyManager/update_constellationStrategy', ConstellationStrategyManager.update_constellationStrategy, name="update_constellationStrategy"),
    path('meta_data_mgt/constellationStrategyManager/query_constellationStrategyData_by_user', ConstellationStrategyManager.query_constellationStrategyData_by_user, name="query_constellationStrategyData_by_user"),

    path('meta_data_mgt/islHoppingManager/create_islHopping', IslHoppingManager.create_islHopping, name="create_islHopping"),
    path('meta_data_mgt/islHoppingManager/delete_islHopping', IslHoppingManager.delete_islHopping, name="delete_islHopping"),
    path('meta_data_mgt/islHoppingManager/update_islHopping', IslHoppingManager.update_islHopping, name="update_islHopping"),
    path('meta_data_mgt/islHoppingManager/query_islHoppingData_by_user', IslHoppingManager.query_islHoppingData_by_user, name="query_islHoppingData_by_user"),

    path('meta_data_mgt/modifyRegenRoutingManager/create_modifyRegenRouting', ModifyRegenRoutingManager.create_modifyRegenRouting, name="create_modifyRegenRouting"),
    path('meta_data_mgt/modifyRegenRoutingManager/delete_modifyRegenRouting', ModifyRegenRoutingManager.delete_modifyRegenRouting, name="delete_modifyRegenRouting"),
    path('meta_data_mgt/modifyRegenRoutingManager/update_modifyRegenRouting', ModifyRegenRoutingManager.update_modifyRegenRouting, name="update_modifyRegenRouting"),
    path('meta_data_mgt/modifyRegenRoutingManager/query_modifyRegenRoutingData_by_user', ModifyRegenRoutingManager.query_modifyRegenRoutingData_by_user, name="query_modifyRegenRoutingData_by_user"),

    path('meta_data_mgt/oneToMultiManager/create_oneToMulti', OneToMultiManager.create_oneToMulti, name="create_oneToMulti"),
    path('meta_data_mgt/oneToMultiManager/delete_oneToMulti', OneToMultiManager.delete_oneToMulti, name="delete_oneToMulti"),
    path('meta_data_mgt/oneToMultiManager/update_oneToMulti', OneToMultiManager.update_oneToMulti, name="update_oneToMulti"),
    path('meta_data_mgt/oneToMultiManager/query_oneToMultiData_by_user', OneToMultiManager.query_oneToMultiData_by_user, name="query_oneToMultiData_by_user"),

    path('meta_data_mgt/multiToMultiManager/create_multiToMulti', MultiToMultiManager.create_multiToMulti, name="create_multiToMulti"),
    path('meta_data_mgt/multiToMultiManager/delete_multiToMulti', MultiToMultiManager.delete_multiToMulti, name="delete_multiToMulti"),
    path('meta_data_mgt/multiToMultiManager/update_multiToMulti', MultiToMultiManager.update_multiToMulti, name="update_multiToMulti"),
    path('meta_data_mgt/multiToMultiManager/query_multiToMultiData_by_user', MultiToMultiManager.query_multiToMultiData_by_user, name="query_multiToMultiData_by_user"),

    path('meta_data_mgt/saveErRoutingManager/create_saveErRouting', SaveErRoutingManager.create_saveErRouting, name="create_saveErRouting"),
    path('meta_data_mgt/saveErRoutingManager/delete_saveErRouting', SaveErRoutingManager.delete_saveErRouting, name="delete_saveErRouting"),
    path('meta_data_mgt/saveErRoutingManager/update_saveErRouting', SaveErRoutingManager.update_saveErRouting, name="update_saveErRouting"),
    path('meta_data_mgt/saveErRoutingManager/query_saveErRoutingData_by_user', SaveErRoutingManager.query_saveErRoutingData_by_user, name="query_saveErRoutingData_by_user"),

    path('meta_data_mgt/endToEndRoutingManager/create_endToEndRouting', EndToEndRoutingManager.create_endToEndRouting, name="create_endToEndRouting"),
    path('meta_data_mgt/endToEndRoutingManager/delete_endToEndRouting', EndToEndRoutingManager.delete_endToEndRouting, name="delete_endToEndRouting"),
    path('meta_data_mgt/endToEndRoutingManager/update_endToEndRouting', EndToEndRoutingManager.update_endToEndRouting, name="update_endToEndRouting"),
    path('meta_data_mgt/endToEndRoutingManager/query_endToEndRoutingData_by_user', EndToEndRoutingManager.query_endToEndRoutingData_by_user, name="query_endToEndRoutingData_by_user"),

    path('meta_data_mgt/singleBeamManager/create_singleBeam', SingleBeamManager.create_singleBeam, name="create_singleBeam"),
    path('meta_data_mgt/singleBeamManager/delete_singleBeam', SingleBeamManager.delete_singleBeam, name="delete_singleBeam"),
    path('meta_data_mgt/singleBeamManager/update_singleBeam', SingleBeamManager.update_singleBeam, name="update_singleBeam"),
    path('meta_data_mgt/singleBeamManager/query_singleBeamData_by_user', SingleBeamManager.query_singleBeamData_by_user, name="query_singleBeamData_by_user"),

    path('meta_data_mgt/gsoManager/create_gso', GsoManager.create_gso, name="create_gso"),
    path('meta_data_mgt/gsoManager/delete_gso', GsoManager.delete_gso, name="delete_gso"),
    path('meta_data_mgt/gsoManager/update_gso', GsoManager.update_gso, name="update_gso"),
    path('meta_data_mgt/gsoManager/query_gsoData_by_user', GsoManager.query_gsoData_by_user, name="query_gsoData_by_user"),
]
