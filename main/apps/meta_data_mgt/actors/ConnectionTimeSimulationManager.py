from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.ConnectionTimeSimulationModel import ConnectionTimeSimulation
from main.utils.logger import log_trigger, log_writer
import os
import threading

class ConnectionTimeSimulationManager:

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_connection_time_simulation(request):
        """
        建立 ConnectionTimeSimulation 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                connection_time_simulation_name = data.get('connection_time_simulation_name')
                connection_time_simulation_parameter = data.get('connection_time_simulation_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([connection_time_simulation_name, connection_time_simulation_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                # 檢查是否有相同參數的資料
                existing_connection_time = ConnectionTimeSimulation.objects.filter(
                    connection_time_simulation_parameter=connection_time_simulation_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_connection_time:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConnectionTimeSimulation with the same parameters already exists',
                        'existing_connection_time_simulation': {
                            'id': existing_connection_time.id,
                            'connection_time_simulation_uid': str(existing_connection_time.connection_time_simulation_uid),
                            'connection_time_simulation_name': existing_connection_time.connection_time_simulation_name,
                            'connection_time_simulation_status': existing_connection_time.connection_time_simulation_status,
                            'connection_time_simulation_parameter': existing_connection_time.connection_time_simulation_parameter,
                            'connection_time_simulation_data_path': existing_connection_time.connection_time_simulation_data_path
                        }
                    }, status=400)

                new_obj = ConnectionTimeSimulation.objects.create(
                    connection_time_simulation_name=connection_time_simulation_name,
                    connection_time_simulation_parameter=connection_time_simulation_parameter,
                    connection_time_simulation_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConnectionTimeSimulation created successfully',
                    'data': {
                        'id': new_obj.id,
                        'connection_time_simulation_uid': str(new_obj.connection_time_simulation_uid),
                        'connection_time_simulation_name': new_obj.connection_time_simulation_name,
                        'connection_time_simulation_status': new_obj.connection_time_simulation_status,
                        'connection_time_simulation_parameter': new_obj.connection_time_simulation_parameter,
                        'connection_time_simulation_data_path': new_obj.connection_time_simulation_data_path
                    }
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def query_connection_time_simulation_by_user(request):
        """
        依照 user_uid 查詢 ConnectionTimeSimulation
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                user_uid = data.get('user_uid')

                if not user_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing user_uid parameter'
                    }, status=400)

                try:
                    user = User.objects.get(user_uid=user_uid)
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'User not found'
                    }, status=404)

                connection_time_list = ConnectionTimeSimulation.objects.filter(f_user_uid=user_uid)

                simulation_list = []
                for obj in connection_time_list:
                    simulation_list.append({
                        'id': obj.id,
                        'connection_time_simulation_uid': str(obj.connection_time_simulation_uid),
                        'connection_time_simulation_name': obj.connection_time_simulation_name,
                        'connection_time_simulation_status': obj.connection_time_simulation_status,
                        'connection_time_simulation_parameter': obj.connection_time_simulation_parameter,
                        'connection_time_simulation_data_path': obj.connection_time_simulation_data_path,
                        'connection_time_simulation_result': obj.connection_time_simulation_result,
                        'connection_time_simulation_create_time': obj.connection_time_simulation_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.connection_time_simulation_create_time else None,
                        'connection_time_simulation_update_time': obj.connection_time_simulation_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.connection_time_simulation_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConnectionTimeSimulation data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'connection_time_simulation_list': simulation_list
                    }
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def delete_connection_time_simulation(request):
        """
        刪除 ConnectionTimeSimulation 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                connection_time_simulation_uid = data.get('connection_time_simulation_uid')

                if not connection_time_simulation_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing connection_time_simulation_uid parameter'
                    }, status=400)

                try:
                    obj = ConnectionTimeSimulation.objects.get(connection_time_simulation_uid=connection_time_simulation_uid)
                except ConnectionTimeSimulation.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConnectionTimeSimulation not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'connection_time_simulation_uid': str(obj.connection_time_simulation_uid),
                    'connection_time_simulation_name': obj.connection_time_simulation_name,
                    'connection_time_simulation_status': obj.connection_time_simulation_status,
                    'connection_time_simulation_parameter': obj.connection_time_simulation_parameter,
                    'connection_time_simulation_create_time': obj.connection_time_simulation_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.connection_time_simulation_create_time else None,
                    'connection_time_simulation_update_time': obj.connection_time_simulation_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.connection_time_simulation_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConnectionTimeSimulation deleted successfully',
                    'data': deleted_info
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def update_connection_time_simulation(request):
        """
        更新 ConnectionTimeSimulation 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                connection_time_simulation_uid = data.get('connection_time_simulation_uid')

                if not connection_time_simulation_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing connection_time_simulation_uid parameter'
                    }, status=400)

                # 參數一旦建立就不可修改
                if 'connection_time_simulation_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Simulation parameter cannot be modified'
                    }, status=400)

                try:
                    obj = ConnectionTimeSimulation.objects.get(connection_time_simulation_uid=connection_time_simulation_uid)
                except ConnectionTimeSimulation.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConnectionTimeSimulation not found'
                    }, status=404)

                has_changes = False

                if 'connection_time_simulation_name' in data and data['connection_time_simulation_name'] != obj.connection_time_simulation_name:
                    has_changes = True

                if 'connection_time_simulation_status' in data and data['connection_time_simulation_status'] != obj.connection_time_simulation_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'connection_time_simulation_uid': str(obj.connection_time_simulation_uid),
                            'connection_time_simulation_name': obj.connection_time_simulation_name,
                            'connection_time_simulation_status': obj.connection_time_simulation_status,
                            'connection_time_simulation_parameter': obj.connection_time_simulation_parameter,
                            'connection_time_simulation_data_path': obj.connection_time_simulation_data_path,
                            'connection_time_simulation_create_time': obj.connection_time_simulation_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'connection_time_simulation_update_time': obj.connection_time_simulation_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'connection_time_simulation_name' in data:
                    obj.connection_time_simulation_name = data['connection_time_simulation_name']

                if 'connection_time_simulation_status' in data:
                    obj.connection_time_simulation_status = data['connection_time_simulation_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConnectionTimeSimulation updated successfully',
                    'data': {
                        'id': obj.id,
                        'connection_time_simulation_uid': str(obj.connection_time_simulation_uid),
                        'connection_time_simulation_name': obj.connection_time_simulation_name,
                        'connection_time_simulation_status': obj.connection_time_simulation_status,
                        'connection_time_simulation_parameter': obj.connection_time_simulation_parameter,
                        'connection_time_simulation_data_path': obj.connection_time_simulation_data_path,
                        'connection_time_simulation_create_time': obj.connection_time_simulation_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'connection_time_simulation_update_time': obj.connection_time_simulation_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)
