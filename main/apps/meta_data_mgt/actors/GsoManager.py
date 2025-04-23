from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.GsoModel import Gso
from main.utils.logger import log_trigger, log_writer
import os
import threading

class GsoManager:
    """
    負責處理 GSO（地球同步軌道）相關的業務邏輯與 API 請求，
    包含建立、查詢、更新、刪除等操作。
    """
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_gso(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                gso_name = data.get('gso_name')
                gso_parameter = data.get('gso_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([gso_name, gso_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = Gso.objects.filter(
                    gso_parameter=gso_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Gso with the same parameters already exists',
                        'existing_gso': {
                            'id': existing_obj.id,
                            'gso_uid': str(existing_obj.gso_uid),
                            'gso_name': existing_obj.gso_name,
                            'gso_status': existing_obj.gso_status,
                            'gso_parameter': existing_obj.gso_parameter,
                            'gso_data_path': existing_obj.gso_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = Gso.objects.create(
                    gso_name=gso_name,
                    gso_parameter=gso_parameter,
                    gso_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Gso created successfully',
                    'data': {
                        'id': obj.id,
                        'gso_uid': str(obj.gso_uid),
                        'gso_name': obj.gso_name,
                        'gso_status': obj.gso_status,
                        'gso_parameter': obj.gso_parameter,
                        'gso_data_path': obj.gso_data_path
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
    def query_gsoData_by_user(request):
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

                objects = Gso.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'gso_uid': str(obj.gso_uid),
                        'gso_name': obj.gso_name,
                        'gso_status': obj.gso_status,
                        'gso_parameter': obj.gso_parameter,
                        'gso_data_path': obj.gso_data_path,
                        'gso_simulation_result': obj.gso_simulation_result,
                        'gso_create_time': obj.gso_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.gso_create_time else None,
                        'gso_update_time': obj.gso_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.gso_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'Gso data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'gsos': obj_list
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
    def delete_gso(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                gso_uid = data.get('gso_uid')

                if not gso_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing gso_uid parameter'
                    }, status=400)

                try:
                    obj = Gso.objects.get(gso_uid=gso_uid)
                except Gso.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Gso not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'gso_uid': str(obj.gso_uid),
                    'gso_name': obj.gso_name,
                    'gso_status': obj.gso_status,
                    'gso_parameter': obj.gso_parameter,
                    'gso_data_path': obj.gso_data_path,
                    'gso_create_time': obj.gso_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.gso_create_time else None,
                    'gso_update_time': obj.gso_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.gso_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Gso deleted successfully',
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
    def update_gso(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                gso_uid = data.get('gso_uid')

                if not gso_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing gso_uid parameter'
                    }, status=400)

                if 'gso_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'gso_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = Gso.objects.get(gso_uid=gso_uid)
                except Gso.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Gso not found'
                    }, status=404)

                has_changes = False

                if 'gso_name' in data and data['gso_name'] != obj.gso_name:
                    has_changes = True

                if 'gso_status' in data and data['gso_status'] != obj.gso_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'gso_uid': str(obj.gso_uid),
                            'gso_name': obj.gso_name,
                            'gso_status': obj.gso_status,
                            'gso_parameter': obj.gso_parameter,
                            'gso_data_path': obj.gso_data_path,
                            'gso_create_time': obj.gso_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'gso_update_time': obj.gso_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'gso_name' in data:
                    obj.gso_name = data['gso_name']

                if 'gso_status' in data:
                    obj.gso_status = data['gso_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Gso updated successfully',
                    'data': {
                        'id': obj.id,
                        'gso_uid': str(obj.gso_uid),
                        'gso_name': obj.gso_name,
                        'gso_status': obj.gso_status,
                        'gso_parameter': obj.gso_parameter,
                        'gso_data_path': obj.gso_data_path,
                        'gso_create_time': obj.gso_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'gso_update_time': obj.gso_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
