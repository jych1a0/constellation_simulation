from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.SingleBeamModel import SingleBeam
from main.utils.logger import log_trigger, log_writer
import os
import threading

class SingleBeamManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_singleBeam(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)

                singleBeam_name = data.get('singleBeam_name')
                singleBeam_parameter = data.get('singleBeam_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([singleBeam_name, singleBeam_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_obj = SingleBeam.objects.filter(
                    singleBeam_parameter=singleBeam_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'SingleBeam with the same parameters already exists',
                        'existing_singleBeam': {
                            'id': existing_obj.id,
                            'singleBeam_uid': str(existing_obj.singleBeam_uid),
                            'singleBeam_name': existing_obj.singleBeam_name,
                            'singleBeam_status': existing_obj.singleBeam_status,
                            'singleBeam_parameter': existing_obj.singleBeam_parameter,
                            'singleBeam_data_path': existing_obj.singleBeam_data_path
                        }
                    }, status=400)

                # 建立實例
                obj = SingleBeam.objects.create(
                    singleBeam_name=singleBeam_name,
                    singleBeam_parameter=singleBeam_parameter,
                    singleBeam_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'SingleBeam created successfully',
                    'data': {
                        'id': obj.id,
                        'singleBeam_uid': str(obj.singleBeam_uid),
                        'singleBeam_name': obj.singleBeam_name,
                        'singleBeam_status': obj.singleBeam_status,
                        'singleBeam_parameter': obj.singleBeam_parameter,
                        'singleBeam_data_path': obj.singleBeam_data_path
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
    def query_singleBeamData_by_user(request):
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

                objects = SingleBeam.objects.filter(f_user_uid=user_uid)

                obj_list = []
                for obj in objects:
                    obj_list.append({
                        'id': obj.id,
                        'singleBeam_uid': str(obj.singleBeam_uid),
                        'singleBeam_name': obj.singleBeam_name,
                        'singleBeam_status': obj.singleBeam_status,
                        'singleBeam_parameter': obj.singleBeam_parameter,
                        'singleBeam_data_path': obj.singleBeam_data_path,
                        'singleBeam_simulation_result': obj.singleBeam_simulation_result,
                        'singleBeam_create_time': obj.singleBeam_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.singleBeam_create_time else None,
                        'singleBeam_update_time': obj.singleBeam_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.singleBeam_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'SingleBeam data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'singleBeams': obj_list
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
    def delete_singleBeam(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                singleBeam_uid = data.get('singleBeam_uid')

                if not singleBeam_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing singleBeam_uid parameter'
                    }, status=400)

                try:
                    obj = SingleBeam.objects.get(singleBeam_uid=singleBeam_uid)
                except SingleBeam.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'SingleBeam not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'singleBeam_uid': str(obj.singleBeam_uid),
                    'singleBeam_name': obj.singleBeam_name,
                    'singleBeam_status': obj.singleBeam_status,
                    'singleBeam_parameter': obj.singleBeam_parameter,
                    'singleBeam_data_path': obj.singleBeam_data_path,
                    'singleBeam_create_time': obj.singleBeam_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.singleBeam_create_time else None,
                    'singleBeam_update_time': obj.singleBeam_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.singleBeam_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'SingleBeam deleted successfully',
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
    def update_singleBeam(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                singleBeam_uid = data.get('singleBeam_uid')

                if not singleBeam_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing singleBeam_uid parameter'
                    }, status=400)

                if 'singleBeam_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'singleBeam_parameter cannot be modified'
                    }, status=400)

                try:
                    obj = SingleBeam.objects.get(singleBeam_uid=singleBeam_uid)
                except SingleBeam.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'SingleBeam not found'
                    }, status=404)

                has_changes = False

                if 'singleBeam_name' in data and data['singleBeam_name'] != obj.singleBeam_name:
                    has_changes = True

                if 'singleBeam_status' in data and data['singleBeam_status'] != obj.singleBeam_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'singleBeam_uid': str(obj.singleBeam_uid),
                            'singleBeam_name': obj.singleBeam_name,
                            'singleBeam_status': obj.singleBeam_status,
                            'singleBeam_parameter': obj.singleBeam_parameter,
                            'singleBeam_data_path': obj.singleBeam_data_path,
                            'singleBeam_create_time': obj.singleBeam_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'singleBeam_update_time': obj.singleBeam_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'singleBeam_name' in data:
                    obj.singleBeam_name = data['singleBeam_name']

                if 'singleBeam_status' in data:
                    obj.singleBeam_status = data['singleBeam_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'SingleBeam updated successfully',
                    'data': {
                        'id': obj.id,
                        'singleBeam_uid': str(obj.singleBeam_uid),
                        'singleBeam_name': obj.singleBeam_name,
                        'singleBeam_status': obj.singleBeam_status,
                        'singleBeam_parameter': obj.singleBeam_parameter,
                        'singleBeam_data_path': obj.singleBeam_data_path,
                        'singleBeam_create_time': obj.singleBeam_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'singleBeam_update_time': obj.singleBeam_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
