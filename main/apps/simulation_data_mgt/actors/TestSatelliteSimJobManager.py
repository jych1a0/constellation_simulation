from django.views.decorators.csrf import csrf_exempt
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

from main.apps.meta_data_mgt.models.TestSatelliteModel import TestSatellite
from main.apps.simulation_data_mgt.models.TestSatelliteSimJobModel import TestSatelliteSimJob

############################################
# 1) 終止模擬：Docker Container + Job 處理 #
############################################
@log_trigger('INFO')
def terminate_test_satellite_sim_job(parent_uid):
    try:
        parent_obj = TestSatellite.objects.get(test_satellite_uid=parent_uid)

        # 找出尚未結束的 job
        sim_jobs = TestSatelliteSimJob.objects.filter(
            f_test_satellite=parent_obj,
            test_satellite_sim_job_end_time__isnull=True
        )

        container_name = f"test_satellite_sim_jobSimulation_{{parent_uid}}"

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
        parent_obj.test_satellite_status = "simulation_failed"
        parent_obj.save()

        print(f"[INFO] All related jobs terminated for TestSatelliteSimJob parent_uid: {{parent_uid}}")
        return True

    except Exception as e:
        print(f"[ERROR] TestSatelliteSimJob job termination error: {{str(e)}}")
        return False


############################################################
# 2) 非同步執行：執行 Docker、檔案複製、狀態更新等完整流程 #
############################################################
@log_trigger('INFO')
def run_test_satellite_sim_job_async(parent_uid):
    sim_job = None
    try:
        parent_obj = TestSatellite.objects.get(test_satellite_uid=parent_uid)

        # 建立 Job 紀錄
        sim_job = TestSatelliteSimJob.objects.create(
            f_test_satellite=parent_obj,
            test_satellite_sim_job_start_time=timezone.now()
        )

        # 更新主表狀態
        parent_obj.test_satellite_status = "processing"
        parent_obj.save()

        # 建立結果目錄 (可依需求命名)
        simulation_result_dir = os.path.join(
            'simulation_result',
            'test_satellite_sim_job_simulation',
            str(parent_obj.f_user_uid.user_uid) if hasattr(parent_obj, 'f_user_uid') else 'unknown_user',
            str(parent_uid)
        )
        os.makedirs(simulation_result_dir, exist_ok=True)
        print(f"[INFO] Simulation result directory: {simulation_result_dir}")

        # 準備 Docker Container 名稱
        container_name = f"test_satellite_sim_jobSimulation_{parent_uid}"

        # 準備模擬參數 (JSON)
        # 假設主表欄位為 parent_obj.test_satellite_parameter
        if isinstance(parent_obj.test_satellite_parameter, dict):
            json_params = json.dumps(parent_obj.test_satellite_parameter)
        else:
            try:
                json_params = json.dumps(json.loads(parent_obj.test_satellite_parameter))
            except json.JSONDecodeError:
                json_params = parent_obj.test_satellite_parameter

        # Docker 命令示範：可自行修改 image, script, volume 等
        docker_cmd = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '28g',
            '--rm',
            '--name', container_name,
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'coverage_analysis_simulation:latest',
            'bash', '-c',
            f'/root/mercury/shell/simulation_script.sh \'{json_params}\' && '
            f'cp -r /root/mercury/build/service/*.csv /root/mercury/build/service/output/'
        ]

        print(f"[INFO] Executing Docker command: {' '.join(docker_cmd)}")

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
                sim_job.test_satellite_sim_job_process_id = container_pid
                sim_job.save()

            # 設定超時 (例如 1 小時)
            timeout = 60 * 60
            start_time = time.time()

            while True:
                # 若超時
                if time.time() - start_time > timeout:
                    print(f"[ERROR] Simulation timeout for TestSatelliteSimJob parent_uid: {{parent_uid}}")
                    terminate_test_satellite_sim_job(parent_uid)
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
                        # 例如將檔案複製到絕對路徑 parent_obj.test_satellite_data_path

                        parent_obj.test_satellite_status = "completed"
                        parent_obj.save()

                        sim_job.test_satellite_sim_job_end_time = timezone.now()
                        sim_job.save()

                        print(f"[INFO] Simulation completed, results stored in: {{simulation_result_dir}}")
                        return

                    except Exception as e:
                        print(f"[ERROR] Error handling results: {{str(e)}}")
                        raise

        except subprocess.TimeoutExpired:
            print(f"[ERROR] Docker command timeout for TestSatelliteSimJob parent_uid: {{parent_uid}}")
            terminate_test_satellite_sim_job(parent_uid)
        except Exception as e:
            print(f"[ERROR] Docker execution error: {{str(e)}}")
            raise

    except Exception as e:
        print(f"[ERROR] Simulation error: {{str(e)}}")
        if sim_job is not None:
            sim_job.delete()
        terminate_test_satellite_sim_job(parent_uid)


