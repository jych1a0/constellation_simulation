#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
此腳本用於自動化生成新的 SimJob Model 和其對應的 Manager (Actor)，
以及在指定的 urls.py 中自動插入 import 與 path 路由設定。

範例：
  python create_simjob_actor.py \
    --model_name "TestSatelliteSimJob" \
    --table_name "TestSatelliteSimJob" \
    --relative_parent_model "TestSatelliteModel" \
    --relative_parent_class "TestSatellite" \
    --db_column_to_field "test_satellite_uid" \
    --output_model_dir "./main/apps/simulation_data_mgt/models" \
    --output_actor_dir "./main/apps/simulation_data_mgt/actors" \
    --urls_file "./main/apps/simulation_data_mgt/api/urls.py"

參數說明：
- model_name：要生成的 SimJob Model 與 Actor (class) 名稱 (駝峰式) 
- table_name：資料表名稱 (db_table)
- relative_parent_model：SimJob 依賴的「上游 Model」.py 檔名（不含 .py 後綴）
- relative_parent_class：SimJob 依賴的上游 Model 類名
- db_column_to_field：SimJob 與上游 Model 關聯時，要對應的欄位，例如 "connection_time_simulation_uid"
- output_model_dir：要輸出 Model 檔案的資料夾路徑
- output_actor_dir：要輸出 Actor 檔案的資料夾路徑
- urls_file：要插入路由設定的 urls.py 檔案路徑

