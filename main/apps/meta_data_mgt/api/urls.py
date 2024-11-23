from django.urls import path
from main.apps.meta_data_mgt.actors.UserManager import UserManager  # 確保導入類而不是模組
from main.apps.meta_data_mgt.actors.HandoverManager import HandoverManager

urlpatterns = [
    path('meta_data_mgt/userManager/get_hello_world', UserManager.get_hello_world),
    path('meta_data_mgt/userManager/create_user', UserManager.create_user, name="create_user"),
    path('meta_data_mgt/userManager/delete_user', UserManager.delete_user, name="delete_user"),
    path('meta_data_mgt/userManager/login_user', UserManager.login_user, name="login_user"),

    path('meta_data_mgt/handoverManager/create_handover', HandoverManager.create_handover, name="create_handover"),
    path('meta_data_mgt/handoverManager/delete_handover', HandoverManager.delete_handover, name="delete_handover"),
    path('meta_data_mgt/handoverManager/update_handover', HandoverManager.update_handover, name="update_handover"),
    path('meta_data_mgt/handoverManager/query_handoverData_by_user', HandoverManager.query_handoverData_by_user, name="query_handoverData_by_user"),

]