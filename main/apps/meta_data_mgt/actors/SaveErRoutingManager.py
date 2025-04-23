from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.SaveErRoutingModel import SaveErRouting
from main.utils.logger import log_trigger, log_writer
import os
import threading

class SaveErRoutingManager:
    """
    負責處理 SaveErRouting（ER 路由儲存）相關的業務邏輯與 API 請求，
    包含建立、查詢、更新、刪除等操作。
    """
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_saveErRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                saveErRouting_name = data.get('saveErRouting_name')
                saveErRouting_parameter = data.get('saveErRouting_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([saveErRouting_name, saveErRouting_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = SaveErRouting.objects.filter(
                    saveErRouting_parameter=saveErRouting_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'SaveErRouting with the same parameters already exists',
                        'existing_saveErRouting': {
                            'id': existing_obj.id,
                            'saveErRouting_uid': str(existing_obj.saveErRouting_uid),
                            'saveErRouting_name': existing_obj.saveErRouting_name,
                            'saveErRouting_status': existing_obj.saveErRouting_status,
                            'saveErRouting_parameter': existing_obj.saveErRouting_parameter,
                            'saveErRouting_data_path': existing_obj.saveErRouting_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = SaveErRouting.objects.create(
                    saveErRouting_name=saveErRouting_name,
                    saveErRouting_parameter=saveErRouting_parameter,
                    saveErRouting_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'SaveErRouting created successfully',
                    'data': {
                        'id': obj.id,
                        'saveErRouting_uid': str(obj.saveErRouting_uid),
                        'saveErRouting_name': obj.saveErRouting_name,
                        'saveErRouting_status': obj.saveErRouting_status,
                        'saveErRouting_parameter': obj.saveErRouting_parameter,
                        'saveErRouting_data_path': obj.saveErRouting_data_path
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
    def query_saveErRoutingData_by_user(request):
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

                objects = SaveErRouting.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'saveErRouting_uid': str(obj.saveErRouting_uid),
                        'saveErRouting_name': obj.saveErRouting_name,
                        'saveErRouting_status': obj.saveErRouting_status,
                        'saveErRouting_parameter': obj.saveErRouting_parameter,
                        'saveErRouting_data_path': obj.saveErRouting_data_path,
                        'saveErRouting_simulation_result': obj.saveErRouting_simulation_result,
                        'saveErRouting_create_time': obj.saveErRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.saveErRouting_create_time else None,
                        'saveErRouting_update_time': obj.saveErRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.saveErRouting_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'SaveErRouting data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'saveErRoutings': obj_list
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
    def delete_saveErRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                saveErRouting_uid = data.get('saveErRouting_uid')

                if not saveErRouting_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing saveErRouting_uid parameter'
                    }, status=400)

                try:
                    obj = SaveErRouting.objects.get(saveErRouting_uid=saveErRouting_uid)
                except SaveErRouting.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'SaveErRouting not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'saveErRouting_uid': str(obj.saveErRouting_uid),
                    'saveErRouting_name': obj.saveErRouting_name,
                    'saveErRouting_status': obj.saveErRouting_status,
                    'saveErRouting_parameter': obj.saveErRouting_parameter,
                    'saveErRouting_data_path': obj.saveErRouting_data_path,
                    'saveErRouting_create_time': obj.saveErRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.saveErRouting_create_time else None,
                    'saveErRouting_update_time': obj.saveErRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.saveErRouting_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'SaveErRouting deleted successfully',
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
    def update_saveErRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                saveErRouting_uid = data.get('saveErRouting_uid')

                if not saveErRouting_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing saveErRouting_uid parameter'
                    }, status=400)

                if 'saveErRouting_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'saveErRouting_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = SaveErRouting.objects.get(saveErRouting_uid=saveErRouting_uid)
                except SaveErRouting.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'SaveErRouting not found'
                    }, status=404)

                has_changes = False

                if 'saveErRouting_name' in data and data['saveErRouting_name'] != obj.saveErRouting_name:
                    has_changes = True

                if 'saveErRouting_status' in data and data['saveErRouting_status'] != obj.saveErRouting_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'saveErRouting_uid': str(obj.saveErRouting_uid),
                            'saveErRouting_name': obj.saveErRouting_name,
                            'saveErRouting_status': obj.saveErRouting_status,
                            'saveErRouting_parameter': obj.saveErRouting_parameter,
                            'saveErRouting_data_path': obj.saveErRouting_data_path,
                            'saveErRouting_create_time': obj.saveErRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'saveErRouting_update_time': obj.saveErRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'saveErRouting_name' in data:
                    obj.saveErRouting_name = data['saveErRouting_name']

                if 'saveErRouting_status' in data:
                    obj.saveErRouting_status = data['saveErRouting_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'SaveErRouting updated successfully',
                    'data': {
                        'id': obj.id,
                        'saveErRouting_uid': str(obj.saveErRouting_uid),
                        'saveErRouting_name': obj.saveErRouting_name,
                        'saveErRouting_status': obj.saveErRouting_status,
                        'saveErRouting_parameter': obj.saveErRouting_parameter,
                        'saveErRouting_data_path': obj.saveErRouting_data_path,
                        'saveErRouting_create_time': obj.saveErRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'saveErRouting_update_time': obj.saveErRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
