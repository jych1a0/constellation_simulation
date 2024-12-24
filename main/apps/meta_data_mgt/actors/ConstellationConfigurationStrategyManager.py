from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.ConstellationConfigurationStrategyModel import ConstellationConfigurationStrategy
from main.utils.logger import log_trigger, log_writer
import os
import threading

class ConstellationConfigurationStrategyManager:

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_constellation_configuration_strategy(request):
        """
        建立 ConstellationConfigurationStrategy 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                constellation_configuration_strategy_name = data.get('constellation_configuration_strategy_name')
                constellation_configuration_strategy_parameter = data.get('constellation_configuration_strategy_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([constellation_configuration_strategy_name, constellation_configuration_strategy_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                # 檢查是否有相同參數的資料
                existing_obj = ConstellationConfigurationStrategy.objects.filter(
                    constellation_configuration_strategy_parameter=constellation_configuration_strategy_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConstellationConfigurationStrategy with the same parameters already exists',
                        'existing_constellation_configuration_strategy': {
                            'id': existing_obj.id,
                            'constellation_configuration_strategy_uid': str(existing_obj.constellation_configuration_strategy_uid),
                            'constellation_configuration_strategy_name': existing_obj.constellation_configuration_strategy_name,
                            'constellation_configuration_strategy_status': existing_obj.constellation_configuration_strategy_status,
                            'constellation_configuration_strategy_parameter': existing_obj.constellation_configuration_strategy_parameter,
                            'constellation_configuration_strategy_data_path': existing_obj.constellation_configuration_strategy_data_path
                        }
                    }, status=400)

                # 建立新的資料
                new_obj = ConstellationConfigurationStrategy.objects.create(
                    constellation_configuration_strategy_name=constellation_configuration_strategy_name,
                    constellation_configuration_strategy_parameter=constellation_configuration_strategy_parameter,
                    constellation_configuration_strategy_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConstellationConfigurationStrategy created successfully',
                    'data': {
                        'id': new_obj.id,
                        'constellation_configuration_strategy_uid': str(new_obj.constellation_configuration_strategy_uid),
                        'constellation_configuration_strategy_name': new_obj.constellation_configuration_strategy_name,
                        'constellation_configuration_strategy_status': new_obj.constellation_configuration_strategy_status,
                        'constellation_configuration_strategy_parameter': new_obj.constellation_configuration_strategy_parameter,
                        'constellation_configuration_strategy_data_path': new_obj.constellation_configuration_strategy_data_path
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
    def query_constellation_configuration_strategy_by_user(request):
        """
        依照 user_uid 查詢 ConstellationConfigurationStrategy
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

                query_set = ConstellationConfigurationStrategy.objects.filter(f_user_uid=user_uid)

                strategy_list = []
                for obj in query_set:
                    strategy_list.append({
                        'id': obj.id,
                        'constellation_configuration_strategy_uid': str(obj.constellation_configuration_strategy_uid),
                        'constellation_configuration_strategy_name': obj.constellation_configuration_strategy_name,
                        'constellation_configuration_strategy_status': obj.constellation_configuration_strategy_status,
                        'constellation_configuration_strategy_parameter': obj.constellation_configuration_strategy_parameter,
                        'constellation_configuration_strategy_data_path': obj.constellation_configuration_strategy_data_path,
                        'constellation_configuration_strategy_result': obj.constellation_configuration_strategy_result,
                        'constellation_configuration_strategy_create_time': obj.constellation_configuration_strategy_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.constellation_configuration_strategy_create_time else None,
                        'constellation_configuration_strategy_update_time': obj.constellation_configuration_strategy_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.constellation_configuration_strategy_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConstellationConfigurationStrategy data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'constellation_configuration_strategy_list': strategy_list
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
    def delete_constellation_configuration_strategy(request):
        """
        刪除 ConstellationConfigurationStrategy 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                constellation_configuration_strategy_uid = data.get('constellation_configuration_strategy_uid')

                if not constellation_configuration_strategy_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing constellation_configuration_strategy_uid parameter'
                    }, status=400)

                try:
                    obj = ConstellationConfigurationStrategy.objects.get(constellation_configuration_strategy_uid=constellation_configuration_strategy_uid)
                except ConstellationConfigurationStrategy.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConstellationConfigurationStrategy not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    'constellation_configuration_strategy_uid': str(obj.constellation_configuration_strategy_uid),
                    'constellation_configuration_strategy_name': obj.constellation_configuration_strategy_name,
                    'constellation_configuration_strategy_status': obj.constellation_configuration_strategy_status,
                    'constellation_configuration_strategy_parameter': obj.constellation_configuration_strategy_parameter,
                    'constellation_configuration_strategy_create_time': obj.constellation_configuration_strategy_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.constellation_configuration_strategy_create_time else None,
                    'constellation_configuration_strategy_update_time': obj.constellation_configuration_strategy_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.constellation_configuration_strategy_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConstellationConfigurationStrategy deleted successfully',
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
    def update_constellation_configuration_strategy(request):
        """
        更新 ConstellationConfigurationStrategy 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                constellation_configuration_strategy_uid = data.get('constellation_configuration_strategy_uid')

                if not constellation_configuration_strategy_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing constellation_configuration_strategy_uid parameter'
                    }, status=400)

                # 參數一旦建立就不可修改
                if 'constellation_configuration_strategy_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Strategy parameter cannot be modified'
                    }, status=400)

                try:
                    obj = ConstellationConfigurationStrategy.objects.get(constellation_configuration_strategy_uid=constellation_configuration_strategy_uid)
                except ConstellationConfigurationStrategy.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ConstellationConfigurationStrategy not found'
                    }, status=404)

                has_changes = False

                if 'constellation_configuration_strategy_name' in data and data['constellation_configuration_strategy_name'] != obj.constellation_configuration_strategy_name:
                    has_changes = True

                if 'constellation_configuration_strategy_status' in data and data['constellation_configuration_strategy_status'] != obj.constellation_configuration_strategy_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            'constellation_configuration_strategy_uid': str(obj.constellation_configuration_strategy_uid),
                            'constellation_configuration_strategy_name': obj.constellation_configuration_strategy_name,
                            'constellation_configuration_strategy_status': obj.constellation_configuration_strategy_status,
                            'constellation_configuration_strategy_parameter': obj.constellation_configuration_strategy_parameter,
                            'constellation_configuration_strategy_data_path': obj.constellation_configuration_strategy_data_path,
                            'constellation_configuration_strategy_create_time': obj.constellation_configuration_strategy_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'constellation_configuration_strategy_update_time': obj.constellation_configuration_strategy_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'constellation_configuration_strategy_name' in data:
                    obj.constellation_configuration_strategy_name = data['constellation_configuration_strategy_name']

                if 'constellation_configuration_strategy_status' in data:
                    obj.constellation_configuration_strategy_status = data['constellation_configuration_strategy_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'ConstellationConfigurationStrategy updated successfully',
                    'data': {
                        'id': obj.id,
                        'constellation_configuration_strategy_uid': str(obj.constellation_configuration_strategy_uid),
                        'constellation_configuration_strategy_name': obj.constellation_configuration_strategy_name,
                        'constellation_configuration_strategy_status': obj.constellation_configuration_strategy_status,
                        'constellation_configuration_strategy_parameter': obj.constellation_configuration_strategy_parameter,
                        'constellation_configuration_strategy_data_path': obj.constellation_configuration_strategy_data_path,
                        'constellation_configuration_strategy_create_time': obj.constellation_configuration_strategy_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'constellation_configuration_strategy_update_time': obj.constellation_configuration_strategy_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
