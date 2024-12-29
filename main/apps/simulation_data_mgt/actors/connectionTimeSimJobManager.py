import os
import json
import uuid
import shutil
import subprocess
import threading
import time
from pathlib import Path

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse

from django.utils import timezone
from main.utils.logger import log_trigger, log_writer

from main.apps.meta_data_mgt.models.ConnectionTimeSimulationModel import ConnectionTimeSimulation
from main.apps.simulation_data_mgt.models.ConnectionTimeSimJobModel import ConnectionTimeSimJob


@log_trigger('INFO')
def terminate_connection_time_sim_job(connection_time_simulation_uid):
    """
    示範：停止容器 or 結束模擬邏輯
    """
    try:
        sim_obj = ConnectionTimeSimulation.objects.get(connection_time_simulation_uid=connection_time_simulation_uid)

        # 找出尚未結束的 job
        sim_jobs = ConnectionTimeSimJob.objects.filter(
            f_connection_time_simulation_uid=sim_obj,
            connectionTimeSimJob_end_time__isnull=True
        )

        container_name = f"connectionTimeSimulation_{connection_time_simulation_uid}"

        # 嘗試停止並移除 Docker container
        try:
            subprocess.run(['docker', 'stop', container_name],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           timeout=30)
            subprocess.run(['docker', 'rm', '-f', container_name],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', container_name],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        except Exception as e:
            print(f"Docker container stop error: {str(e)}")

        # 將尚未結束的 job 刪除或標註結束
        sim_jobs.delete()

        # 更新狀態
        sim_obj.connection_time_simulation_status = "simulation_failed"
        sim_obj.save()

        print(f"All related simulation jobs terminated for connection_time_simulation_uid: {connection_time_simulation_uid}")
        return True

    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False


@log_trigger('INFO')
def run_connection_time_simulation_async(connection_time_simulation_uid):
    """
    非同步執行 ConnectionTimeSimulation job 的示範函式
    """
    sim_job = None
    try:
        # 1. 取得對應的 Connection_Time_Simulation
        sim_obj = ConnectionTimeSimulation.objects.get(connection_time_simulation_uid=connection_time_simulation_uid)

        # 2. 建立 job 紀錄
        sim_job = ConnectionTimeSimJob.objects.create(
            f_connection_time_simulation_uid=sim_obj,
            connectionTimeSimJob_start_time=timezone.now(),
            connectionTimeSimJob_result={}  # 建立時先給個空 dict
        )

        # 更新 Simulation 狀態
        sim_obj.connection_time_simulation_status = "processing"
        sim_obj.save()

        # 3. 準備結果目錄
        simulation_result_dir = os.path.join(
            'simulation_result',
            'connection_time_simulation',
            str(sim_obj.f_user_uid.user_uid),
            str(connection_time_simulation_uid)
        )
        os.makedirs(simulation_result_dir, exist_ok=True)
        print(f"Simulation result directory: {simulation_result_dir}")

        # 4. 建立 Docker 命令
        container_name = f"connectionTimeSimulation_{connection_time_simulation_uid}"

        # 參數 (JSON 格式)
        if isinstance(sim_obj.connection_time_simulation_parameter, dict):
            json_params = json.dumps(sim_obj.connection_time_simulation_parameter)
        else:
            try:
                json_params = json.dumps(json.loads(sim_obj.connection_time_simulation_parameter))
            except json.JSONDecodeError:
                json_params = sim_obj.connection_time_simulation_parameter

        # Docker 命令示範（可自行修改 image 名稱或 script）
        docker_cmd = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '28g',
            '--rm',
            '--name', container_name,
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'coverage_analysis_simulation:latest',  # 此處只是示範，可替換為實際 image
            'bash', '-c',
            f'/root/mercury/shell/simulation_script.sh \'{json_params}\' && '
            f'cp -r /root/mercury/build/service/*.csv /root/mercury/build/service/output/'
        ]

        print(f"Executing Docker command: {' '.join(docker_cmd)}")

        # 5. 執行 Docker
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
                sim_job.connectionTimeSimJob_process_id = container_pid
                sim_job.save()

            # 設定超時時間 (例如 1 小時)
            timeout = 60 * 60
            start_time = time.time()

            while True:
                # 超時檢查
                if time.time() - start_time > timeout:
                    print(f"Simulation timeout for connection_time_simulation_uid: {connection_time_simulation_uid}")
                    terminate_connection_time_sim_job(connection_time_simulation_uid)
                    return

                # 檢查容器狀態
                container_check = subprocess.run(
                    ['docker', 'ps', '-q', '-f', f'name={container_name}'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                container_exists = bool(container_check.stdout.strip())

                # 檢查結果文件
                results_exist = os.path.exists(simulation_result_dir) and os.listdir(simulation_result_dir)

                if results_exist and not container_exists:
                    try:
                        # 如果檔案已產生且容器結束，判定為成功
                        sim_obj.connection_time_simulation_status = "completed"
                        sim_obj.save()

                        sim_job.connectionTimeSimJob_end_time = timezone.now()
                        # 如果需要，可在此處更新 sim_job_result (例如解析 .csv)
                        sim_job.connectionTimeSimJob_result = {
                            "message": "Simulation completed successfully.",
                            "files": os.listdir(simulation_result_dir)
                        }
                        sim_job.save()

                        print(f"Simulation completed and results stored in: {simulation_result_dir}")
                        return

                    except Exception as e:
                        print(f"Error handling results: {str(e)}")
                        raise

        except subprocess.TimeoutExpired:
            print(f"Docker command timeout for connection_time_simulation_uid: {connection_time_simulation_uid}")
            terminate_connection_time_sim_job(connection_time_simulation_uid)
        except Exception as e:
            print(f"Docker execution error: {str(e)}")
            raise

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_connection_time_sim_job(connection_time_simulation_uid)


class connectionTimeSimJobManager:

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_connection_time_sim_job(request):
        """
        啟動 ConnectionTimeSimJob 模擬的範例
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                connection_time_simulation_uid = data.get('connection_time_simulation_uid')

                if not connection_time_simulation_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 connection_time_simulation_uid 參數'
                    }, status=400)

                try:
                    sim_obj = ConnectionTimeSimulation.objects.get(
                        connection_time_simulation_uid=connection_time_simulation_uid
                    )
                except ConnectionTimeSimulation.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 Connection_Time_Simulation'
                    }, status=404)

                if not sim_obj.connection_time_simulation_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 connection_time_simulation_parameter'
                    }, status=400)

                # 1. 檢查是否已有同一模擬任務正在執行
                current_sim_job = ConnectionTimeSimJob.objects.filter(
                    f_connection_time_simulation_uid=sim_obj,
                    connectionTimeSimJob_end_time__isnull=True
                ).first()

                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此 Connection_Time_Simulation 正在執行模擬作業',
                        'data': {
                            'connectionTimeSimJob_uid': str(current_sim_job.connectionTimeSimJob_uid),
                            'connection_time_simulation_uid': str(connection_time_simulation_uid),
                            'connection_time_simulation_status': sim_obj.connection_time_simulation_status
                        }
                    })

                # 2. 檢查同使用者是否有其他模擬任務正在執行 (若不需要可移除)
                other_sim_job = ConnectionTimeSimJob.objects.filter(
                    f_connection_time_simulation_uid__f_user_uid=sim_obj.f_user_uid,
                    connectionTimeSimJob_end_time__isnull=True
                ).exclude(
                    f_connection_time_simulation_uid__connection_time_simulation_uid=connection_time_simulation_uid
                ).select_related('f_connection_time_simulation_uid').first()

                if other_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '使用者已有其他正在執行的模擬作業',
                        'data': {
                            'connectionTimeSimJob_uid': str(other_sim_job.connectionTimeSimJob_uid),
                            'connection_time_simulation_uid': str(
                                other_sim_job.f_connection_time_simulation_uid.connection_time_simulation_uid
                            ),
                            'current_connection_time_simulation_uid': str(connection_time_simulation_uid),
                            'connection_time_simulation_status':
                                other_sim_job.f_connection_time_simulation_uid.connection_time_simulation_status
                        }
                    })

                # 3. 如果已完成但有舊的結果檔，可直接回傳；若結果檔不存在則標為 simulation_failed
                if sim_obj.connection_time_simulation_status == "completed":
                    if sim_obj.connection_time_simulation_data_path:
                        full_path = os.path.join(
                            'simulation_result',
                            'connection_time_simulation',
                            str(sim_obj.f_user_uid.user_uid),
                            str(connection_time_simulation_uid)
                        )
                        if os.path.exists(full_path):
                            return JsonResponse({
                                'status': 'success',
                                'message': '模擬已經執行完成，結果可供使用',
                                'data': {
                                    'connection_time_simulation_uid': str(connection_time_simulation_uid),
                                    'connection_time_simulation_status': sim_obj.connection_time_simulation_status,
                                    'connection_time_simulation_data_path': sim_obj.connection_time_simulation_data_path
                                }
                            })
                        else:
                            # 若 DB 狀態為 completed 但檔案實際不存在，則視需求將狀態改為失敗
                            sim_obj.connection_time_simulation_status = "simulation_failed"
                            sim_obj.save()

                # 4. 啟動執行緒進行模擬
                simulation_thread = threading.Thread(
                    target=run_connection_time_simulation_async,
                    args=(connection_time_simulation_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'connection_time_simulation_uid': str(connection_time_simulation_uid),
                        'connection_time_simulation_status': 'processing'
                    }
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': '無效的 JSON 格式'
                }, status=400)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def delete_connection_time_sim_result(request):
        """
        刪除 Connection_Time_Simulation 的模擬結果與相關 Job 資訊
        """
        try:
            data = json.loads(request.body)
            connection_time_simulation_uid = data.get('connection_time_simulation_uid')

            if not connection_time_simulation_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': '缺少 connection_time_simulation_uid 參數'
                }, status=400)

            try:
                sim_obj = ConnectionTimeSimulation.objects.get(connection_time_simulation_uid=connection_time_simulation_uid)
            except ConnectionTimeSimulation.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': '找不到對應的 Connection_Time_Simulation'
                }, status=404)

            # 刪除所有相關的 Job
            ConnectionTimeSimJob.objects.filter(
                f_connection_time_simulation_uid=sim_obj
            ).delete()

            # 檢查模擬結果路徑
            if not sim_obj.connection_time_simulation_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No simulation result path found'
                }, status=404)

            full_path = os.path.join('./simulation_result', sim_obj.connection_time_simulation_data_path)
            print(full_path)
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Simulation result directory not found: {sim_obj.connection_time_simulation_data_path}'
                }, status=404)

            shutil.rmtree(full_path)

            sim_obj.connection_time_simulation_status = "None"
            sim_obj.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Connection Time Simulation result and related jobs deleted successfully'
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
    def download_connection_time_sim_result(request):
        """
        範例：下載/回傳 ConnectionTimeSimJob 產生的結果檔案
        """
        try:
            data = json.loads(request.body)
            connection_time_simulation_uid = data.get('connection_time_simulation_uid')

            if not connection_time_simulation_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'connection_time_simulation_uid is required'
                }, status=400)

            # 假設需要傳回 PDF 或 CSV 檔：此處舉例為 PDF
            pdf_path = os.path.join(
                'simulation_result',
                'connection_time_simulation',
                str(connection_time_simulation_uid),
                'connection_time_simulation_report.pdf'
            )
            print(f"Attempting to download PDF from path: {pdf_path}")

            if not os.path.exists(pdf_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'PDF file not found'
                }, status=404)

            try:
                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="connection_time_simulation_report.pdf"'
                    return response
            except IOError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Error reading PDF file'
                }, status=500)

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
