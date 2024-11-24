from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.HandoverModel import Handover
from main.apps.simulation_data_mgt.models.handoverSimJobModel import HandoverSimJob
from main.utils.logger import log_trigger, log_writer
from django.views.decorators.csrf import csrf_exempt
import os
import threading
from django.utils import timezone
import subprocess
import time
import shutil


def terminate_handover_sim_job(handover_uid):
    try:
        handover = Handover.objects.get(handover_uid=handover_uid)

        # 找到所有相關的未完成模擬作業
        sim_jobs = HandoverSimJob.objects.filter(
            f_handover_uid=handover,
            handoverSimJob_end_time__isnull=True
        )

        container_name = f"handoverSimulation_{handover_uid}"

        # 嘗試停止和移除 Docker 容器
        try:
            # 使用 docker stop 命令終止容器
            subprocess.run(
                ['docker', 'stop', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # 設置超時時間
            )

            # 確保容器被移除
            subprocess.run(
                ['docker', 'rm', '-f', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
        except subprocess.TimeoutExpired:
            # 如果 docker stop 超時，強制移除容器
            subprocess.run(
                ['docker', 'rm', '-f', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"Docker container stop error: {str(e)}")

        # 刪除所有相關的未完成模擬作業
        sim_jobs.delete()

        # 更新 handover 狀態
        handover.handover_status = "simulation fail"
        handover.save()

        print(f"All related simulation jobs terminated for handover_uid: {handover_uid}")
        return True

    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False

def run_handover_simulation_async(handover_uid):
    sim_job = None
    try:
        # 獲取 handover 實例
        handover = Handover.objects.get(handover_uid=handover_uid)

        # 建立新的 HandoverSimJob 記錄
        sim_job = HandoverSimJob.objects.create(
            f_handover_uid=handover,
            handoverSimJob_start_time=timezone.now()
        )

        # 更新狀態為執行中
        handover.handover_status = "processing"
        handover.save()

        # 定義輸出目錄，包含使用者UID和handover_uid
        simulation_result_dir = os.path.join(
            'simulation_result', 'handover_simulation',
            str(handover.f_user_uid.user_uid),
            str(handover_uid)
        )
        print(f"Simulation result directory: {simulation_result_dir}")

        # 確保輸出目錄存在
        os.makedirs(simulation_result_dir, exist_ok=True)

        # 構建 docker run 命令
        container_name = f"handoverSimulation_{handover_uid}"

        # 如果 handover_parameter 是字典，轉換為正確格式的字串
        if isinstance(handover.handover_parameter, dict):
            simulation_command = f"/root/mercury/shell/simulation_script.sh '{json.dumps(handover.handover_parameter)}'"
        else:
            try:
                param_dict = json.loads(handover.handover_parameter)
                simulation_command = f"/root/mercury/shell/simulation_script.sh '{json.dumps(param_dict)}'"
            except json.JSONDecodeError:
                simulation_command = handover.handover_parameter

        docker_command = [
            'docker', 'run',
            '-d',  # 在背景執行
            '--rm',  # 容器停止後自動移除
            f'--name={container_name}',
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'handoversimulationimage',
            'bash', '-c', simulation_command
        ]

        print(f"Docker command: {' '.join(docker_command)}")

        # 執行 docker 命令
        simulation_process = subprocess.Popen(
            docker_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 等待容器啟動並獲取容器 ID
        stdout, stderr = simulation_process.communicate()

        if simulation_process.returncode != 0:
            raise Exception(f"Unable to start Docker container: {stderr.decode()}")

        # 獲取容器的程序 ID
        container_info = subprocess.run(
            ['docker', 'inspect', '--format',
                '{{.State.Pid}}', container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if container_info.returncode == 0:
            container_pid = int(container_info.stdout.decode().strip())
            # 儲存容器的程序 ID
            sim_job.handoverSimJob_process_id = container_pid
            sim_job.save()
        else:
            raise Exception("Unable to get container process ID")

        # 設置超時時間（例如：60分鐘）
        timeout = 60 * 60  # 秒
        start_time = time.time()

        while True:
            # 檢查是否超時
            if time.time() - start_time > timeout:
                print(f"Simulation timeout for handover_uid: {handover_uid}")
                terminate_handover_sim_job(handover_uid)
                return

            # 檢查 Docker 容器是否存在
            container_check = subprocess.run(
                ['docker', 'ps', '-q', '-f', f'name={container_name}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            container_exists = bool(container_check.stdout.decode().strip())

            # 檢查結果檔案是否存在且有內容
            results_exist = os.path.exists(
                simulation_result_dir) and os.listdir(simulation_result_dir)

            if results_exist and not container_exists:
                # 如果有結果檔案且容器不存在，標記為完成
                sim_job.handoverSimJob_end_time = timezone.now()
                sim_job.save()
                handover.handover_status = "completed"
                # 更新 handover_data_path
                handover.handover_data_path = simulation_result_dir
                handover.save()
                print(f"Simulation completed successfully, results saved for handover_uid: {handover_uid}")
                return

            # 如果容器已經停止但沒有結果檔案，判定為失敗
            if not container_exists and not results_exist:
                raise Exception("Container stopped but no results found, simulation failed")

            # 等待一段時間再檢查
            time.sleep(10)

            # 重新從資料庫獲取 handover 狀態
            handover.refresh_from_db()
            if handover.handover_status == "simulation fail":
                return

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_handover_sim_job(handover_uid)

class handoverSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_handover_sim_job(request):
        if request.method == 'POST':
            try:
                # 解析 JSON 資料
                data = json.loads(request.body)

                # 獲取必要的參數
                handover_uid = data.get('handover_uid')

                # 驗證必要參數
                if not handover_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 handover_uid 參數'
                    }, status=400)

                # 檢查 handover 是否存在
                try:
                    handover = Handover.objects.get(handover_uid=handover_uid)
                except Handover.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 Handover'
                    }, status=404)

                # 檢查是否有 handover_parameter
                if not handover.handover_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Handover 缺少參數 handover_parameter'
                    }, status=400)

                # 檢查目前狀態是否為執行中
                if handover.handover_status == "processing":
                    return JsonResponse({
                        'status': 'info',
                        'message': '模擬正在執行中，請稍後查詢結果',
                        'data': {
                            'handover_uid': str(handover_uid),
                            'handover_status': handover.handover_status
                        }
                    })

                # 檢查是否有正在執行的模擬作業
                active_sim_job = HandoverSimJob.objects.filter(
                    f_handover_uid=handover,
                    handoverSimJob_end_time__isnull=True
                ).first()

                if active_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '已存在正在執行的模擬作業',
                        'data': {
                            'handoverSimJob_uid': str(active_sim_job.handoverSimJob_uid),
                            'handover_status': handover.handover_status
                        }
                    })

                # 檢查目前狀態和資料路徑
                if handover.handover_status == "completed":
                    if handover.handover_data_path and os.path.exists(handover.handover_data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已經執行完成，結果可供使用',
                            'data': {
                                'handover_uid': str(handover_uid),
                                'handover_status': handover.handover_status,
                                'handover_data_path': handover.handover_data_path
                            }
                        })
                    else:
                        # 如果狀態是 completed 但找不到資料，設置狀態為 simulation fail 並繼續
                        handover.handover_status = "simulation fail"
                        handover.save()

                # 在新的執行緒中執行模擬
                simulation_thread = threading.Thread(
                    target=run_handover_simulation_async,
                    args=(handover_uid,)
                )
                simulation_thread.start()

                # 立即返回回應
                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'handover_uid': str(handover_uid),
                        'handover_status': 'processing',
                        'handover_parameter': handover.handover_parameter,
                        'handover_data_path': handover.handover_data_path
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
    def delete_handover_sim_result(request):
        try:
            # 解析請求資料
            data = json.loads(request.body)
            handover_uid = data.get('handover_uid')

            if not handover_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'handover_uid is required'
                }, status=400)

            # 查找對應的 Handover 記錄
            try:
                handover = Handover.objects.get(handover_uid=handover_uid)
            except Handover.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Handover not found'
                }, status=404)

            # 檢查是否有 handover_data_path
            if not handover.handover_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No simulation result path found'
                }, status=404)

            # 刪除資料夾
            full_path = os.path.join('./', handover.handover_data_path)
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Simulation result directory not found: {handover.handover_data_path}'
                }, status=404)

            # 執行刪除
            shutil.rmtree(full_path)

            # 更新狀態
            handover.handover_status = "None"
            handover.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Handover simulation result deleted successfully'
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