from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.EndToEndRoutingModel import EndToEndRouting
from main.utils.logger import log_trigger, log_writer
import os
import threading

class EndToEndRoutingManager:
    """
    負責處理 EndToEndRouting（端到端路由）相關的業務邏輯與 API 請求，
    包含建立、查詢、更新、刪除等操作。
    """
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_endToEndRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                endToEndRouting_name = data.get('endToEndRouting_name')
                endToEndRouting_parameter = data.get('endToEndRouting_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([endToEndRouting_name, endToEndRouting_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = EndToEndRouting.objects.filter(
                    endToEndRouting_parameter=endToEndRouting_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'EndToEndRouting with the same parameters already exists',
                        'existing_endToEndRouting': {
                            'id': existing_obj.id,
                            'endToEndRouting_uid': str(existing_obj.endToEndRouting_uid),
                            'endToEndRouting_name': existing_obj.endToEndRouting_name,
                            'endToEndRouting_status': existing_obj.endToEndRouting_status,
                            'endToEndRouting_parameter': existing_obj.endToEndRouting_parameter,
                            'endToEndRouting_data_path': existing_obj.endToEndRouting_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = EndToEndRouting.objects.create(
                    endToEndRouting_name=endToEndRouting_name,
                    endToEndRouting_parameter=endToEndRouting_parameter,
                    endToEndRouting_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'EndToEndRouting created successfully',
                    'data': {
                        'id': obj.id,
                        'endToEndRouting_uid': str(obj.endToEndRouting_uid),
                        'endToEndRouting_name': obj.endToEndRouting_name,
                        'endToEndRouting_status': obj.endToEndRouting_status,
                        'endToEndRouting_parameter': obj.endToEndRouting_parameter,
                        'endToEndRouting_data_path': obj.endToEndRouting_data_path
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
    def query_endToEndRoutingData_by_user(request):
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

                objects = EndToEndRouting.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'endToEndRouting_uid': str(obj.endToEndRouting_uid),
                        'endToEndRouting_name': obj.endToEndRouting_name,
                        'endToEndRouting_status': obj.endToEndRouting_status,
                        'endToEndRouting_parameter': obj.endToEndRouting_parameter,
                        'endToEndRouting_data_path': obj.endToEndRouting_data_path,
                        'endToEndRouting_simulation_result': obj.endToEndRouting_simulation_result,
                        'endToEndRouting_create_time': obj.endToEndRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.endToEndRouting_create_time else None,
                        'endToEndRouting_update_time': obj.endToEndRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.endToEndRouting_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'EndToEndRouting data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'endToEndRoutings': obj_list
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
    def delete_endToEndRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                endToEndRouting_uid = data.get('endToEndRouting_uid')

                if not endToEndRouting_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing endToEndRouting_uid parameter'
                    }, status=400)

                try:
                    obj = EndToEndRouting.objects.get(endToEndRouting_uid=endToEndRouting_uid)
                except EndToEndRouting.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'EndToEndRouting not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'endToEndRouting_uid': str(obj.endToEndRouting_uid),
                    'endToEndRouting_name': obj.endToEndRouting_name,
                    'endToEndRouting_status': obj.endToEndRouting_status,
                    'endToEndRouting_parameter': obj.endToEndRouting_parameter,
                    'endToEndRouting_data_path': obj.endToEndRouting_data_path,
                    'endToEndRouting_create_time': obj.endToEndRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.endToEndRouting_create_time else None,
                    'endToEndRouting_update_time': obj.endToEndRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.endToEndRouting_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'EndToEndRouting deleted successfully',
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
    def update_endToEndRouting(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                endToEndRouting_uid = data.get('endToEndRouting_uid')

                if not endToEndRouting_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing endToEndRouting_uid parameter'
                    }, status=400)

                if 'endToEndRouting_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'endToEndRouting_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = EndToEndRouting.objects.get(endToEndRouting_uid=endToEndRouting_uid)
                except EndToEndRouting.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'EndToEndRouting not found'
                    }, status=404)

                has_changes = False

                if 'endToEndRouting_name' in data and data['endToEndRouting_name'] != obj.endToEndRouting_name:
                    has_changes = True

                if 'endToEndRouting_status' in data and data['endToEndRouting_status'] != obj.endToEndRouting_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'endToEndRouting_uid': str(obj.endToEndRouting_uid),
                            'endToEndRouting_name': obj.endToEndRouting_name,
                            'endToEndRouting_status': obj.endToEndRouting_status,
                            'endToEndRouting_parameter': obj.endToEndRouting_parameter,
                            'endToEndRouting_data_path': obj.endToEndRouting_data_path,
                            'endToEndRouting_create_time': obj.endToEndRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'endToEndRouting_update_time': obj.endToEndRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'endToEndRouting_name' in data:
                    obj.endToEndRouting_name = data['endToEndRouting_name']

                if 'endToEndRouting_status' in data:
                    obj.endToEndRouting_status = data['endToEndRouting_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'EndToEndRouting updated successfully',
                    'data': {
                        'id': obj.id,
                        'endToEndRouting_uid': str(obj.endToEndRouting_uid),
                        'endToEndRouting_name': obj.endToEndRouting_name,
                        'endToEndRouting_status': obj.endToEndRouting_status,
                        'endToEndRouting_parameter': obj.endToEndRouting_parameter,
                        'endToEndRouting_data_path': obj.endToEndRouting_data_path,
                        'endToEndRouting_create_time': obj.endToEndRouting_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'endToEndRouting_update_time': obj.endToEndRouting_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
