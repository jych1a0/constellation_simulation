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
ACTOR_TEMPLATE = r'''from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json
import os
import threading
from django.utils import timezone
import subprocess
import time
import shutil
import glob
from pathlib import Path

from main.utils.logger import log_trigger, log_writer

from main.apps.meta_data_mgt.models.{PARENT_MODEL} import {PARENT_CLASS}
from main.apps.simulation_data_mgt.models.{MODEL_NAME}Model import {MODEL_NAME}

############################################
# 1) 終止模擬：Docker Container + Job 處理 #
############################################
@log_trigger('INFO')
def terminate_{MODEL_VAR_PREFIX}(parent_uid):
    try:
        parent_obj = {PARENT_CLASS}.objects.get({DB_COLUMN_TO_FIELD}=parent_uid)

        # 找出尚未結束的 job
        sim_jobs = {MODEL_NAME}.objects.filter(
            f_{MODEL_VAR_PREFIX_parent}=parent_obj,
            {MODEL_VAR_PREFIX}_end_time__isnull=True
        )

        container_name = f"{MODEL_VAR_PREFIX}Simulation_{{parent_uid}}"

        # 嘗試停止並移除 Docker container
        try:
            subprocess.run(
                ['docker', 'stop', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            subprocess.run(
                ['docker', 'rm', '-f', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
        except subprocess.TimeoutExpired:
            subprocess.run(
                ['docker', 'rm', '-f', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"[ERROR] Docker container stop error: {{str(e)}}")

        # 刪除 or 標註結束未完成的 job
        sim_jobs.delete()

        # 更新主表狀態 (若有需要)
        parent_obj.{MODEL_VAR_PREFIX_parent}_status = "simulation_failed"
        parent_obj.save()

        print(f"[INFO] All related jobs terminated for {MODEL_NAME} parent_uid: {{parent_uid}}")
        return True

    except Exception as e:
        print(f"[ERROR] {MODEL_NAME} job termination error: {{str(e)}}")
        return False


############################################################
# 2) 非同步執行：執行 Docker、檔案複製、狀態更新等完整流程 #
############################################################
@log_trigger('INFO')
def run_{MODEL_VAR_PREFIX}_async(parent_uid):
    sim_job = None
    try:
        parent_obj = {PARENT_CLASS}.objects.get({DB_COLUMN_TO_FIELD}=parent_uid)

        # 建立 Job 紀錄
        sim_job = {MODEL_NAME}.objects.create(
            f_{MODEL_VAR_PREFIX_parent}=parent_obj,
            {MODEL_VAR_PREFIX}_start_time=timezone.now()
        )

        # 更新主表狀態
        parent_obj.{MODEL_VAR_PREFIX_parent}_status = "processing"
        parent_obj.save()

        # 建立結果目錄 (可依需求命名)
        simulation_result_dir = os.path.join(
            'simulation_result',
            '{MODEL_VAR_PREFIX}_simulation',
            str(parent_obj.f_user_uid.user_uid) if hasattr(parent_obj, 'f_user_uid') else 'unknown_user',
            str(parent_uid)
        )
        os.makedirs(simulation_result_dir, exist_ok=True)
        print(f"[INFO] Simulation result directory: {{simulation_result_dir}}")

        # 準備 Docker Container 名稱
        container_name = f"{MODEL_VAR_PREFIX}Simulation_{{parent_uid}}"

        # 準備模擬參數 (JSON)
        # 假設主表欄位為 parent_obj.{MODEL_VAR_PREFIX_parent}_parameter
        if isinstance(parent_obj.{MODEL_VAR_PREFIX_parent}_parameter, dict):
            json_params = json.dumps(parent_obj.{MODEL_VAR_PREFIX_parent}_parameter)
        else:
            try:
                json_params = json.dumps(json.loads(parent_obj.{MODEL_VAR_PREFIX_parent}_parameter))
            except json.JSONDecodeError:
                json_params = parent_obj.{MODEL_VAR_PREFIX_parent}_parameter

        # Docker 命令示範：可自行修改 image, script, volume 等
        docker_cmd = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '28g',
            '--rm',
            '--name', container_name,
            '-v', f'{{os.path.abspath(simulation_result_dir)}}:/root/mercury/build/service/output',
            'coverage_analysis_simulation:latest',
            'bash', '-c',
            f'/root/mercury/shell/simulation_script.sh \'{json_params}\' && '
            f'cp -r /root/mercury/build/service/*.csv /root/mercury/build/service/output/'
        ]

        print(f"[INFO] Executing Docker command: {{' '.join(docker_cmd)}}")

        # 執行 Docker 命令
        try:
            process = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 取得容器 PID
            container_info = subprocess.run(
                ['docker', 'inspect', '--format', '{{.State.Pid}}', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if container_info.returncode == 0:
                container_pid = int(container_info.stdout.strip())
                sim_job.{MODEL_VAR_PREFIX}_process_id = container_pid
                sim_job.save()

            # 設定超時 (例如 1 小時)
            timeout = 60 * 60
            start_time = time.time()

            while True:
                # 若超時
                if time.time() - start_time > timeout:
                    print(f"[ERROR] Simulation timeout for {MODEL_NAME} parent_uid: {{parent_uid}}")
                    terminate_{MODEL_VAR_PREFIX}(parent_uid)
                    return

                # 檢查容器狀態
                container_check = subprocess.run(
                    ['docker', 'ps', '-q', '-f', f'name={{container_name}}'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                container_exists = bool(container_check.stdout.strip())

                # 檢查結果文件是否已產生
                results_exist = os.path.exists(simulation_result_dir) and os.listdir(simulation_result_dir)

                if results_exist and not container_exists:
                    # 容器已結束，結果已生成 -> 視為成功
                    try:
                        # 若需要複製檔案到其他路徑，可在此進行
                        # 例如將檔案複製到絕對路徑 parent_obj.{MODEL_VAR_PREFIX_parent}_data_path

                        parent_obj.{MODEL_VAR_PREFIX_parent}_status = "completed"
                        parent_obj.save()

                        sim_job.{MODEL_VAR_PREFIX}_end_time = timezone.now()
                        sim_job.save()

                        print(f"[INFO] Simulation completed, results stored in: {{simulation_result_dir}}")
                        return

                    except Exception as e:
                        print(f"[ERROR] Error handling results: {{str(e)}}")
                        raise

        except subprocess.TimeoutExpired:
            print(f"[ERROR] Docker command timeout for {MODEL_NAME} parent_uid: {{parent_uid}}")
            terminate_{MODEL_VAR_PREFIX}(parent_uid)
        except Exception as e:
            print(f"[ERROR] Docker execution error: {{str(e)}}")
            raise

    except Exception as e:
        print(f"[ERROR] Simulation error: {{str(e)}}")
        if sim_job is not None:
            sim_job.delete()
        terminate_{MODEL_VAR_PREFIX}(parent_uid)


##########################
# 3) Manager (Actor) 類別 #
##########################
class {MODEL_NAME}Manager:

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_{MODEL_VAR_PREFIX}(request):
        """
        建立並啟動 {MODEL_NAME} 模擬
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                parent_uid = data.get('{DB_COLUMN_TO_FIELD}')

                if not parent_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 {DB_COLUMN_TO_FIELD} 參數'
                    }, status=400)

                try:
                    parent_obj = {PARENT_CLASS}.objects.get({DB_COLUMN_TO_FIELD}=parent_uid)
                except {PARENT_CLASS}.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 {PARENT_CLASS}'
                    }, status=404)

                # 若缺乏參數 (例如 parent_obj.{MODEL_VAR_PREFIX_parent}_parameter)，則報錯
                if not getattr(parent_obj, '{MODEL_VAR_PREFIX_parent}_parameter', None):
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少必要的模擬參數 ({MODEL_VAR_PREFIX_parent}_parameter)'
                    }, status=400)

                # 檢查是否已有尚未結束的 job
                current_sim_job = {MODEL_NAME}.objects.filter(
                    f_{MODEL_VAR_PREFIX_parent}=parent_obj,
                    {MODEL_VAR_PREFIX}_end_time__isnull=True
                ).first()
                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此模擬已在執行中',
                        'data': {
                            '{MODEL_VAR_PREFIX}_uid': str(current_sim_job.{MODEL_VAR_PREFIX}_uid),
                            '{DB_COLUMN_TO_FIELD}': str(parent_uid),
                            '{MODEL_VAR_PREFIX_parent}_status': getattr(parent_obj, '{MODEL_VAR_PREFIX_parent}_status', 'unknown')
                        }
                    })

                # (選用) 檢查同使用者是否有其他模擬在進行
                if hasattr(parent_obj, 'f_user_uid'):
                    other_sim_job = {MODEL_NAME}.objects.filter(
                        f_{MODEL_VAR_PREFIX_parent}__f_user_uid=parent_obj.f_user_uid,
                        {MODEL_VAR_PREFIX}_end_time__isnull=True
                    ).exclude(
                        f_{MODEL_VAR_PREFIX_parent}__{DB_COLUMN_TO_FIELD}=parent_uid
                    ).select_related('f_{MODEL_VAR_PREFIX_parent}').first()

                    if other_sim_job:
                        return JsonResponse({
                            'status': 'info',
                            'message': '使用者已有其他正在執行的模擬作業',
                            'data': {
                                '{MODEL_VAR_PREFIX}_uid': str(other_sim_job.{MODEL_VAR_PREFIX}_uid),
                                'current_{DB_COLUMN_TO_FIELD}': str(parent_uid),
                                '{MODEL_VAR_PREFIX_parent}_status': getattr(other_sim_job.f_{MODEL_VAR_PREFIX_parent}, '{MODEL_VAR_PREFIX_parent}_status', 'unknown')
                            }
                        })

                # 若主表為 completed 且結果檔案存在，可直接回傳
                # 假設主表有 {MODEL_VAR_PREFIX_parent}_status & {MODEL_VAR_PREFIX_parent}_data_path
                if getattr(parent_obj, '{MODEL_VAR_PREFIX_parent}_status', None) == 'completed':
                    data_path = getattr(parent_obj, '{MODEL_VAR_PREFIX_parent}_data_path', None)
                    if data_path and os.path.exists(data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已執行完成',
                            'data': {
                                '{DB_COLUMN_TO_FIELD}': str(parent_uid),
                                '{MODEL_VAR_PREFIX_parent}_status': parent_obj.{MODEL_VAR_PREFIX_parent}_status,
                                '{MODEL_VAR_PREFIX_parent}_data_path': data_path
                            }
                        })
                    else:
                        # 若檔案不在，改為失敗
                        parent_obj.{MODEL_VAR_PREFIX_parent}_status = 'simulation_failed'
                        parent_obj.save()

                # 啟動執行緒
                simulation_thread = threading.Thread(
                    target=run_{MODEL_VAR_PREFIX}_async,
                    args=(parent_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        '{DB_COLUMN_TO_FIELD}': str(parent_uid),
                        '{MODEL_VAR_PREFIX_parent}_status': 'processing'
                    }
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': '無效的 JSON 資料'
                }, status=400)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)


    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def delete_{MODEL_VAR_PREFIX}_result(request):
        """
        刪除 {MODEL_NAME} 的所有 Job & 結果檔案
        """
        try:
            data = json.loads(request.body)
            parent_uid = data.get('{DB_COLUMN_TO_FIELD}')

            if not parent_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': '缺少 {DB_COLUMN_TO_FIELD} 參數'
                }, status=400)

            try:
                parent_obj = {PARENT_CLASS}.objects.get({DB_COLUMN_TO_FIELD}=parent_uid)
            except {PARENT_CLASS}.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '找不到對應的 {PARENT_CLASS}'
                }, status=404)

            # 刪除所有 Job
            {MODEL_NAME}.objects.filter(
                f_{MODEL_VAR_PREFIX_parent}=parent_obj
            ).delete()

            # 刪除結果資料夾 (若主表有 {MODEL_VAR_PREFIX_parent}_data_path)
            data_path = getattr(parent_obj, '{MODEL_VAR_PREFIX_parent}_data_path', None)
            if data_path:
                full_path = os.path.join('./simulation_result', data_path)
                if os.path.exists(full_path):
                    shutil.rmtree(full_path)

            # 重置狀態
            parent_obj.{MODEL_VAR_PREFIX_parent}_status = "None"
            parent_obj.save()

            return JsonResponse({
                'status': 'success',
                'message': f'{MODEL_NAME} simulation result and related jobs deleted successfully'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def download_{MODEL_VAR_PREFIX}_result(request):
        """
        範例：下載 {MODEL_NAME} 產生的結果檔案
        """
        try:
            data = json.loads(request.body)
            parent_uid = data.get('{DB_COLUMN_TO_FIELD}')

            if not parent_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': '缺少 {DB_COLUMN_TO_FIELD} 參數'
                }, status=400)

            try:
                parent_obj = {PARENT_CLASS}.objects.get({DB_COLUMN_TO_FIELD}=parent_uid)
            except {PARENT_CLASS}.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '找不到對應的 {PARENT_CLASS}'
                }, status=404)

            # 假設要下載一個 PDF 檔案
            # pdf_path = os.path.join(
            #     parent_obj.{MODEL_VAR_PREFIX_parent}_data_path,
            #     '{MODEL_VAR_PREFIX}_simulation_report.pdf'
            # )
            # if not os.path.exists(pdf_path):
            #     return JsonResponse({
            #         'status': 'error',
            #         'message': 'PDF file not found'
            #     }, status=404)

            # with open(pdf_path, 'rb') as pdf_file:
            #     response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            #     response['Content-Disposition'] = f'attachment; filename="{MODEL_VAR_PREFIX}_simulation_report.pdf"'
            #     return response

            return JsonResponse({
                'status': 'info',
                'message': 'Download feature not yet implemented'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def test_post(request):
        """
        範例：測試使用 Docker 執行模擬，並將結果檔複製出來
        """
        try:
            data = json.loads(request.body)

            # 準備 Docker 命令參數
            json_params = json.dumps({
                "constellation": data.get("constellation"),
                "minLatitude": data.get("minLatitude"),
                "maxLatitude": data.get("maxLatitude"),
                "leastSatCount": data.get("leastSatCount")
            })

            # 建立目標資料夾
            host_output_dir = "/root/constellation_simulation/simulation_result/{MODEL_VAR_PREFIX}"
            os.makedirs(host_output_dir, exist_ok=True)

            # 準備 Docker run 指令
            container_name = f"{MODEL_VAR_PREFIX}_simulation_container"
            docker_cmd = f"""
            docker run \
                --oom-kill-disable=true \
                -m 28g \
                --rm \
                -v {{host_output_dir}}:/host_output \
                --name={{container_name}} \
                coverage_analysis_simulation:latest \
                bash -c '/root/mercury/shell/simulation_script.sh '"'"'{{json_params}}'"'"' && cp /root/mercury/build/service/*.csv /host_output/'
            """

            # 執行 Docker (設置較長的超時時間: 3600 秒 = 1 小時)
            try:
                result = subprocess.run(
                    docker_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=3600
                )

                print(f"[INFO] Command output: {{result.stdout}}")
                print(f"[INFO] Command errors: {{result.stderr}}")
                print(f"[INFO] Return code: {{result.returncode}}")

                if result.returncode != 0:
                    raise Exception(f"Docker 執行失敗: {{result.stderr}}")

            except subprocess.TimeoutExpired:
                raise Exception("Docker 命令執行超時（超過1小時）")
            except subprocess.CalledProcessError as e:
                raise Exception(f"Docker 命令執行失敗: {{str(e)}}")

            # 檢查輸出文件
            csv_files = glob.glob(os.path.join(host_output_dir, "*.csv"))
            if not csv_files:
                raise Exception("沒有找到輸出的 CSV 文件")

            response_data = {
                "status": "success",
                "message": "模擬完成並已複製結果檔案",
                "output_directory": host_output_dir,
                "files_generated": [os.path.basename(f) for f in csv_files]
            }
            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
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
