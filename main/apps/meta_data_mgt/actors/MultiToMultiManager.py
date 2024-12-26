from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.MultiToMultiModel import MultiToMulti
from main.utils.logger import log_trigger, log_writer
import os
import threading

class MultiToMultiManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_multiToMulti(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                multiToMulti_name = data.get('multiToMulti_name')
                multiToMulti_parameter = data.get('multiToMulti_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([multiToMulti_name, multiToMulti_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = MultiToMulti.objects.filter(
                    multiToMulti_parameter=multiToMulti_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'MultiToMulti with the same parameters already exists',
                        'existing_multiToMulti': {
                            'id': existing_obj.id,
                            'multiToMulti_uid': str(existing_obj.multiToMulti_uid),
                            'multiToMulti_name': existing_obj.multiToMulti_name,
                            'multiToMulti_status': existing_obj.multiToMulti_status,
                            'multiToMulti_parameter': existing_obj.multiToMulti_parameter,
                            'multiToMulti_data_path': existing_obj.multiToMulti_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = MultiToMulti.objects.create(
                    multiToMulti_name=multiToMulti_name,
                    multiToMulti_parameter=multiToMulti_parameter,
                    multiToMulti_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'MultiToMulti created successfully',
                    'data': {
                        'id': obj.id,
                        'multiToMulti_uid': str(obj.multiToMulti_uid),
                        'multiToMulti_name': obj.multiToMulti_name,
                        'multiToMulti_status': obj.multiToMulti_status,
                        'multiToMulti_parameter': obj.multiToMulti_parameter,
                        'multiToMulti_data_path': obj.multiToMulti_data_path
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
    def query_multiToMultiData_by_user(request):
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

                objects = MultiToMulti.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'multiToMulti_uid': str(obj.multiToMulti_uid),
                        'multiToMulti_name': obj.multiToMulti_name,
                        'multiToMulti_status': obj.multiToMulti_status,
                        'multiToMulti_parameter': obj.multiToMulti_parameter,
                        'multiToMulti_data_path': obj.multiToMulti_data_path,
                        'multiToMulti_simulation_result': obj.multiToMulti_simulation_result,
                        'multiToMulti_create_time': obj.multiToMulti_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.multiToMulti_create_time else None,
                        'multiToMulti_update_time': obj.multiToMulti_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.multiToMulti_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'MultiToMulti data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'multiToMultis': obj_list
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
    def delete_multiToMulti(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                multiToMulti_uid = data.get('multiToMulti_uid')

                if not multiToMulti_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing multiToMulti_uid parameter'
                    }, status=400)

                try:
                    obj = MultiToMulti.objects.get(multiToMulti_uid=multiToMulti_uid)
                except MultiToMulti.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'MultiToMulti not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'multiToMulti_uid': str(obj.multiToMulti_uid),
                    'multiToMulti_name': obj.multiToMulti_name,
                    'multiToMulti_status': obj.multiToMulti_status,
                    'multiToMulti_parameter': obj.multiToMulti_parameter,
                    'multiToMulti_data_path': obj.multiToMulti_data_path,
                    'multiToMulti_create_time': obj.multiToMulti_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.multiToMulti_create_time else None,
                    'multiToMulti_update_time': obj.multiToMulti_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.multiToMulti_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'MultiToMulti deleted successfully',
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
    def update_multiToMulti(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                multiToMulti_uid = data.get('multiToMulti_uid')

                if not multiToMulti_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing multiToMulti_uid parameter'
                    }, status=400)

                if 'multiToMulti_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'multiToMulti_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = MultiToMulti.objects.get(multiToMulti_uid=multiToMulti_uid)
                except MultiToMulti.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'MultiToMulti not found'
                    }, status=404)

                has_changes = False

                if 'multiToMulti_name' in data and data['multiToMulti_name'] != obj.multiToMulti_name:
                    has_changes = True

                if 'multiToMulti_status' in data and data['multiToMulti_status'] != obj.multiToMulti_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'multiToMulti_uid': str(obj.multiToMulti_uid),
                            'multiToMulti_name': obj.multiToMulti_name,
                            'multiToMulti_status': obj.multiToMulti_status,
                            'multiToMulti_parameter': obj.multiToMulti_parameter,
                            'multiToMulti_data_path': obj.multiToMulti_data_path,
                            'multiToMulti_create_time': obj.multiToMulti_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'multiToMulti_update_time': obj.multiToMulti_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'multiToMulti_name' in data:
                    obj.multiToMulti_name = data['multiToMulti_name']

                if 'multiToMulti_status' in data:
                    obj.multiToMulti_status = data['multiToMulti_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'MultiToMulti updated successfully',
                    'data': {
                        'id': obj.id,
                        'multiToMulti_uid': str(obj.multiToMulti_uid),
                        'multiToMulti_name': obj.multiToMulti_name,
                        'multiToMulti_status': obj.multiToMulti_status,
                        'multiToMulti_parameter': obj.multiToMulti_parameter,
                        'multiToMulti_data_path': obj.multiToMulti_data_path,
                        'multiToMulti_create_time': obj.multiToMulti_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'multiToMulti_update_time': obj.multiToMulti_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
