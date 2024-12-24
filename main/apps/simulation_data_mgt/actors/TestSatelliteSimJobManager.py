import json
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

from main.apps.meta_data_mgt.models.TestSatelliteModel import TestSatellite
from main.apps.simulation_data_mgt.models.TestSatelliteSimJobModel import TestSatelliteSimJob

class TestSatelliteSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_test_satellite_sim_job(request):
        """
        建立並啟動 TestSatelliteSimJob (SimJob) 執行
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                parent_uid = data.get('test_satellite_uid')

                if not parent_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing test_satellite_uid parameter'
                    }, status=400)

                # 取得上游主表（ex: ConnectionTimeSimulation）
                try:
                    parent_obj = TestSatellite.objects.get(test_satellite_uid=parent_uid)
                except TestSatellite.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parent object not found'
                    }, status=404)

                # 檢查是否已有未結束的任務
                current_job = TestSatelliteSimJob.objects.filter(
                    f_test_satellite=parent_obj,
                    test_satellite_sim_job_end_time__isnull=True
                ).first()

                if current_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'There is already a running job for this parent object',
                        'data': {
                            'test_satellite_sim_job_uid': str(current_job.test_satellite_sim_job_uid)
                        }
                    })

                # 建立 Job
                new_job = TestSatelliteSimJob.objects.create(
                    f_test_satellite=parent_obj,
                    test_satellite_sim_job_start_time=timezone.now()
                )

                # 在此自行啟動執行緒 / Docker / 其他流程
                simulation_thread = threading.Thread(
                    target=async_test_satellite_sim_job_task,
                    args=(new_job.test_satellite_sim_job_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': f'TestSatelliteSimJob job is started',
                    'data': {
                        'test_satellite_sim_job_uid': str(new_job.test_satellite_sim_job_uid)
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
    def delete_test_satellite_sim_job_result(request):
        """
        刪除 TestSatelliteSimJob 相關結果
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                parent_uid = data.get('test_satellite_uid')

                if not parent_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing test_satellite_uid parameter'
                    }, status=400)

                try:
                    parent_obj = TestSatellite.objects.get(test_satellite_uid=parent_uid)
                except TestSatellite.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parent object not found'
                    }, status=404)

                # 刪除所有 Job
                TestSatelliteSimJob.objects.filter(f_test_satellite=parent_obj).delete()

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
    def download_test_satellite_sim_job_result(request):
        """
        範例：下載 TestSatelliteSimJob 的結果檔案
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                parent_uid = data.get('test_satellite_uid')

                if not parent_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing test_satellite_uid parameter'
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


def async_test_satellite_sim_job_task(job_uid):
    """
    這裡示範非同步執行模擬或其他處理邏輯。
    """
    try:
        job_obj = TestSatelliteSimJob.objects.get(test_satellite_sim_job_uid=job_uid)
        # 模擬執行邏輯 ...
        time.sleep(5)  # 假裝跑 5 秒

        # 更新 job 狀態
        job_obj.test_satellite_sim_job_end_time = timezone.now()
        job_obj.test_satellite_sim_job_result = {
            "message": "Simulation completed",
            "timestamp": str(timezone.now())
        }
        job_obj.save()
        print(f"[INFO] TestSatelliteSimJob job ({job_uid}) completed.")

    except Exception as e:
        print(f"[ERROR] TestSatelliteSimJob job execution failed: {{str(e)}}")
