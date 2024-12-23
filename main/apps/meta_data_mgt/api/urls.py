from django.urls import path
from main.apps.meta_data_mgt.actors.UserManager import UserManager
from main.apps.meta_data_mgt.actors.HandoverManager import HandoverManager
from main.apps.meta_data_mgt.actors.CoverageAnalysisManager import CoverageAnalysisManager
from main.apps.meta_data_mgt.actors.ConnectionTimeSimulationManager import ConnectionTimeSimulationManager
from main.apps.meta_data_mgt.actors.PhaseParameterSelectionManager import PhaseParameterSelectionManager

urlpatterns = [
    path('meta_data_mgt/userManager/get_hello_world', UserManager.get_hello_world),
    path('meta_data_mgt/userManager/create_user', UserManager.create_user, name="create_user"),
    path('meta_data_mgt/userManager/delete_user', UserManager.delete_user, name="delete_user"),
    path('meta_data_mgt/userManager/login_user', UserManager.login_user, name="login_user"),

    path('meta_data_mgt/handoverManager/create_handover', HandoverManager.create_handover, name="create_handover"),
    path('meta_data_mgt/handoverManager/delete_handover', HandoverManager.delete_handover, name="delete_handover"),
    path('meta_data_mgt/handoverManager/update_handover', HandoverManager.update_handover, name="update_handover"),
    path('meta_data_mgt/handoverManager/query_handoverData_by_user', HandoverManager.query_handoverData_by_user, name="query_handoverData_by_user"),
    
    path('meta_data_mgt/CoverageAnalysisManager/query_coverage_analysis_by_user', CoverageAnalysisManager.query_coverage_analysis_by_user, name="query_coverage_analysis_by_user"),
    path('meta_data_mgt/CoverageAnalysisManager/create_coverage_analysis', CoverageAnalysisManager.create_coverage_analysis, name="create_coverage_analysis"),
    path('meta_data_mgt/CoverageAnalysisManager/delete_coverage_analysis', CoverageAnalysisManager.delete_coverage_analysis, name="delete_coverage_analysis"),
    path('meta_data_mgt/CoverageAnalysisManager/update_coverage_analysis', CoverageAnalysisManager.update_coverage_analysis, name="update_coverage_analysis"),

    # 新增 ConnectionTimeSimulationManager 路由
    path('meta_data_mgt/ConnectionTimeSimulationManager/create_connection_time_simulation', 
         ConnectionTimeSimulationManager.create_connection_time_simulation, 
         name="create_connection_time_simulation"),

    path('meta_data_mgt/ConnectionTimeSimulationManager/delete_connection_time_simulation', 
         ConnectionTimeSimulationManager.delete_connection_time_simulation, 
         name="delete_connection_time_simulation"),

    path('meta_data_mgt/ConnectionTimeSimulationManager/update_connection_time_simulation', 
         ConnectionTimeSimulationManager.update_connection_time_simulation, 
         name="update_connection_time_simulation"),

    path('meta_data_mgt/ConnectionTimeSimulationManager/query_connection_time_simulation_by_user', 
         ConnectionTimeSimulationManager.query_connection_time_simulation_by_user, 
         name="query_connection_time_simulation_by_user"),

    # PhaseParameterSelectionManager 路由
    path('meta_data_mgt/PhaseParameterSelectionManager/create_phase_parameter_selection',
         PhaseParameterSelectionManager.create_phase_parameter_selection,
         name="create_phase_parameter_selection"),
    path('meta_data_mgt/PhaseParameterSelectionManager/query_phase_parameter_selection_by_user',
         PhaseParameterSelectionManager.query_phase_parameter_selection_by_user,
         name="query_phase_parameter_selection_by_user"),
    path('meta_data_mgt/PhaseParameterSelectionManager/delete_phase_parameter_selection',
         PhaseParameterSelectionManager.delete_phase_parameter_selection,
         name="delete_phase_parameter_selection"),
    path('meta_data_mgt/PhaseParameterSelectionManager/update_phase_parameter_selection',
         PhaseParameterSelectionManager.update_phase_parameter_selection,
         name="update_phase_parameter_selection"),
]
