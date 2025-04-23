from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.ConstellationStrategyModel import ConstellationStrategy
from main.utils.logger import log_trigger, log_writer
import os
import threading

class ConstellationStrategyManager:
    """
    負責處理 ConstellationStrategy（星座策略）相關的業務邏輯與 API 請求，
    包含建立、查詢、更新、刪除等操作。
    """
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_constellationStrategy(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                constellationStrategy_name = data.get('constellationStrategy_name')
                constellationStrategy_parameter = data.get('constellationStrategy_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([constellationStrategy_name, constellationStrategy_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = ConstellationStrategy.objects.filter(
                    constellationStrategy_parameter=constellationStrategy_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConstellationStrategy with the same parameters already exists',
                        'existing_constellationStrategy': {
                            'id': existing_obj.id,
                            'constellationStrategy_uid': str(existing_obj.constellationStrategy_uid),
                            'constellationStrategy_name': existing_obj.constellationStrategy_name,
                            'constellationStrategy_status': existing_obj.constellationStrategy_status,
                            'constellationStrategy_parameter': existing_obj.constellationStrategy_parameter,
                            'constellationStrategy_data_path': existing_obj.constellationStrategy_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = ConstellationStrategy.objects.create(
                    constellationStrategy_name=constellationStrategy_name,
                    constellationStrategy_parameter=constellationStrategy_parameter,
                    constellationStrategy_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConstellationStrategy created successfully',
                    'data': {
                        'id': obj.id,
                        'constellationStrategy_uid': str(obj.constellationStrategy_uid),
                        'constellationStrategy_name': obj.constellationStrategy_name,
                        'constellationStrategy_status': obj.constellationStrategy_status,
                        'constellationStrategy_parameter': obj.constellationStrategy_parameter,
                        'constellationStrategy_data_path': obj.constellationStrategy_data_path
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
    def query_constellationStrategyData_by_user(request):
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

                objects = ConstellationStrategy.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'constellationStrategy_uid': str(obj.constellationStrategy_uid),
                        'constellationStrategy_name': obj.constellationStrategy_name,
                        'constellationStrategy_status': obj.constellationStrategy_status,
                        'constellationStrategy_parameter': obj.constellationStrategy_parameter,
                        'constellationStrategy_data_path': obj.constellationStrategy_data_path,
                        'constellationStrategy_simulation_result': obj.constellationStrategy_simulation_result,
                        'constellationStrategy_create_time': obj.constellationStrategy_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.constellationStrategy_create_time else None,
                        'constellationStrategy_update_time': obj.constellationStrategy_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.constellationStrategy_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConstellationStrategy data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'constellationStrategys': obj_list
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
    def delete_constellationStrategy(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                constellationStrategy_uid = data.get('constellationStrategy_uid')

                if not constellationStrategy_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing constellationStrategy_uid parameter'
                    }, status=400)

                try:
                    obj = ConstellationStrategy.objects.get(constellationStrategy_uid=constellationStrategy_uid)
                except ConstellationStrategy.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConstellationStrategy not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'constellationStrategy_uid': str(obj.constellationStrategy_uid),
                    'constellationStrategy_name': obj.constellationStrategy_name,
                    'constellationStrategy_status': obj.constellationStrategy_status,
                    'constellationStrategy_parameter': obj.constellationStrategy_parameter,
                    'constellationStrategy_data_path': obj.constellationStrategy_data_path,
                    'constellationStrategy_create_time': obj.constellationStrategy_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.constellationStrategy_create_time else None,
                    'constellationStrategy_update_time': obj.constellationStrategy_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.constellationStrategy_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConstellationStrategy deleted successfully',
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
    def update_constellationStrategy(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                constellationStrategy_uid = data.get('constellationStrategy_uid')

                if not constellationStrategy_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing constellationStrategy_uid parameter'
                    }, status=400)

                if 'constellationStrategy_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'constellationStrategy_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = ConstellationStrategy.objects.get(constellationStrategy_uid=constellationStrategy_uid)
                except ConstellationStrategy.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConstellationStrategy not found'
                    }, status=404)

                has_changes = False

                if 'constellationStrategy_name' in data and data['constellationStrategy_name'] != obj.constellationStrategy_name:
                    has_changes = True

                if 'constellationStrategy_status' in data and data['constellationStrategy_status'] != obj.constellationStrategy_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'constellationStrategy_uid': str(obj.constellationStrategy_uid),
                            'constellationStrategy_name': obj.constellationStrategy_name,
                            'constellationStrategy_status': obj.constellationStrategy_status,
                            'constellationStrategy_parameter': obj.constellationStrategy_parameter,
                            'constellationStrategy_data_path': obj.constellationStrategy_data_path,
                            'constellationStrategy_create_time': obj.constellationStrategy_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'constellationStrategy_update_time': obj.constellationStrategy_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'constellationStrategy_name' in data:
                    obj.constellationStrategy_name = data['constellationStrategy_name']

                if 'constellationStrategy_status' in data:
                    obj.constellationStrategy_status = data['constellationStrategy_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConstellationStrategy updated successfully',
                    'data': {
                        'id': obj.id,
                        'constellationStrategy_uid': str(obj.constellationStrategy_uid),
                        'constellationStrategy_name': obj.constellationStrategy_name,
                        'constellationStrategy_status': obj.constellationStrategy_status,
                        'constellationStrategy_parameter': obj.constellationStrategy_parameter,
                        'constellationStrategy_data_path': obj.constellationStrategy_data_path,
                        'constellationStrategy_create_time': obj.constellationStrategy_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'constellationStrategy_update_time': obj.constellationStrategy_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
