from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.IslHoppingModel import IslHopping
from main.utils.logger import log_trigger, log_writer
import os
import threading

class IslHoppingManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_islHopping(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                islHopping_name = data.get('islHopping_name')
                islHopping_parameter = data.get('islHopping_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([islHopping_name, islHopping_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = IslHopping.objects.filter(
                    islHopping_parameter=islHopping_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'IslHopping with the same parameters already exists',
                        'existing_islHopping': {
                            'id': existing_obj.id,
                            'islHopping_uid': str(existing_obj.islHopping_uid),
                            'islHopping_name': existing_obj.islHopping_name,
                            'islHopping_status': existing_obj.islHopping_status,
                            'islHopping_parameter': existing_obj.islHopping_parameter,
                            'islHopping_data_path': existing_obj.islHopping_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = IslHopping.objects.create(
                    islHopping_name=islHopping_name,
                    islHopping_parameter=islHopping_parameter,
                    islHopping_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'IslHopping created successfully',
                    'data': {
                        'id': obj.id,
                        'islHopping_uid': str(obj.islHopping_uid),
                        'islHopping_name': obj.islHopping_name,
                        'islHopping_status': obj.islHopping_status,
                        'islHopping_parameter': obj.islHopping_parameter,
                        'islHopping_data_path': obj.islHopping_data_path
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
    def query_islHoppingData_by_user(request):
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

                objects = IslHopping.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'islHopping_uid': str(obj.islHopping_uid),
                        'islHopping_name': obj.islHopping_name,
                        'islHopping_status': obj.islHopping_status,
                        'islHopping_parameter': obj.islHopping_parameter,
                        'islHopping_data_path': obj.islHopping_data_path,
                        'islHopping_simulation_result': obj.islHopping_simulation_result,
                        'islHopping_create_time': obj.islHopping_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.islHopping_create_time else None,
                        'islHopping_update_time': obj.islHopping_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.islHopping_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'IslHopping data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'islHoppings': obj_list
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
    def delete_islHopping(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                islHopping_uid = data.get('islHopping_uid')

                if not islHopping_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing islHopping_uid parameter'
                    }, status=400)

                try:
                    obj = IslHopping.objects.get(islHopping_uid=islHopping_uid)
                except IslHopping.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'IslHopping not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'islHopping_uid': str(obj.islHopping_uid),
                    'islHopping_name': obj.islHopping_name,
                    'islHopping_status': obj.islHopping_status,
                    'islHopping_parameter': obj.islHopping_parameter,
                    'islHopping_data_path': obj.islHopping_data_path,
                    'islHopping_create_time': obj.islHopping_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.islHopping_create_time else None,
                    'islHopping_update_time': obj.islHopping_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.islHopping_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'IslHopping deleted successfully',
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
    def update_islHopping(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                islHopping_uid = data.get('islHopping_uid')

                if not islHopping_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing islHopping_uid parameter'
                    }, status=400)

                if 'islHopping_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'islHopping_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = IslHopping.objects.get(islHopping_uid=islHopping_uid)
                except IslHopping.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'IslHopping not found'
                    }, status=404)

                has_changes = False

                if 'islHopping_name' in data and data['islHopping_name'] != obj.islHopping_name:
                    has_changes = True

                if 'islHopping_status' in data and data['islHopping_status'] != obj.islHopping_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'islHopping_uid': str(obj.islHopping_uid),
                            'islHopping_name': obj.islHopping_name,
                            'islHopping_status': obj.islHopping_status,
                            'islHopping_parameter': obj.islHopping_parameter,
                            'islHopping_data_path': obj.islHopping_data_path,
                            'islHopping_create_time': obj.islHopping_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'islHopping_update_time': obj.islHopping_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'islHopping_name' in data:
                    obj.islHopping_name = data['islHopping_name']

                if 'islHopping_status' in data:
                    obj.islHopping_status = data['islHopping_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'IslHopping updated successfully',
                    'data': {
                        'id': obj.id,
                        'islHopping_uid': str(obj.islHopping_uid),
                        'islHopping_name': obj.islHopping_name,
                        'islHopping_status': obj.islHopping_status,
                        'islHopping_parameter': obj.islHopping_parameter,
                        'islHopping_data_path': obj.islHopping_data_path,
                        'islHopping_create_time': obj.islHopping_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'islHopping_update_time': obj.islHopping_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
