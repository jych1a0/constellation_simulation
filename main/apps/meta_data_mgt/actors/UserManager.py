from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.http import require_http_methods
from main.utils.logger import log_trigger, log_writer
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from main.apps.meta_data_mgt.models.UserModel import User
from django.views.decorators.csrf import csrf_exempt
import json
import hashlib
from django.utils import timezone


class UserManager:
    @log_trigger('INFO')  # 作為裝飾器使用
    @require_http_methods(["GET"])
    def get_hello_world(request):
        try:
            return JsonResponse({
                "message": "Hello, World!"
            })
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def login_user(request):
        try:
            data = json.loads(request.body)

            # 檢查必要欄位
            required_fields = ['user_name', 'user_password']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Missing required field: {field}"
                    }, status=400)

            # 查找用戶
            try:
                user = User.objects.get(user_name=data['user_name'])
            except User.DoesNotExist:
                return JsonResponse({
                    "status": "error",
                    "message": "User not found"
                }, status=400)

            # 驗證密碼
            if check_password(data['user_password'], user.user_password):
                # 直接在這裡更新最近登入時間
                user.last_login_time = timezone.now()
                user.save()

                return JsonResponse({
                    "status": "success",
                    "data": {
                        "user_uid": str(user.user_uid),
                        "user_name": user.user_name,
                        "user_email": user.user_email,
                        "last_login_time": user.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_time else None
                    }
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid password"
                }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON format"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_user(request):
        try:
            data = json.loads(request.body)

            # 檢查必要欄位
            required_fields = ['user_name', 'user_password', 'user_email']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Missing required field: {field}"
                    }, status=400)

            # 檢查用戶名和郵箱是否已存在
            if User.objects.filter(user_name=data['user_name']).exists():
                return JsonResponse({
                    "status": "error",
                    "message": "Username already exists"
                }, status=400)

            if User.objects.filter(user_email=data['user_email']).exists():
                return JsonResponse({
                    "status": "error",
                    "message": "Email already exists"
                }, status=400)

            # 在這裡進行密碼雜湊
            hashed_password = make_password(data['user_password'])

            # 創建新用戶
            user = User.objects.create(
                user_name=data['user_name'],
                user_password=hashed_password,  # 使用已經雜湊的密碼
                user_email=data['user_email']
            )

            return JsonResponse({
                "status": "success",
                "data": {
                    "id": user.id,
                    "user_uid": str(user.user_uid),
                    "user_name": user.user_name,
                    "user_email": user.user_email
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON format"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def delete_user(request):
        try:
            # 從 POST 請求體中獲取數據
            data = json.loads(request.body)
            user_uid = data.get('user_uid')

            if not user_uid:
                return JsonResponse({
                    "status": "error",
                    "message": "user_uid is required"
                }, status=400)

            try:
                user = User.objects.get(user_uid=user_uid)
                user.delete()
                return JsonResponse({
                    "status": "success",
                    "message": "User deleted successfully"
                })
            except ObjectDoesNotExist:
                return JsonResponse({
                    "status": "error",
                    "message": "User not found"
                }, status=404)

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON format"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["GET"])
    def query_user(request):
        try:
            # 支援多種查詢參數
            user_uid = request.GET.get('user_uid')
            user_name = request.GET.get('user_name')
            user_email = request.GET.get('user_email')

            # 構建查詢條件
            query = {}
            if user_uid:
                query['user_uid'] = user_uid
            if user_name:
                query['user_name'] = user_name
            if user_email:
                query['user_email'] = user_email

            if not query:
                # 如果沒有查詢參數，返回所有用戶（可能需要分頁）
                users = User.objects.all()
            else:
                users = User.objects.filter(**query)

            # 轉換查詢結果為列表
            users_list = [{
                'id': user.id,
                'user_uid': str(user.user_uid),
                'user_name': user.user_name,
                'user_email': user.user_email,
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
            } for user in users]

            return JsonResponse({
                "status": "success",
                "data": users_list
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
