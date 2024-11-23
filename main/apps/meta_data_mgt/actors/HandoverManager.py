from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.HandoverModel import Handover
from main.utils.logger import log_trigger, log_writer
from django.views.decorators.csrf import csrf_exempt


class HandoverManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_handover(request):
        if request.method == 'POST':
            try:
                # 解析 JSON 數據
                data = json.loads(request.body)

                # 獲取必要的參數
                handover_name = data.get('handover_name')
                handover_parameter = data.get('handover_parameter')
                f_user_uid = data.get('f_user_uid')

                # 驗證必要參數
                if not all([handover_name, handover_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                # 檢查是否存在相同的 handover_parameter
                existing_handover = Handover.objects.filter(
                    handover_parameter=handover_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_handover:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Handover with the same parameters already exists',
                        'existing_handover': {
                            'id': existing_handover.id,
                            'handover_uid': str(existing_handover.handover_uid),
                            'handover_name': existing_handover.handover_name,
                            'handover_status': existing_handover.handover_status,
                            'handover_parameter': existing_handover.handover_parameter
                        }
                    }, status=400)

                # 創建 Handover 實例
                handover = Handover.objects.create(
                    handover_name=handover_name,
                    handover_parameter=handover_parameter,
                    handover_status = "None",
                    f_user_uid_id=f_user_uid
                )

                # 返回成功響應
                return JsonResponse({
                    'status': 'success',
                    'message': 'Handover created successfully',
                    'data': {
                        'id': handover.id,
                        'handover_uid': str(handover.handover_uid),
                        'handover_name': handover.handover_name,
                        'handover_status': handover.handover_status,
                        'handover_parameter': handover.handover_parameter  # 添加這行
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
    def query_handoverData_by_user(request):
        if request.method == 'POST':
            try:
                # 解析 JSON 數據
                data = json.loads(request.body)

                # 獲取必要的參數
                user_uid = data.get('user_uid')

                # 驗證必要參數
                if not user_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing user_uid parameter'
                    }, status=400)

                # 先查找用戶
                try:
                    user = User.objects.get(user_uid=user_uid)
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'User not found'
                    }, status=404)

                # 查詢該用戶的所有交接資料
                # 修改這裡：使用 f_user_uid 而不是 f_user_rid
                handovers = Handover.objects.filter(f_user_uid=user_uid)

                # 準備回傳資料
                handover_list = []
                for handover in handovers:
                    handover_list.append({
                        'id': handover.id,
                        'handover_uid': str(handover.handover_uid),
                        'handover_name': handover.handover_name,
                        'handover_status': handover.handover_status,
                        'handover_parameter': handover.handover_parameter,
                        'handover_create_time': handover.handover_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if handover.handover_create_time else None,
                        'handover_update_time': handover.handover_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if handover.handover_update_time else None
                    })

                # 返回成功響應
                return JsonResponse({
                    'status': 'success',
                    'message': 'Handover data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'handovers': handover_list
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
    def delete_handover(request):
        if request.method == 'POST':
            try:
                # 解析 JSON 數據
                data = json.loads(request.body)

                # 獲取必要的參數
                handover_uid = data.get('handover_uid')

                # 驗證必要參數
                if not handover_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing handover_uid parameter'
                    }, status=400)

                # 查找要刪除的交接資料
                try:
                    handover = Handover.objects.get(handover_uid=handover_uid)
                except Handover.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Handover not found'
                    }, status=404)

                # 保存要返回的資料
                deleted_handover_info = {
                    'id': handover.id,
                    'handover_uid': str(handover.handover_uid),
                    'handover_name': handover.handover_name,
                    'handover_status': handover.handover_status,
                    'handover_parameter': handover.handover_parameter,
                    'handover_create_time': handover.handover_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if handover.handover_create_time else None,
                    'handover_update_time': handover.handover_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if handover.handover_update_time else None
                }

                # 執行刪除操作
                handover.delete()

                # 返回成功響應
                return JsonResponse({
                    'status': 'success',
                    'message': 'Handover deleted successfully',
                    'data': deleted_handover_info
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
    def update_handover(request):
        if request.method == 'POST':
            try:
                # 解析 JSON 數據
                data = json.loads(request.body)

                # 獲取必要的參數
                handover_uid = data.get('handover_uid')
                
                # 驗證必要參數
                if not handover_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing handover_uid parameter'
                    }, status=400)

                try:
                    # 獲取要更新的 Handover 實例
                    handover = Handover.objects.get(handover_uid=handover_uid)
                except Handover.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Handover not found'
                    }, status=404)

                # 檢查是否有任何更改
                has_changes = False
                
                # 比對每個欄位
                if 'handover_name' in data and data['handover_name'] != handover.handover_name:
                    has_changes = True
                
                if 'handover_parameter' in data and data['handover_parameter'] != handover.handover_parameter:
                    has_changes = True
                    # 檢查是否存在相同的 handover_parameter（排除當前記錄）
                    existing_handover = Handover.objects.filter(
                        handover_parameter=data['handover_parameter'],
                        f_user_uid=handover.f_user_uid
                    ).exclude(handover_uid=handover_uid).first()

                    if existing_handover:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Handover with the same parameters already exists',
                            'existing_handover': {
                                'id': existing_handover.id,
                                'handover_uid': str(existing_handover.handover_uid),
                                'handover_name': existing_handover.handover_name,
                                'handover_status': existing_handover.handover_status,
                                'handover_parameter': existing_handover.handover_parameter
                            }
                        }, status=400)

                if 'handover_status' in data and data['handover_status'] != handover.handover_status:
                    has_changes = True

                # 如果沒有任何更改
                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': handover.id,
                            'handover_uid': str(handover.handover_uid),
                            'handover_name': handover.handover_name,
                            'handover_status': handover.handover_status,
                            'handover_parameter': handover.handover_parameter,
                            'handover_create_time': handover.handover_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'handover_update_time': handover.handover_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                # 更新欄位
                if 'handover_name' in data:
                    handover.handover_name = data['handover_name']
                
                if 'handover_parameter' in data:
                    handover.handover_parameter = data['handover_parameter']

                if 'handover_status' in data:
                    handover.handover_status = data['handover_status']

                # 保存更新
                handover.save()

                # 返回成功響應
                return JsonResponse({
                    'status': 'success',
                    'message': 'Handover updated successfully',
                    'data': {
                        'id': handover.id,
                        'handover_uid': str(handover.handover_uid),
                        'handover_name': handover.handover_name,
                        'handover_status': handover.handover_status,
                        'handover_parameter': handover.handover_parameter,
                        'handover_create_time': handover.handover_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'handover_update_time': handover.handover_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
