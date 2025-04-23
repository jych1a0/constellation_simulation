from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.OneToMultiModel import OneToMulti
from main.utils.logger import log_trigger, log_writer
import os
import threading

class OneToMultiManager:
    """
    負責處理 OneToMulti（一對多路由）相關的業務邏輯與 API 請求，
    包含建立、查詢、更新、刪除等操作。
    """
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_oneToMulti(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                oneToMulti_name = data.get('oneToMulti_name')
                oneToMulti_parameter = data.get('oneToMulti_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([oneToMulti_name, oneToMulti_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = OneToMulti.objects.filter(
                    oneToMulti_parameter=oneToMulti_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'OneToMulti with the same parameters already exists',
                        'existing_oneToMulti': {
                            'id': existing_obj.id,
                            'oneToMulti_uid': str(existing_obj.oneToMulti_uid),
                            'oneToMulti_name': existing_obj.oneToMulti_name,
                            'oneToMulti_status': existing_obj.oneToMulti_status,
                            'oneToMulti_parameter': existing_obj.oneToMulti_parameter,
                            'oneToMulti_data_path': existing_obj.oneToMulti_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = OneToMulti.objects.create(
                    oneToMulti_name=oneToMulti_name,
                    oneToMulti_parameter=oneToMulti_parameter,
                    oneToMulti_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'OneToMulti created successfully',
                    'data': {
                        'id': obj.id,
                        'oneToMulti_uid': str(obj.oneToMulti_uid),
                        'oneToMulti_name': obj.oneToMulti_name,
                        'oneToMulti_status': obj.oneToMulti_status,
                        'oneToMulti_parameter': obj.oneToMulti_parameter,
                        'oneToMulti_data_path': obj.oneToMulti_data_path
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
    def query_oneToMultiData_by_user(request):
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

                objects = OneToMulti.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'oneToMulti_uid': str(obj.oneToMulti_uid),
                        'oneToMulti_name': obj.oneToMulti_name,
                        'oneToMulti_status': obj.oneToMulti_status,
                        'oneToMulti_parameter': obj.oneToMulti_parameter,
                        'oneToMulti_data_path': obj.oneToMulti_data_path,
                        'oneToMulti_simulation_result': obj.oneToMulti_simulation_result,
                        'oneToMulti_create_time': obj.oneToMulti_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.oneToMulti_create_time else None,
                        'oneToMulti_update_time': obj.oneToMulti_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.oneToMulti_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'OneToMulti data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'oneToMultis': obj_list
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
    def delete_oneToMulti(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                oneToMulti_uid = data.get('oneToMulti_uid')

                if not oneToMulti_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing oneToMulti_uid parameter'
                    }, status=400)

                try:
                    obj = OneToMulti.objects.get(oneToMulti_uid=oneToMulti_uid)
                except OneToMulti.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'OneToMulti not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'oneToMulti_uid': str(obj.oneToMulti_uid),
                    'oneToMulti_name': obj.oneToMulti_name,
                    'oneToMulti_status': obj.oneToMulti_status,
                    'oneToMulti_parameter': obj.oneToMulti_parameter,
                    'oneToMulti_data_path': obj.oneToMulti_data_path,
                    'oneToMulti_create_time': obj.oneToMulti_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.oneToMulti_create_time else None,
                    'oneToMulti_update_time': obj.oneToMulti_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.oneToMulti_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'OneToMulti deleted successfully',
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
    def update_oneToMulti(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                oneToMulti_uid = data.get('oneToMulti_uid')

                if not oneToMulti_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing oneToMulti_uid parameter'
                    }, status=400)

                if 'oneToMulti_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'oneToMulti_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = OneToMulti.objects.get(oneToMulti_uid=oneToMulti_uid)
                except OneToMulti.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'OneToMulti not found'
                    }, status=404)

                has_changes = False

                if 'oneToMulti_name' in data and data['oneToMulti_name'] != obj.oneToMulti_name:
                    has_changes = True

                if 'oneToMulti_status' in data and data['oneToMulti_status'] != obj.oneToMulti_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'oneToMulti_uid': str(obj.oneToMulti_uid),
                            'oneToMulti_name': obj.oneToMulti_name,
                            'oneToMulti_status': obj.oneToMulti_status,
                            'oneToMulti_parameter': obj.oneToMulti_parameter,
                            'oneToMulti_data_path': obj.oneToMulti_data_path,
                            'oneToMulti_create_time': obj.oneToMulti_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'oneToMulti_update_time': obj.oneToMulti_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'oneToMulti_name' in data:
                    obj.oneToMulti_name = data['oneToMulti_name']

                if 'oneToMulti_status' in data:
                    obj.oneToMulti_status = data['oneToMulti_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'OneToMulti updated successfully',
                    'data': {
                        'id': obj.id,
                        'oneToMulti_uid': str(obj.oneToMulti_uid),
                        'oneToMulti_name': obj.oneToMulti_name,
                        'oneToMulti_status': obj.oneToMulti_status,
                        'oneToMulti_parameter': obj.oneToMulti_parameter,
                        'oneToMulti_data_path': obj.oneToMulti_data_path,
                        'oneToMulti_create_time': obj.oneToMulti_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'oneToMulti_update_time': obj.oneToMulti_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
