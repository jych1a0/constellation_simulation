#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
此腳本用於自動化生成新的 Metadata Model 和其對應的 Actor (Manager) 
以及在 urls.py 中自動插入路由設定。

使用方式：
  python create_metadata_actor.py \
    --model_name "TestSatellite" \
    --table_name "TestSatellite" \
    --output_model_dir "./main/apps/meta_data_mgt/models" \
    --output_actor_dir "./main/apps/meta_data_mgt/actors" \
    --urls_file "./main/apps/meta_data_mgt/api/urls.py"

參數說明：
- model_name：新 Model/Actor 的 class 名稱 (駝峰式，如 CoverageAnalysis) 
- table_name：資料表名稱 (資料庫內實際的 db_table 名稱)
- output_model_dir：要輸出 Model 檔案的資料夾路徑
- output_actor_dir：要輸出 Actor 檔案的資料夾路徑
- urls_file：要插入路由設定的 urls.py 路徑
"""

import argparse
import os
import re
from datetime import datetime

MODEL_TEMPLATE = r'''from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.UserModel import User

class {MODEL_NAME}(models.Model):
    id = models.AutoField(primary_key=True)
    {MODEL_VAR_PREFIX}_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    {MODEL_VAR_PREFIX}_name = models.CharField(max_length=255)
    {MODEL_VAR_PREFIX}_parameter = models.JSONField()  # 使用 JSONField 來儲存 JSON 格式的參數
    {MODEL_VAR_PREFIX}_status = models.CharField(max_length=50)
    {MODEL_VAR_PREFIX}_data_path = models.CharField(max_length=255)
    {MODEL_VAR_PREFIX}_create_time = models.DateTimeField(default=timezone.now)
    {MODEL_VAR_PREFIX}_update_time = models.DateTimeField(auto_now=True)
    {MODEL_VAR_PREFIX}_result = models.JSONField(null=True, blank=True)

    # 外鍵連至 UserModel
    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',       # 關聯到 User 表的 user_uid 欄位
        db_column='f_user_uid'     # 指定資料庫中的欄位名稱
    )

    class Meta:
        db_table = '{TABLE_NAME}'  # 指定資料表名稱

    def save(self, *args, **kwargs):
        # 如果是新建實例（沒有 id）或 {MODEL_VAR_PREFIX}_data_path 為空，則自動生成
        if not self.id or not self.{MODEL_VAR_PREFIX}_data_path:
            self.{MODEL_VAR_PREFIX}_data_path = (
                f"{MODEL_VAR_PREFIX}/{self.f_user_uid.user_uid}/{self.{MODEL_VAR_PREFIX}_uid}"
            )
        super().save(*args, **kwargs)
'''

ACTOR_TEMPLATE = r'''from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.{MODEL_NAME}Model import {MODEL_NAME}
from main.utils.logger import log_trigger, log_writer
import os
import threading

class {MODEL_NAME}Manager:

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_{MODEL_VAR_PREFIX}(request):
        """
        建立 {MODEL_NAME} 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                {MODEL_VAR_PREFIX}_name = data.get('{MODEL_VAR_PREFIX}_name')
                {MODEL_VAR_PREFIX}_parameter = data.get('{MODEL_VAR_PREFIX}_parameter')
                f_user_uid = data.get('f_user_uid')

                # 檢查必填參數
                if not all([{MODEL_VAR_PREFIX}_name, {MODEL_VAR_PREFIX}_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                # 檢查是否有相同參數的資料
                existing_obj = {MODEL_NAME}.objects.filter(
                    {MODEL_VAR_PREFIX}_parameter={MODEL_VAR_PREFIX}_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_obj:
                    return JsonResponse({
                        'status': 'error',
                        'message': '{MODEL_NAME} with the same parameters already exists',
                        'existing_{MODEL_VAR_PREFIX}': {
                            'id': existing_obj.id,
                            '{MODEL_VAR_PREFIX}_uid': str(existing_obj.{MODEL_VAR_PREFIX}_uid),
                            '{MODEL_VAR_PREFIX}_name': existing_obj.{MODEL_VAR_PREFIX}_name,
                            '{MODEL_VAR_PREFIX}_status': existing_obj.{MODEL_VAR_PREFIX}_status,
                            '{MODEL_VAR_PREFIX}_parameter': existing_obj.{MODEL_VAR_PREFIX}_parameter,
                            '{MODEL_VAR_PREFIX}_data_path': existing_obj.{MODEL_VAR_PREFIX}_data_path
                        }
                    }, status=400)

                new_obj = {MODEL_NAME}.objects.create(
                    {MODEL_VAR_PREFIX}_name={MODEL_VAR_PREFIX}_name,
                    {MODEL_VAR_PREFIX}_parameter={MODEL_VAR_PREFIX}_parameter,
                    {MODEL_VAR_PREFIX}_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': '{MODEL_NAME} created successfully',
                    'data': {
                        'id': new_obj.id,
                        '{MODEL_VAR_PREFIX}_uid': str(new_obj.{MODEL_VAR_PREFIX}_uid),
                        '{MODEL_VAR_PREFIX}_name': new_obj.{MODEL_VAR_PREFIX}_name,
                        '{MODEL_VAR_PREFIX}_status': new_obj.{MODEL_VAR_PREFIX}_status,
                        '{MODEL_VAR_PREFIX}_parameter': new_obj.{MODEL_VAR_PREFIX}_parameter,
                        '{MODEL_VAR_PREFIX}_data_path': new_obj.{MODEL_VAR_PREFIX}_data_path
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
    def query_{MODEL_VAR_PREFIX}_by_user(request):
        """
        依照 user_uid 查詢 {MODEL_NAME}
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

                query_set = {MODEL_NAME}.objects.filter(f_user_uid=user_uid)

                result_list = []
                for obj in query_set:
                    result_list.append({
                        'id': obj.id,
                        '{MODEL_VAR_PREFIX}_uid': str(obj.{MODEL_VAR_PREFIX}_uid),
                        '{MODEL_VAR_PREFIX}_name': obj.{MODEL_VAR_PREFIX}_name,
                        '{MODEL_VAR_PREFIX}_status': obj.{MODEL_VAR_PREFIX}_status,
                        '{MODEL_VAR_PREFIX}_parameter': obj.{MODEL_VAR_PREFIX}_parameter,
                        '{MODEL_VAR_PREFIX}_data_path': obj.{MODEL_VAR_PREFIX}_data_path,
                        '{MODEL_VAR_PREFIX}_result': obj.{MODEL_VAR_PREFIX}_result,
                        '{MODEL_VAR_PREFIX}_create_time': obj.{MODEL_VAR_PREFIX}_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.{MODEL_VAR_PREFIX}_create_time else None,
                        '{MODEL_VAR_PREFIX}_update_time': obj.{MODEL_VAR_PREFIX}_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.{MODEL_VAR_PREFIX}_update_time else None
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': '{MODEL_NAME} data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        '{MODEL_VAR_PREFIX}_list': result_list
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
    def delete_{MODEL_VAR_PREFIX}(request):
        """
        刪除 {MODEL_NAME} 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                {MODEL_VAR_PREFIX}_uid = data.get('{MODEL_VAR_PREFIX}_uid')

                if not {MODEL_VAR_PREFIX}_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing {MODEL_VAR_PREFIX}_uid parameter'
                    }, status=400)

                try:
                    obj = {MODEL_NAME}.objects.get({MODEL_VAR_PREFIX}_uid={MODEL_VAR_PREFIX}_uid)
                except {MODEL_NAME}.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '{MODEL_NAME} not found'
                    }, status=404)

                deleted_info = {
                    'id': obj.id,
                    '{MODEL_VAR_PREFIX}_uid': str(obj.{MODEL_VAR_PREFIX}_uid),
                    '{MODEL_VAR_PREFIX}_name': obj.{MODEL_VAR_PREFIX}_name,
                    '{MODEL_VAR_PREFIX}_status': obj.{MODEL_VAR_PREFIX}_status,
                    '{MODEL_VAR_PREFIX}_parameter': obj.{MODEL_VAR_PREFIX}_parameter,
                    '{MODEL_VAR_PREFIX}_create_time': obj.{MODEL_VAR_PREFIX}_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.{MODEL_VAR_PREFIX}_create_time else None,
                    '{MODEL_VAR_PREFIX}_update_time': obj.{MODEL_VAR_PREFIX}_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if obj.{MODEL_VAR_PREFIX}_update_time else None
                }

                obj.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': '{MODEL_NAME} deleted successfully',
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
    def update_{MODEL_VAR_PREFIX}(request):
        """
        更新 {MODEL_NAME} 資料
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                {MODEL_VAR_PREFIX}_uid = data.get('{MODEL_VAR_PREFIX}_uid')

                if not {MODEL_VAR_PREFIX}_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing {MODEL_VAR_PREFIX}_uid parameter'
                    }, status=400)

                # 參數一旦建立就不可修改
                if '{MODEL_VAR_PREFIX}_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parameter cannot be modified'
                    }, status=400)

                try:
                    obj = {MODEL_NAME}.objects.get({MODEL_VAR_PREFIX}_uid={MODEL_VAR_PREFIX}_uid)
                except {MODEL_NAME}.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '{MODEL_NAME} not found'
                    }, status=404)

                has_changes = False

                if '{MODEL_VAR_PREFIX}_name' in data and data['{MODEL_VAR_PREFIX}_name'] != obj.{MODEL_VAR_PREFIX}_name:
                    has_changes = True

                if '{MODEL_VAR_PREFIX}_status' in data and data['{MODEL_VAR_PREFIX}_status'] != obj.{MODEL_VAR_PREFIX}_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': obj.id,
                            '{MODEL_VAR_PREFIX}_uid': str(obj.{MODEL_VAR_PREFIX}_uid),
                            '{MODEL_VAR_PREFIX}_name': obj.{MODEL_VAR_PREFIX}_name,
                            '{MODEL_VAR_PREFIX}_status': obj.{MODEL_VAR_PREFIX}_status,
                            '{MODEL_VAR_PREFIX}_parameter': obj.{MODEL_VAR_PREFIX}_parameter,
                            '{MODEL_VAR_PREFIX}_data_path': obj.{MODEL_VAR_PREFIX}_data_path,
                            '{MODEL_VAR_PREFIX}_create_time': obj.{MODEL_VAR_PREFIX}_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            '{MODEL_VAR_PREFIX}_update_time': obj.{MODEL_VAR_PREFIX}_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if '{MODEL_VAR_PREFIX}_name' in data:
                    obj.{MODEL_VAR_PREFIX}_name = data['{MODEL_VAR_PREFIX}_name']

                if '{MODEL_VAR_PREFIX}_status' in data:
                    obj.{MODEL_VAR_PREFIX}_status = data['{MODEL_VAR_PREFIX}_status']

                obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': '{MODEL_NAME} updated successfully',
                    'data': {
                        'id': obj.id,
                        '{MODEL_VAR_PREFIX}_uid': str(obj.{MODEL_VAR_PREFIX}_uid),
                        '{MODEL_VAR_PREFIX}_name': obj.{MODEL_VAR_PREFIX}_name,
                        '{MODEL_VAR_PREFIX}_status': obj.{MODEL_VAR_PREFIX}_status,
                        '{MODEL_VAR_PREFIX}_parameter': obj.{MODEL_VAR_PREFIX}_parameter,
                        '{MODEL_VAR_PREFIX}_data_path': obj.{MODEL_VAR_PREFIX}_data_path,
                        '{MODEL_VAR_PREFIX}_create_time': obj.{MODEL_VAR_PREFIX}_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        '{MODEL_VAR_PREFIX}_update_time': obj.{MODEL_VAR_PREFIX}_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
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
'''

IMPORT_SNIPPET = r'''from main.apps.meta_data_mgt.actors.{MODEL_NAME}Manager import {MODEL_NAME}Manager
'''

URLS_TEMPLATE = r'''
# 以下由自動腳本插入
path('meta_data_mgt/{MODEL_NAME}Manager/create_{MODEL_VAR_PREFIX}',
     {MODEL_NAME}Manager.create_{MODEL_VAR_PREFIX},
     name="create_{MODEL_VAR_PREFIX}"),
path('meta_data_mgt/{MODEL_NAME}Manager/query_{MODEL_VAR_PREFIX}_by_user',
     {MODEL_NAME}Manager.query_{MODEL_VAR_PREFIX}_by_user,
     name="query_{MODEL_VAR_PREFIX}_by_user"),
path('meta_data_mgt/{MODEL_NAME}Manager/delete_{MODEL_VAR_PREFIX}',
     {MODEL_NAME}Manager.delete_{MODEL_VAR_PREFIX},
     name="delete_{MODEL_VAR_PREFIX}"),
path('meta_data_mgt/{MODEL_NAME}Manager/update_{MODEL_VAR_PREFIX}',
     {MODEL_NAME}Manager.update_{MODEL_VAR_PREFIX},
     name="update_{MODEL_VAR_PREFIX}"),
'''

def replace_placeholders(template_str, model_name, table_name):
    """
    根據參數替換模板中 {MODEL_NAME}, {MODEL_VAR_PREFIX}, {TABLE_NAME} 等佔位符
    其中 MODEL_VAR_PREFIX 是將 model_name 轉小寫蛇底線或部分命名
    """
    # 這裡假設: 駝峰命名 => 小寫蛇底線
    # 例如: MyNewMetadata => my_new_metadata
    # 你可以依自己需求客製
    model_var_prefix = camel_to_snake(model_name)

    replaced = (template_str
        .replace("{MODEL_NAME}", model_name)
        .replace("{MODEL_VAR_PREFIX}", model_var_prefix)
        .replace("{TABLE_NAME}", table_name)
    )
    return replaced

def camel_to_snake(camel_str):
    """
    簡易將駝峰字串轉成小寫蛇底線
    e.g. "CoverageAnalysis" -> "coverage_analysis"
    """
    # 若已經是全小寫 or 有底線的，就直接返回
    if '_' in camel_str:
        return camel_str.lower()

    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    return snake

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', required=True, help='新 Model (Class) 名稱, e.g.: CoverageAnalysis')
    parser.add_argument('--table_name', required=True, help='資料表名稱 (db_table)')
    parser.add_argument('--output_model_dir', required=True, help='輸出 Model 檔案的資料夾路徑')
    parser.add_argument('--output_actor_dir', required=True, help='輸出 Actor 檔案的資料夾路徑')
    parser.add_argument('--urls_file', required=True, help='要插入路由設定的 urls.py 檔案路徑')
    args = parser.parse_args()

    model_name = args.model_name
    table_name = args.table_name
    output_model_dir = args.output_model_dir
    output_actor_dir = args.output_actor_dir
    urls_file = args.urls_file

    # 生成 Model.py 檔名, e.g.: CoverageAnalysisModel.py
    model_file_name = f"{model_name}Model.py"
    # 生成 Actor.py 檔名, e.g.: CoverageAnalysisManager.py
    actor_file_name = f"{model_name}Manager.py"

    # 1) 產生 Model 檔內容
    model_content = replace_placeholders(MODEL_TEMPLATE, model_name, table_name)

    # 2) 產生 Actor 檔內容
    actor_content = replace_placeholders(ACTOR_TEMPLATE, model_name, table_name)

    # 3) 寫出 Model 檔
    if not os.path.exists(output_model_dir):
        os.makedirs(output_model_dir, exist_ok=True)
    model_path = os.path.join(output_model_dir, model_file_name)

    with open(model_path, 'w', encoding='utf-8') as f:
        f.write(model_content)
    print(f"[INFO] Model file created: {model_path}")

    # 4) 寫出 Actor 檔
    if not os.path.exists(output_actor_dir):
        os.makedirs(output_actor_dir, exist_ok=True)
    actor_path = os.path.join(output_actor_dir, actor_file_name)

    with open(actor_path, 'w', encoding='utf-8') as f:
        f.write(actor_content)
    print(f"[INFO] Actor file created: {actor_path}")

    # 5) 在 urls.py 插入路由
    import_snippet = replace_placeholders(IMPORT_SNIPPET, model_name, table_name)
    url_snippet = replace_placeholders(URLS_TEMPLATE, model_name, table_name)

    if not os.path.exists(urls_file):
        print(f"[WARNING] urls.py not found: {urls_file}")
        return

    # 讀取 urls.py 內容
    with open(urls_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # (a) 在 urlpatterns = [ 之前，插入 import_snippet
    urlpatterns_marker = "urlpatterns = ["
    idx = content.find(urlpatterns_marker)
    if idx == -1:
        print("[ERROR] Cannot find 'urlpatterns = [' in urls.py. Please insert manually.")
        return

    # 在該行最前面插入 import_snippet（帶換行）
    new_content = (
        content[:idx] 
        + import_snippet 
        + "\n"
        + content[idx:]
    )

    # (b) 找最後一個 "]" 以插入路由
    last_bracket_index = new_content.rfind("]")
    if last_bracket_index == -1:
        print("[ERROR] Cannot find ']' in urls.py. Please insert manually.")
        return

    # 在最後一個 "]" 前插入 url_snippet
    final_content = (
        new_content[:last_bracket_index]
        + url_snippet
        + "\n"
        + new_content[last_bracket_index:]
    )

    # 寫回 urls.py
    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"[INFO] Successfully inserted import and route snippet into {urls_file}")

if __name__ == "__main__":
    main()
