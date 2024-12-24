from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.TestSatelliteModel import TestSatellite
from main.utils.logger import log_trigger, log_writer
import os
import threading

class TestSatelliteManager:

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_test_satellite(request):
        """
        建立 TestSatellite 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                test_satellite_name = data.get('test_satellite_name')
                test_satellite_parameter = data.get('test_satellite_parameter')
                f_user_uid = data.get('f_user_uid')

                # 檢查必填參數
                if not all([test_satellite_name, test_satellite_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                # 檢查是否有相同參數的資料
                existing_obj = TestSatellite.objects.filter(
                    test_satellite_parameter=test_satellite_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'TestSatellite with the same parameters already exists',
                        'existing_test_satellite': {
                            'id': existing_obj.id,
                            'test_satellite_uid': str(existing_obj.test_satellite_uid),
                            'test_satellite_name': existing_obj.test_satellite_name,
                            'test_satellite_status': existing_obj.test_satellite_status,
                            'test_satellite_parameter': existing_obj.test_satellite_parameter,
                            'test_satellite_data_path': existing_obj.test_satellite_data_path
                        }
                    }, status=400)

                new_obj = TestSatellite.objects.create(
                    test_satellite_name=test_satellite_name,
                    test_satellite_parameter=test_satellite_parameter,
                    test_satellite_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'TestSatellite created successfully',
                    'data': {
                        'id': new_obj.id,
                        'test_satellite_uid': str(new_obj.test_satellite_uid),
                        'test_satellite_name': new_obj.test_satellite_name,
                        'test_satellite_status': new_obj.test_satellite_status,
                        'test_satellite_parameter': new_obj.test_satellite_parameter,
                        'test_satellite_data_path': new_obj.test_satellite_data_path
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
    def query_test_satellite_by_user(request):
        """
        依照 user_uid 查詢 TestSatellite
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

                try:
                    user = User.objects.get(user_uid=user_uid)
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'User not found'
                    }, status=404)

                query_set = TestSatellite.objects.filter(f_user_uid=user_uid)

                result_list = []
                for obj in query_set:
                    result_list.append({
                        'id': obj.id,
                        'test_satellite_uid': str(obj.test_satellite_uid),
                        'test_satellite_name': obj.test_satellite_name,
                        'test_satellite_status': obj.test_satellite_status,
                        'test_satellite_parameter': obj.test_satellite_parameter,
                        'test_satellite_data_path': obj.test_satellite_data_path,
                        'test_satellite_result': obj.test_satellite_result,
                        'test_satellite_create_time': obj.test_satellite_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.test_satellite_create_time else None,
                        'test_satellite_update_time': obj.test_satellite_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.test_satellite_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'TestSatellite data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'test_satellite_list': result_list
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
    def delete_test_satellite(request):
        """
        刪除 TestSatellite 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                test_satellite_uid = data.get('test_satellite_uid')

                if not test_satellite_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing test_satellite_uid parameter'
                    }, status=400)

                try:
                    obj = TestSatellite.objects.get(test_satellite_uid=test_satellite_uid)
                except TestSatellite.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'TestSatellite not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'test_satellite_uid': str(obj.test_satellite_uid),
                    'test_satellite_name': obj.test_satellite_name,
                    'test_satellite_status': obj.test_satellite_status,
                    'test_satellite_parameter': obj.test_satellite_parameter,
                    'test_satellite_create_time': obj.test_satellite_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.test_satellite_create_time else None,
                    'test_satellite_update_time': obj.test_satellite_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.test_satellite_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'TestSatellite deleted successfully',
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
    def update_test_satellite(request):
        """
        更新 TestSatellite 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                test_satellite_uid = data.get('test_satellite_uid')

                if not test_satellite_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing test_satellite_uid parameter'
                    }, status=400)

                # 參數一旦建立就不可修改
                if 'test_satellite_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parameter cannot be modified'
                    }, status=400)

                try:
                    obj = TestSatellite.objects.get(test_satellite_uid=test_satellite_uid)
                except TestSatellite.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'TestSatellite not found'
                    }, status=404)

                has_changes = False

                if 'test_satellite_name' in data and data['test_satellite_name'] != obj.test_satellite_name:
                    has_changes = True

                if 'test_satellite_status' in data and data['test_satellite_status'] != obj.test_satellite_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'test_satellite_uid': str(obj.test_satellite_uid),
                            'test_satellite_name': obj.test_satellite_name,
                            'test_satellite_status': obj.test_satellite_status,
                            'test_satellite_parameter': obj.test_satellite_parameter,
                            'test_satellite_data_path': obj.test_satellite_data_path,
                            'test_satellite_create_time': obj.test_satellite_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'test_satellite_update_time': obj.test_satellite_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'test_satellite_name' in data:
                    obj.test_satellite_name = data['test_satellite_name']

                if 'test_satellite_status' in data:
                    obj.test_satellite_status = data['test_satellite_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'TestSatellite updated successfully',
                    'data': {
                        'id': obj.id,
                        'test_satellite_uid': str(obj.test_satellite_uid),
                        'test_satellite_name': obj.test_satellite_name,
                        'test_satellite_status': obj.test_satellite_status,
                        'test_satellite_parameter': obj.test_satellite_parameter,
                        'test_satellite_data_path': obj.test_satellite_data_path,
                        'test_satellite_create_time': obj.test_satellite_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'test_satellite_update_time': obj.test_satellite_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