##########################
# 3) Manager (Actor) 類別 #
##########################
class TestSatelliteSimJobManager:

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_test_satellite_sim_job(request):
        """
        建立並啟動 TestSatelliteSimJob 模擬
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                parent_uid = data.get('test_satellite_uid')

                if not parent_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 test_satellite_uid 參數'
                    }, status=400)

                try:
                    parent_obj = TestSatellite.objects.get(test_satellite_uid=parent_uid)
                except TestSatellite.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 TestSatellite'
                    }, status=404)

                # 若缺乏參數 (例如 parent_obj.test_satellite_parameter)，則報錯
                if not getattr(parent_obj, 'test_satellite_parameter', None):
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少必要的模擬參數 (test_satellite_parameter)'
                    }, status=400)

                # 檢查是否已有尚未結束的 job
                current_sim_job = TestSatelliteSimJob.objects.filter(
                    f_test_satellite=parent_obj,
                    test_satellite_sim_job_end_time__isnull=True
                ).first()
                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此模擬已在執行中',
                        'data': {
                            'test_satellite_sim_job_uid': str(current_sim_job.test_satellite_sim_job_uid),
                            'test_satellite_uid': str(parent_uid),
                            'test_satellite_status': getattr(parent_obj, 'test_satellite_status', 'unknown')
                        }
                    })

                # (選用) 檢查同使用者是否有其他模擬在進行
                if hasattr(parent_obj, 'f_user_uid'):
                    other_sim_job = TestSatelliteSimJob.objects.filter(
                        f_test_satellite__f_user_uid=parent_obj.f_user_uid,
                        test_satellite_sim_job_end_time__isnull=True
                    ).exclude(
                        f_test_satellite__test_satellite_uid=parent_uid
                    ).select_related('f_test_satellite').first()

                    if other_sim_job:
                        return JsonResponse({
                            'status': 'info',
                            'message': '使用者已有其他正在執行的模擬作業',
                            'data': {
                                'test_satellite_sim_job_uid': str(other_sim_job.test_satellite_sim_job_uid),
                                'current_test_satellite_uid': str(parent_uid),
                                'test_satellite_status': getattr(other_sim_job.f_test_satellite, 'test_satellite_status', 'unknown')
                            }
                        })

                # 若主表為 completed 且結果檔案存在，可直接回傳
                # 假設主表有 test_satellite_status & test_satellite_data_path
                if getattr(parent_obj, 'test_satellite_status', None) == 'completed':
                    data_path = getattr(parent_obj, 'test_satellite_data_path', None)
                    if data_path and os.path.exists(data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已執行完成',
                            'data': {
                                'test_satellite_uid': str(parent_uid),
                                'test_satellite_status': parent_obj.test_satellite_status,
                                'test_satellite_data_path': data_path
                            }
                        })
                    else:
                        # 若檔案不在，改為失敗
                        parent_obj.test_satellite_status = 'simulation_failed'
                        parent_obj.save()

                # 啟動執行緒
                simulation_thread = threading.Thread(
                    target=run_test_satellite_sim_job_async,
                    args=(parent_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'test_satellite_uid': str(parent_uid),
                        'test_satellite_status': 'processing'
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
    def delete_test_satellite_sim_job_result(request):
        """
        刪除 TestSatelliteSimJob 的所有 Job & 結果檔案
        """
        try:
            data = json.loads(request.body)
            parent_uid = data.get('test_satellite_uid')

            if not parent_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': '缺少 test_satellite_uid 參數'
                }, status=400)

            try:
                parent_obj = TestSatellite.objects.get(test_satellite_uid=parent_uid)
            except TestSatellite.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '找不到對應的 TestSatellite'
                }, status=404)

            # 刪除所有 Job
            TestSatelliteSimJob.objects.filter(
                f_test_satellite=parent_obj
            ).delete()

            # 刪除結果資料夾 (若主表有 test_satellite_data_path)
            data_path = getattr(parent_obj, 'test_satellite_data_path', None)
            if data_path:
                full_path = os.path.join('./simulation_result', data_path)
                if os.path.exists(full_path):
                    shutil.rmtree(full_path)

            # 重置狀態
            parent_obj.test_satellite_status = "None"
            parent_obj.save()

            return JsonResponse({
                'status': 'success',
                'message': f'TestSatelliteSimJob simulation result and related jobs deleted successfully'
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
    def download_test_satellite_sim_job_result(request):
        """
        範例：下載 TestSatelliteSimJob 產生的結果檔案
        """
        try:
            data = json.loads(request.body)
            parent_uid = data.get('test_satellite_uid')

            if not parent_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': '缺少 test_satellite_uid 參數'
                }, status=400)

            try:
                parent_obj = TestSatellite.objects.get(test_satellite_uid=parent_uid)
            except TestSatellite.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '找不到對應的 TestSatellite'
                }, status=404)

            # 假設要下載一個 PDF 檔案
            # pdf_path = os.path.join(
            #     parent_obj.test_satellite_data_path,
            #     'test_satellite_sim_job_simulation_report.pdf'
            # )
            # if not os.path.exists(pdf_path):
            #     return JsonResponse({
            #         'status': 'error',
            #         'message': 'PDF file not found'
            #     }, status=404)

            # with open(pdf_path, 'rb') as pdf_file:
            #     response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            #     response['Content-Disposition'] = f'attachment; filename="test_satellite_sim_job_simulation_report.pdf"'
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
            host_output_dir = "/root/constellation_simulation/simulation_result/test_satellite_sim_job"
            os.makedirs(host_output_dir, exist_ok=True)

            # 準備 Docker run 指令
            container_name = f"test_satellite_sim_job_simulation_container"
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