你可依專案實際需求進行調整。
"""

import argparse
import os
import re
from datetime import datetime

# === 1. Model 的模板（SimJob 版本） ===
# 依照你的範例 ConnectionTimeSimJobModel.py 的結構，可自行增修
MODEL_TEMPLATE = r'''from django.db import models
import uuid
from django.utils import timezone
from main.apps.meta_data_mgt.models.{PARENT_MODEL} import {PARENT_CLASS}

class {MODEL_NAME}(models.Model):
    id = models.AutoField(primary_key=True)
    {MODEL_VAR_PREFIX}_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    {MODEL_VAR_PREFIX}_process_id = models.IntegerField(null=True, blank=True)
    {MODEL_VAR_PREFIX}_start_time = models.DateTimeField(default=timezone.now)
    {MODEL_VAR_PREFIX}_end_time = models.DateTimeField(null=True, blank=True)
    {MODEL_VAR_PREFIX}_result = models.JSONField(null=True, blank=True)

    f_{MODEL_VAR_PREFIX_parent} = models.ForeignKey(
        {PARENT_CLASS},
        on_delete=models.CASCADE,
        to_field='{DB_COLUMN_TO_FIELD}',
        db_column='f_{MODEL_VAR_PREFIX_parent}'
    )

    class Meta:
        db_table = '{TABLE_NAME}'

    def __str__(self):
        return f'{MODEL_NAME}(uid={{self.{MODEL_VAR_PREFIX}_uid}})'
'''

# === 2. Manager (Actor) 的模板 ===
# 依照你的 SimJob Manager 需求客製
ACTOR_TEMPLATE = r'''import json
import os
import threading
import time
import subprocess
import shutil
from pathlib import Path

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from main.utils.logger import log_trigger, log_writer

from main.apps.meta_data_mgt.models.{PARENT_MODEL} import {PARENT_CLASS}
from main.apps.simulation_data_mgt.models.{MODEL_NAME}Model import {MODEL_NAME}

class {MODEL_NAME}Manager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_{MODEL_VAR_PREFIX}(request):
        """
        建立並啟動 {MODEL_NAME} (SimJob) 執行
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                parent_uid = data.get('{DB_COLUMN_TO_FIELD}')

                if not parent_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing {DB_COLUMN_TO_FIELD} parameter'
                    }, status=400)

                # 取得上游主表（ex: ConnectionTimeSimulation）
                try:
                    parent_obj = {PARENT_CLASS}.objects.get({DB_COLUMN_TO_FIELD}=parent_uid)
                except {PARENT_CLASS}.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parent object not found'
                    }, status=404)

                # 檢查是否已有未結束的任務
                current_job = {MODEL_NAME}.objects.filter(
                    f_{MODEL_VAR_PREFIX_parent}=parent_obj,
                    {MODEL_VAR_PREFIX}_end_time__isnull=True
                ).first()

                if current_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'There is already a running job for this parent object',
                        'data': {
                            '{MODEL_VAR_PREFIX}_uid': str(current_job.{MODEL_VAR_PREFIX}_uid)
                        }
                    })

                # 建立 Job
                new_job = {MODEL_NAME}.objects.create(
                    f_{MODEL_VAR_PREFIX_parent}=parent_obj,
                    {MODEL_VAR_PREFIX}_start_time=timezone.now()
                )

                # 在此自行啟動執行緒 / Docker / 其他流程
                simulation_thread = threading.Thread(
                    target=async_{MODEL_VAR_PREFIX}_task,
                    args=(new_job.{MODEL_VAR_PREFIX}_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': f'{MODEL_NAME} job is started',
                    'data': {
                        '{MODEL_VAR_PREFIX}_uid': str(new_job.{MODEL_VAR_PREFIX}_uid)
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

    @csrf_exempt
    @log_trigger('INFO')
    def delete_{MODEL_VAR_PREFIX}_result(request):
        """
        刪除 {MODEL_NAME} 相關結果
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                parent_uid = data.get('{DB_COLUMN_TO_FIELD}')

                if not parent_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing {DB_COLUMN_TO_FIELD} parameter'
                    }, status=400)

                try:
                    parent_obj = {PARENT_CLASS}.objects.get({DB_COLUMN_TO_FIELD}=parent_uid)
                except {PARENT_CLASS}.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parent object not found'
                    }, status=404)

                # 刪除所有 Job
                {MODEL_NAME}.objects.filter(f_{MODEL_VAR_PREFIX_parent}=parent_obj).delete()

                # 此處可依需求刪除檔案資料夾
                # full_path = ...
                # if os.path.exists(full_path):
                #     shutil.rmtree(full_path)

                return JsonResponse({
                    'status': 'success',
                    'message': 'Job results deleted successfully'
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

    @csrf_exempt
    @log_trigger('INFO')
    def download_{MODEL_VAR_PREFIX}_result(request):
        """
        範例：下載 {MODEL_NAME} 的結果檔案
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                parent_uid = data.get('{DB_COLUMN_TO_FIELD}')

                if not parent_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing {DB_COLUMN_TO_FIELD} parameter'
                    }, status=400)

                # 假設要讀取產生的檔案
                # ex: pdf_path = ...
                # if not os.path.exists(pdf_path):
                #     return JsonResponse({
                #         'status': 'error',
                #         'message': 'File not found'
                #     }, status=404)

                # with open(pdf_path, 'rb') as f:
                #     response = HttpResponse(f.read(), content_type='application/pdf')
                #     response['Content-Disposition'] = 'attachment; filename="result.pdf"'
                #     return response

                return JsonResponse({
                    'status': 'success',
                    'message': 'Download simulation result example'
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


def async_{MODEL_VAR_PREFIX}_task(job_uid):
    """
    這裡示範非同步執行模擬或其他處理邏輯。
    """
    try:
        job_obj = {MODEL_NAME}.objects.get({MODEL_VAR_PREFIX}_uid=job_uid)
        # 模擬執行邏輯 ...
        time.sleep(5)  # 假裝跑 5 秒

        # 更新 job 狀態
        job_obj.{MODEL_VAR_PREFIX}_end_time = timezone.now()
        job_obj.{MODEL_VAR_PREFIX}_result = {
            "message": "Simulation completed",
            "timestamp": str(timezone.now())
        }
        job_obj.save()
        print(f"[INFO] {MODEL_NAME} job ({job_uid}) completed.")

    except Exception as e:
        print(f"[ERROR] {MODEL_NAME} job execution failed: {{str(e)}}")
'''


# === 3. 自動插入 import 與路由 (urls.py) 的模板 ===
IMPORT_SNIPPET = r'''from main.apps.simulation_data_mgt.actors.{MODEL_NAME}Manager import {MODEL_NAME}Manager
'''

URLS_SNIPPET = r'''
# 以下由腳本插入 {MODEL_NAME}
path('simulation_data_mgt/{MODEL_VAR_PREFIX}Manager/run_{MODEL_VAR_PREFIX}',
     {MODEL_NAME}Manager.run_{MODEL_VAR_PREFIX},
     name="run_{MODEL_VAR_PREFIX}"),

path('simulation_data_mgt/{MODEL_VAR_PREFIX}Manager/delete_{MODEL_VAR_PREFIX}_result',
     {MODEL_NAME}Manager.delete_{MODEL_VAR_PREFIX}_result,
     name="delete_{MODEL_VAR_PREFIX}_result"),

path('simulation_data_mgt/{MODEL_VAR_PREFIX}Manager/download_{MODEL_VAR_PREFIX}_result',
     {MODEL_NAME}Manager.download_{MODEL_VAR_PREFIX}_result,
     name="download_{MODEL_VAR_PREFIX}_result"),
'''

def replace_placeholders(template_str, model_name, table_name, 
                         parent_model, parent_class, db_column):
    """
    依據參數替換模板中的 {MODEL_NAME}, {MODEL_VAR_PREFIX}, {TABLE_NAME}, {PARENT_MODEL}, {PARENT_CLASS}, {DB_COLUMN_TO_FIELD}, ...
    """
    model_var_prefix = camel_to_snake(model_name)
    model_var_prefix_parent = camel_to_snake(parent_class)
    replaced = (template_str
        .replace("{MODEL_NAME}", model_name)
        .replace("{MODEL_VAR_PREFIX}", model_var_prefix)
        .replace("{MODEL_VAR_PREFIX_parent}", model_var_prefix_parent)
        .replace("{TABLE_NAME}", table_name)
        .replace("{PARENT_MODEL}", parent_model)    # e.g. ConnectionTimeSimulationModel
        .replace("{PARENT_CLASS}", parent_class)    # e.g. ConnectionTimeSimulation
        .replace("{DB_COLUMN_TO_FIELD}", db_column) # e.g. connection_time_simulation_uid
    )
    return replaced

def camel_to_snake(camel_str):
    """
    將駝峰字串轉成小寫蛇底線
    e.g. "ConnectionTimeSimJob" -> "connection_time_sim_job"
    """
    if '_' in camel_str:
        return camel_str.lower()
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    return snake

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', required=True, help='新 SimJob Model (Class) 名稱, e.g.: ConnectionTimeSimJob')
    parser.add_argument('--table_name', required=True, help='資料表名稱 (db_table)')
    parser.add_argument('--relative_parent_model', required=True, help='上游 Model 檔名, e.g. ConnectionTimeSimulationModel')
    parser.add_argument('--relative_parent_class', required=True, help='上游 Model 類名, e.g. ConnectionTimeSimulation')
    parser.add_argument('--db_column_to_field', required=True, help='對應 foreign key 的 to_field, e.g. connection_time_simulation_uid')
    parser.add_argument('--output_model_dir', required=True, help='輸出 Model 檔案的資料夾路徑')
    parser.add_argument('--output_actor_dir', required=True, help='輸出 Actor 檔案的資料夾路徑')
    parser.add_argument('--urls_file', required=True, help='要插入路由設定的 urls.py 檔案路徑')
    args = parser.parse_args()

    model_name = args.model_name
    table_name = args.table_name
    parent_model = args.relative_parent_model
    parent_class = args.relative_parent_class
    db_column = args.db_column_to_field
    output_model_dir = args.output_model_dir
    output_actor_dir = args.output_actor_dir
    urls_file = args.urls_file

    # 產出檔名
    model_file_name = f"{model_name}Model.py"
    actor_file_name = f"{model_name}Manager.py"

    # 1) 生成 Model
    model_content = replace_placeholders(
        MODEL_TEMPLATE, 
        model_name, 
        table_name, 
        parent_model, 
        parent_class, 
        db_column
    )

    # 2) 生成 Manager
    actor_content = replace_placeholders(
        ACTOR_TEMPLATE, 
        model_name, 
        table_name, 
        parent_model, 
        parent_class, 
        db_column
    )

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

    # 5) 更新 urls.py：插入 import 與 path
    import_snippet = replace_placeholders(
        IMPORT_SNIPPET, 
        model_name, 
        table_name, 
        parent_model, 
        parent_class, 
        db_column
    )
    urls_snippet = replace_placeholders(
        URLS_SNIPPET, 
        model_name, 
        table_name, 
        parent_model, 
        parent_class, 
        db_column
    )

    if not os.path.exists(urls_file):
        print(f"[WARNING] urls.py not found: {urls_file}")
        return

    with open(urls_file, 'r', encoding='utf-8') as f:
        original_urls = f.read()

    # (a) 在urlpatterns = [ 上方插入 import_snippet
    urlpatterns_marker = "urlpatterns = ["
    idx = original_urls.find(urlpatterns_marker)
    if idx == -1:
        print("[ERROR] Cannot find 'urlpatterns = [' in urls.py. Please insert manually.")
        return

    new_urls_content = (
        original_urls[:idx]
        + import_snippet
        + "\n"
        + original_urls[idx:]
    )

    # (b) 找到最後一個 "]" 以插入 urls_snippet
    last_bracket_index = new_urls_content.rfind("]")
    if last_bracket_index == -1:
        print("[ERROR] Cannot find ']' in urls.py. Please insert manually.")
        return

    final_urls_content = (
        new_urls_content[:last_bracket_index]
        + urls_snippet
        + "\n"
        + new_urls_content[last_bracket_index:]
    )

    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write(final_urls_content)

    print("[INFO] Import & path snippet inserted into", urls_file)
    print("[INFO] Done.")

def camel_to_snake(camel_str):
    """
    將駝峰字串轉成小寫蛇底線
    e.g.: "ConnectionTimeSimJob" -> "connection_time_sim_job"
    """
    if '_' in camel_str:
        return camel_str.lower()
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    return snake


if __name__ == "__main__":
    main()
