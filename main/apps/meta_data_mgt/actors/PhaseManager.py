from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.PhaseModel import Phase
from main.utils.logger import log_trigger, log_writer
import os
import threading

class PhaseManager:
    """
    負責處理 Phase（相位）相關的業務邏輯與 API 請求，
    包含建立、查詢、更新、刪除等操作。
    """
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_phase(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                phase_name = data.get('phase_name')
                phase_parameter = data.get('phase_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([phase_name, phase_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = Phase.objects.filter(
                    phase_parameter=phase_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Phase with the same parameters already exists',
                        'existing_phase': {
                            'id': existing_obj.id,
                            'phase_uid': str(existing_obj.phase_uid),
                            'phase_name': existing_obj.phase_name,
                            'phase_status': existing_obj.phase_status,
                            'phase_parameter': existing_obj.phase_parameter,
                            'phase_data_path': existing_obj.phase_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = Phase.objects.create(
                    phase_name=phase_name,
                    phase_parameter=phase_parameter,
                    phase_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Phase created successfully',
                    'data': {
                        'id': obj.id,
                        'phase_uid': str(obj.phase_uid),
                        'phase_name': obj.phase_name,
                        'phase_status': obj.phase_status,
                        'phase_parameter': obj.phase_parameter,
                        'phase_data_path': obj.phase_data_path
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
    def query_phaseData_by_user(request):
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

                objects = Phase.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'phase_uid': str(obj.phase_uid),
                        'phase_name': obj.phase_name,
                        'phase_status': obj.phase_status,
                        'phase_parameter': obj.phase_parameter,
                        'phase_data_path': obj.phase_data_path,
                        'phase_simulation_result': obj.phase_simulation_result,
                        'phase_create_time': obj.phase_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.phase_create_time else None,
                        'phase_update_time': obj.phase_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.phase_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'Phase data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'phases': obj_list
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
    def delete_phase(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                phase_uid = data.get('phase_uid')

                if not phase_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing phase_uid parameter'
                    }, status=400)

                try:
                    obj = Phase.objects.get(phase_uid=phase_uid)
                except Phase.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Phase not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'phase_uid': str(obj.phase_uid),
                    'phase_name': obj.phase_name,
                    'phase_status': obj.phase_status,
                    'phase_parameter': obj.phase_parameter,
                    'phase_data_path': obj.phase_data_path,
                    'phase_create_time': obj.phase_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.phase_create_time else None,
                    'phase_update_time': obj.phase_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.phase_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Phase deleted successfully',
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
    def update_phase(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                phase_uid = data.get('phase_uid')

                if not phase_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing phase_uid parameter'
                    }, status=400)

                if 'phase_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'phase_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = Phase.objects.get(phase_uid=phase_uid)
                except Phase.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Phase not found'
                    }, status=404)

                has_changes = False

                if 'phase_name' in data and data['phase_name'] != obj.phase_name:
                    has_changes = True

                if 'phase_status' in data and data['phase_status'] != obj.phase_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'phase_uid': str(obj.phase_uid),
                            'phase_name': obj.phase_name,
                            'phase_status': obj.phase_status,
                            'phase_parameter': obj.phase_parameter,
                            'phase_data_path': obj.phase_data_path,
                            'phase_create_time': obj.phase_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'phase_update_time': obj.phase_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'phase_name' in data:
                    obj.phase_name = data['phase_name']

                if 'phase_status' in data:
                    obj.phase_status = data['phase_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Phase updated successfully',
                    'data': {
                        'id': obj.id,
                        'phase_uid': str(obj.phase_uid),
                        'phase_name': obj.phase_name,
                        'phase_status': obj.phase_status,
                        'phase_parameter': obj.phase_parameter,
                        'phase_data_path': obj.phase_data_path,
                        'phase_create_time': obj.phase_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'phase_update_time': obj.phase_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
