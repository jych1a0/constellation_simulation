# main/apps/meta_data_mgt/actors/PhaseParameterSelectionManager.py
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.PhaseParameterSelectionModel import PhaseParameterSelection
from main.utils.logger import log_trigger, log_writer
import os
import threading

class PhaseParameterSelectionManager:

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_phase_parameter_selection(request):
        """
        建立 PhaseParameterSelection 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                phase_parameter_selection_name = data.get('phase_parameter_selection_name')
                phase_parameter_selection_parameter = data.get('phase_parameter_selection_parameter')
                f_user_uid = data.get('f_user_uid')

                # 檢查必填參數
                if not all([phase_parameter_selection_name, phase_parameter_selection_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                # 檢查是否有相同參數的資料
                existing_obj = PhaseParameterSelection.objects.filter(
                    phase_parameter_selection_parameter=phase_parameter_selection_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'PhaseParameterSelection with the same parameters already exists',
                        'existing_phase_parameter_selection': {
                            'id': existing_obj.id,
                            'phase_parameter_selection_uid': str(existing_obj.phase_parameter_selection_uid),
                            'phase_parameter_selection_name': existing_obj.phase_parameter_selection_name,
                            'phase_parameter_selection_status': existing_obj.phase_parameter_selection_status,
                            'phase_parameter_selection_parameter': existing_obj.phase_parameter_selection_parameter,
                            'phase_parameter_selection_data_path': existing_obj.phase_parameter_selection_data_path
                        }
                    }, status=400)

                # 建立新的資料
                new_obj = PhaseParameterSelection.objects.create(
                    phase_parameter_selection_name=phase_parameter_selection_name,
                    phase_parameter_selection_parameter=phase_parameter_selection_parameter,
                    phase_parameter_selection_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'PhaseParameterSelection created successfully',
                    'data': {
                        'id': new_obj.id,
                        'phase_parameter_selection_uid': str(new_obj.phase_parameter_selection_uid),
                        'phase_parameter_selection_name': new_obj.phase_parameter_selection_name,
                        'phase_parameter_selection_status': new_obj.phase_parameter_selection_status,
                        'phase_parameter_selection_parameter': new_obj.phase_parameter_selection_parameter,
                        'phase_parameter_selection_data_path': new_obj.phase_parameter_selection_data_path
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
    def query_phase_parameter_selection_by_user(request):
        """
        依照 user_uid 查詢 PhaseParameterSelection
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

                # 檢查使用者是否存在
                try:
                    user = User.objects.get(user_uid=user_uid)
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'User not found'
                    }, status=404)

                # 查詢資料
                query_set = PhaseParameterSelection.objects.filter(f_user_uid=user_uid)

                selection_list = []
                for obj in query_set:
                    selection_list.append({
                        'id': obj.id,
                        'phase_parameter_selection_uid': str(obj.phase_parameter_selection_uid),
                        'phase_parameter_selection_name': obj.phase_parameter_selection_name,
                        'phase_parameter_selection_status': obj.phase_parameter_selection_status,
                        'phase_parameter_selection_parameter': obj.phase_parameter_selection_parameter,
                        'phase_parameter_selection_data_path': obj.phase_parameter_selection_data_path,
                        'phase_parameter_selection_result': obj.phase_parameter_selection_result,
                        'phase_parameter_selection_create_time': obj.phase_parameter_selection_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.phase_parameter_selection_create_time else None,
                        'phase_parameter_selection_update_time': obj.phase_parameter_selection_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.phase_parameter_selection_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'PhaseParameterSelection data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'phase_parameter_selection_list': selection_list
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
    def delete_phase_parameter_selection(request):
        """
        刪除 PhaseParameterSelection 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                phase_parameter_selection_uid = data.get('phase_parameter_selection_uid')

                if not phase_parameter_selection_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing phase_parameter_selection_uid parameter'
                    }, status=400)

                try:
                    obj = PhaseParameterSelection.objects.get(phase_parameter_selection_uid=phase_parameter_selection_uid)
                except PhaseParameterSelection.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'PhaseParameterSelection not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'phase_parameter_selection_uid': str(obj.phase_parameter_selection_uid),
                    'phase_parameter_selection_name': obj.phase_parameter_selection_name,
                    'phase_parameter_selection_status': obj.phase_parameter_selection_status,
                    'phase_parameter_selection_parameter': obj.phase_parameter_selection_parameter,
                    'phase_parameter_selection_create_time': obj.phase_parameter_selection_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.phase_parameter_selection_create_time else None,
                    'phase_parameter_selection_update_time': obj.phase_parameter_selection_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.phase_parameter_selection_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'PhaseParameterSelection deleted successfully',
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
    def update_phase_parameter_selection(request):
        """
        更新 PhaseParameterSelection 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                phase_parameter_selection_uid = data.get('phase_parameter_selection_uid')

                if not phase_parameter_selection_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing phase_parameter_selection_uid parameter'
                    }, status=400)

                # 參數一旦建立就不可修改
                if 'phase_parameter_selection_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Phase parameter cannot be modified'
                    }, status=400)

                try:
                    obj = PhaseParameterSelection.objects.get(phase_parameter_selection_uid=phase_parameter_selection_uid)
                except PhaseParameterSelection.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'PhaseParameterSelection not found'
                    }, status=404)

                has_changes = False

                if 'phase_parameter_selection_name' in data and data['phase_parameter_selection_name'] != obj.phase_parameter_selection_name:
                    has_changes = True

                if 'phase_parameter_selection_status' in data and data['phase_parameter_selection_status'] != obj.phase_parameter_selection_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'phase_parameter_selection_uid': str(obj.phase_parameter_selection_uid),
                            'phase_parameter_selection_name': obj.phase_parameter_selection_name,
                            'phase_parameter_selection_status': obj.phase_parameter_selection_status,
                            'phase_parameter_selection_parameter': obj.phase_parameter_selection_parameter,
                            'phase_parameter_selection_data_path': obj.phase_parameter_selection_data_path,
                            'phase_parameter_selection_create_time': obj.phase_parameter_selection_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'phase_parameter_selection_update_time': obj.phase_parameter_selection_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'phase_parameter_selection_name' in data:
                    obj.phase_parameter_selection_name = data['phase_parameter_selection_name']

                if 'phase_parameter_selection_status' in data:
                    obj.phase_parameter_selection_status = data['phase_parameter_selection_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'PhaseParameterSelection updated successfully',
                    'data': {
                        'id': obj.id,
                        'phase_parameter_selection_uid': str(obj.phase_parameter_selection_uid),
                        'phase_parameter_selection_name': obj.phase_parameter_selection_name,
                        'phase_parameter_selection_status': obj.phase_parameter_selection_status,
                        'phase_parameter_selection_parameter': obj.phase_parameter_selection_parameter,
                        'phase_parameter_selection_data_path': obj.phase_parameter_selection_data_path,
                        'phase_parameter_selection_create_time': obj.phase_parameter_selection_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'phase_parameter_selection_update_time': obj.phase_parameter_selection_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
