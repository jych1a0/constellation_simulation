from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.CoverageModel import Coverage
from main.utils.logger import log_trigger, log_writer
import os
import threading

class CoverageManager:
    """
    負責處理 Coverage（覆蓋範圍）相關的業務邏輯與 API 請求，
    包含建立、查詢、更新、刪除等操作。
    """
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_coverage(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                coverage_name = data.get('coverage_name')
                coverage_parameter = data.get('coverage_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([coverage_name, coverage_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = Coverage.objects.filter(
                    coverage_parameter=coverage_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage with the same parameters already exists',
                        'existing_coverage': {
                            'id': existing_obj.id,
                            'coverage_uid': str(existing_obj.coverage_uid),
                            'coverage_name': existing_obj.coverage_name,
                            'coverage_status': existing_obj.coverage_status,
                            'coverage_parameter': existing_obj.coverage_parameter,
                            'coverage_data_path': existing_obj.coverage_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = Coverage.objects.create(
                    coverage_name=coverage_name,
                    coverage_parameter=coverage_parameter,
                    coverage_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Coverage created successfully',
                    'data': {
                        'id': obj.id,
                        'coverage_uid': str(obj.coverage_uid),
                        'coverage_name': obj.coverage_name,
                        'coverage_status': obj.coverage_status,
                        'coverage_parameter': obj.coverage_parameter,
                        'coverage_data_path': obj.coverage_data_path
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
    def query_coverageData_by_user(request):
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

                objects = Coverage.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'coverage_uid': str(obj.coverage_uid),
                        'coverage_name': obj.coverage_name,
                        'coverage_status': obj.coverage_status,
                        'coverage_parameter': obj.coverage_parameter,
                        'coverage_data_path': obj.coverage_data_path,
                        'coverage_simulation_result': obj.coverage_simulation_result,
                        'coverage_create_time': obj.coverage_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.coverage_create_time else None,
                        'coverage_update_time': obj.coverage_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.coverage_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'Coverage data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'coverages': obj_list
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
    def delete_coverage(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                coverage_uid = data.get('coverage_uid')

                if not coverage_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing coverage_uid parameter'
                    }, status=400)

                try:
                    obj = Coverage.objects.get(coverage_uid=coverage_uid)
                except Coverage.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'coverage_uid': str(obj.coverage_uid),
                    'coverage_name': obj.coverage_name,
                    'coverage_status': obj.coverage_status,
                    'coverage_parameter': obj.coverage_parameter,
                    'coverage_data_path': obj.coverage_data_path,
                    'coverage_create_time': obj.coverage_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.coverage_create_time else None,
                    'coverage_update_time': obj.coverage_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.coverage_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Coverage deleted successfully',
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
    def update_coverage(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                coverage_uid = data.get('coverage_uid')

                if not coverage_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing coverage_uid parameter'
                    }, status=400)

                if 'coverage_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'coverage_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = Coverage.objects.get(coverage_uid=coverage_uid)
                except Coverage.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage not found'
                    }, status=404)

                has_changes = False

                if 'coverage_name' in data and data['coverage_name'] != obj.coverage_name:
                    has_changes = True

                if 'coverage_status' in data and data['coverage_status'] != obj.coverage_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'coverage_uid': str(obj.coverage_uid),
                            'coverage_name': obj.coverage_name,
                            'coverage_status': obj.coverage_status,
                            'coverage_parameter': obj.coverage_parameter,
                            'coverage_data_path': obj.coverage_data_path,
                            'coverage_create_time': obj.coverage_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'coverage_update_time': obj.coverage_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'coverage_name' in data:
                    obj.coverage_name = data['coverage_name']

                if 'coverage_status' in data:
                    obj.coverage_status = data['coverage_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Coverage updated successfully',
                    'data': {
                        'id': obj.id,
                        'coverage_uid': str(obj.coverage_uid),
                        'coverage_name': obj.coverage_name,
                        'coverage_status': obj.coverage_status,
                        'coverage_parameter': obj.coverage_parameter,
                        'coverage_data_path': obj.coverage_data_path,
                        'coverage_create_time': obj.coverage_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'coverage_update_time': obj.coverage_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
