from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.ConnectedDurationModel import ConnectedDuration
from main.utils.logger import log_trigger, log_writer
import os
import threading

class ConnectedDurationManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_connectedDuration(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                connectedDuration_name = data.get('connectedDuration_name')
                connectedDuration_parameter = data.get('connectedDuration_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([connectedDuration_name, connectedDuration_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = ConnectedDuration.objects.filter(
                    connectedDuration_parameter=connectedDuration_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConnectedDuration with the same parameters already exists',
                        'existing_connectedDuration': {
                            'id': existing_obj.id,
                            'connectedDuration_uid': str(existing_obj.connectedDuration_uid),
                            'connectedDuration_name': existing_obj.connectedDuration_name,
                            'connectedDuration_status': existing_obj.connectedDuration_status,
                            'connectedDuration_parameter': existing_obj.connectedDuration_parameter,
                            'connectedDuration_data_path': existing_obj.connectedDuration_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = ConnectedDuration.objects.create(
                    connectedDuration_name=connectedDuration_name,
                    connectedDuration_parameter=connectedDuration_parameter,
                    connectedDuration_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConnectedDuration created successfully',
                    'data': {
                        'id': obj.id,
                        'connectedDuration_uid': str(obj.connectedDuration_uid),
                        'connectedDuration_name': obj.connectedDuration_name,
                        'connectedDuration_status': obj.connectedDuration_status,
                        'connectedDuration_parameter': obj.connectedDuration_parameter,
                        'connectedDuration_data_path': obj.connectedDuration_data_path
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


    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def query_connectedDurationData_by_user(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                user_uid = data.get('user_uid')

                if not user_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing user_uid parameter'
                    }, status=400)

                # 查找用戶
                try:
                    user = User.objects.get(user_uid=user_uid)
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'User not found'
                    }, status=404)

                objects = ConnectedDuration.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'connectedDuration_uid': str(obj.connectedDuration_uid),
                        'connectedDuration_name': obj.connectedDuration_name,
                        'connectedDuration_status': obj.connectedDuration_status,
                        'connectedDuration_parameter': obj.connectedDuration_parameter,
                        'connectedDuration_data_path': obj.connectedDuration_data_path,
                        'connectedDuration_simulation_result': obj.connectedDuration_simulation_result,
                        'connectedDuration_create_time': obj.connectedDuration_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.connectedDuration_create_time else None,
                        'connectedDuration_update_time': obj.connectedDuration_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.connectedDuration_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConnectedDuration data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'connectedDurations': obj_list
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


    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def delete_connectedDuration(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                connectedDuration_uid = data.get('connectedDuration_uid')

                if not connectedDuration_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing connectedDuration_uid parameter'
                    }, status=400)

                try:
                    obj = ConnectedDuration.objects.get(connectedDuration_uid=connectedDuration_uid)
                except ConnectedDuration.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConnectedDuration not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'connectedDuration_uid': str(obj.connectedDuration_uid),
                    'connectedDuration_name': obj.connectedDuration_name,
                    'connectedDuration_status': obj.connectedDuration_status,
                    'connectedDuration_parameter': obj.connectedDuration_parameter,
                    'connectedDuration_data_path': obj.connectedDuration_data_path,
                    'connectedDuration_create_time': obj.connectedDuration_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.connectedDuration_create_time else None,
                    'connectedDuration_update_time': obj.connectedDuration_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.connectedDuration_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConnectedDuration deleted successfully',
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

        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)


    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def update_connectedDuration(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                connectedDuration_uid = data.get('connectedDuration_uid')

                if not connectedDuration_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing connectedDuration_uid parameter'
                    }, status=400)

                if 'connectedDuration_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'connectedDuration_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = ConnectedDuration.objects.get(connectedDuration_uid=connectedDuration_uid)
                except ConnectedDuration.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConnectedDuration not found'
                    }, status=404)

                has_changes = False

                if 'connectedDuration_name' in data and data['connectedDuration_name'] != obj.connectedDuration_name:
                    has_changes = True

                if 'connectedDuration_status' in data and data['connectedDuration_status'] != obj.connectedDuration_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'connectedDuration_uid': str(obj.connectedDuration_uid),
                            'connectedDuration_name': obj.connectedDuration_name,
                            'connectedDuration_status': obj.connectedDuration_status,
                            'connectedDuration_parameter': obj.connectedDuration_parameter,
                            'connectedDuration_data_path': obj.connectedDuration_data_path,
                            'connectedDuration_create_time': obj.connectedDuration_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'connectedDuration_update_time': obj.connectedDuration_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'connectedDuration_name' in data:
                    obj.connectedDuration_name = data['connectedDuration_name']

                if 'connectedDuration_status' in data:
                    obj.connectedDuration_status = data['connectedDuration_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConnectedDuration updated successfully',
                    'data': {
                        'id': obj.id,
                        'connectedDuration_uid': str(obj.connectedDuration_uid),
                        'connectedDuration_name': obj.connectedDuration_name,
                        'connectedDuration_status': obj.connectedDuration_status,
                        'connectedDuration_parameter': obj.connectedDuration_parameter,
                        'connectedDuration_data_path': obj.connectedDuration_data_path,
                        'connectedDuration_create_time': obj.connectedDuration_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'connectedDuration_update_time': obj.connectedDuration_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
