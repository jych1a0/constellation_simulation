from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.ModifyRegenRoutingModel import ModifyRegenRouting
from main.utils.logger import log_trigger, log_writer
import os
import threading

class ModifyRegenRoutingManager:
    """
    負責處理 ModifyRegenRouting（再生路由修改）相關的業務邏輯與 API 請求，
    包含建立、查詢、更新、刪除等操作。
    """
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_modifyRegenRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                modifyRegenRouting_name = data.get('modifyRegenRouting_name')
                modifyRegenRouting_parameter = data.get('modifyRegenRouting_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([modifyRegenRouting_name, modifyRegenRouting_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = ModifyRegenRouting.objects.filter(
                    modifyRegenRouting_parameter=modifyRegenRouting_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ModifyRegenRouting with the same parameters already exists',
                        'existing_modifyRegenRouting': {
                            'id': existing_obj.id,
                            'modifyRegenRouting_uid': str(existing_obj.modifyRegenRouting_uid),
                            'modifyRegenRouting_name': existing_obj.modifyRegenRouting_name,
                            'modifyRegenRouting_status': existing_obj.modifyRegenRouting_status,
                            'modifyRegenRouting_parameter': existing_obj.modifyRegenRouting_parameter,
                            'modifyRegenRouting_data_path': existing_obj.modifyRegenRouting_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = ModifyRegenRouting.objects.create(
                    modifyRegenRouting_name=modifyRegenRouting_name,
                    modifyRegenRouting_parameter=modifyRegenRouting_parameter,
                    modifyRegenRouting_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'ModifyRegenRouting created successfully',
                    'data': {
                        'id': obj.id,
                        'modifyRegenRouting_uid': str(obj.modifyRegenRouting_uid),
                        'modifyRegenRouting_name': obj.modifyRegenRouting_name,
                        'modifyRegenRouting_status': obj.modifyRegenRouting_status,
                        'modifyRegenRouting_parameter': obj.modifyRegenRouting_parameter,
                        'modifyRegenRouting_data_path': obj.modifyRegenRouting_data_path
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
    def query_modifyRegenRoutingData_by_user(request):
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

                objects = ModifyRegenRouting.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'modifyRegenRouting_uid': str(obj.modifyRegenRouting_uid),
                        'modifyRegenRouting_name': obj.modifyRegenRouting_name,
                        'modifyRegenRouting_status': obj.modifyRegenRouting_status,
                        'modifyRegenRouting_parameter': obj.modifyRegenRouting_parameter,
                        'modifyRegenRouting_data_path': obj.modifyRegenRouting_data_path,
                        'modifyRegenRouting_simulation_result': obj.modifyRegenRouting_simulation_result,
                        'modifyRegenRouting_create_time': obj.modifyRegenRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.modifyRegenRouting_create_time else None,
                        'modifyRegenRouting_update_time': obj.modifyRegenRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.modifyRegenRouting_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'ModifyRegenRouting data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'modifyRegenRoutings': obj_list
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
    def delete_modifyRegenRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                modifyRegenRouting_uid = data.get('modifyRegenRouting_uid')

                if not modifyRegenRouting_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing modifyRegenRouting_uid parameter'
                    }, status=400)

                try:
                    obj = ModifyRegenRouting.objects.get(modifyRegenRouting_uid=modifyRegenRouting_uid)
                except ModifyRegenRouting.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ModifyRegenRouting not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'modifyRegenRouting_uid': str(obj.modifyRegenRouting_uid),
                    'modifyRegenRouting_name': obj.modifyRegenRouting_name,
                    'modifyRegenRouting_status': obj.modifyRegenRouting_status,
                    'modifyRegenRouting_parameter': obj.modifyRegenRouting_parameter,
                    'modifyRegenRouting_data_path': obj.modifyRegenRouting_data_path,
                    'modifyRegenRouting_create_time': obj.modifyRegenRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.modifyRegenRouting_create_time else None,
                    'modifyRegenRouting_update_time': obj.modifyRegenRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.modifyRegenRouting_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ModifyRegenRouting deleted successfully',
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
    def update_modifyRegenRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                modifyRegenRouting_uid = data.get('modifyRegenRouting_uid')

                if not modifyRegenRouting_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing modifyRegenRouting_uid parameter'
                    }, status=400)

                if 'modifyRegenRouting_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'modifyRegenRouting_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = ModifyRegenRouting.objects.get(modifyRegenRouting_uid=modifyRegenRouting_uid)
                except ModifyRegenRouting.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ModifyRegenRouting not found'
                    }, status=404)

                has_changes = False

                if 'modifyRegenRouting_name' in data and data['modifyRegenRouting_name'] != obj.modifyRegenRouting_name:
                    has_changes = True

                if 'modifyRegenRouting_status' in data and data['modifyRegenRouting_status'] != obj.modifyRegenRouting_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'modifyRegenRouting_uid': str(obj.modifyRegenRouting_uid),
                            'modifyRegenRouting_name': obj.modifyRegenRouting_name,
                            'modifyRegenRouting_status': obj.modifyRegenRouting_status,
                            'modifyRegenRouting_parameter': obj.modifyRegenRouting_parameter,
                            'modifyRegenRouting_data_path': obj.modifyRegenRouting_data_path,
                            'modifyRegenRouting_create_time': obj.modifyRegenRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'modifyRegenRouting_update_time': obj.modifyRegenRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'modifyRegenRouting_name' in data:
                    obj.modifyRegenRouting_name = data['modifyRegenRouting_name']

                if 'modifyRegenRouting_status' in data:
                    obj.modifyRegenRouting_status = data['modifyRegenRouting_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ModifyRegenRouting updated successfully',
                    'data': {
                        'id': obj.id,
                        'modifyRegenRouting_uid': str(obj.modifyRegenRouting_uid),
                        'modifyRegenRouting_name': obj.modifyRegenRouting_name,
                        'modifyRegenRouting_status': obj.modifyRegenRouting_status,
                        'modifyRegenRouting_parameter': obj.modifyRegenRouting_parameter,
                        'modifyRegenRouting_data_path': obj.modifyRegenRouting_data_path,
                        'modifyRegenRouting_create_time': obj.modifyRegenRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'modifyRegenRouting_update_time': obj.modifyRegenRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
