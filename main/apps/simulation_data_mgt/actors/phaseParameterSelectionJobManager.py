# main/apps/simulation_data_mgt/actors/phaseParameterSelectionJobManager.py
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json, os, shutil, subprocess, glob
import threading, time
from pathlib import Path
from django.utils import timezone

from main.utils.logger import log_trigger, log_writer
from main.apps.meta_data_mgt.models.PhaseParameterSelectionModel import PhaseParameterSelection
from main.apps.simulation_data_mgt.models.PhaseParameterSelectionJobModel import PhaseParameterSelectionJob


@log_trigger('INFO')
def terminate_phase_parameter_selection_job(phase_parameter_selection_uid):
    """
    停止並刪除尚未結束的模擬 Job（例如 docker container）
    """
    try:
        selection_obj = PhaseParameterSelection.objects.get(
            phase_parameter_selection_uid=phase_parameter_selection_uid
        )

        sim_jobs = PhaseParameterSelectionJob.objects.filter(
            f_phase_parameter_selection_uid=selection_obj,
            phaseParameterSelectionJob_end_time__isnull=True
        )

        container_name = f"phaseParameterSelection_{phase_parameter_selection_uid}"

        # 嘗試停止並刪除 Docker Container
        try:
            subprocess.run(['docker', 'stop', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            subprocess.run(['docker', 'rm', '-f', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', container_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"Docker container stop error: {str(e)}")

        # 刪除資料庫中的 job 紀錄
        sim_jobs.delete()
        
        # 更新主表狀態
        selection_obj.phase_parameter_selection_status = "simulation_failed"
        selection_obj.save()

        print(f"Terminated all sim jobs for phase_parameter_selection_uid: {phase_parameter_selection_uid}")
        return True
    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False


@log_trigger('INFO')
def run_phase_parameter_selection_async(phase_parameter_selection_uid):
    """
    非同步執行模擬作業
    """
    sim_job = None
    try:
        selection_obj = PhaseParameterSelection.objects.get(
            phase_parameter_selection_uid=phase_parameter_selection_uid
        )
        # 建立 job 紀錄
        sim_job = PhaseParameterSelectionJob.objects.create(
            f_phase_parameter_selection_uid=selection_obj,
            phaseParameterSelectionJob_start_time=timezone.now()
        )
        # 更新主表狀態
        selection_obj.phase_parameter_selection_status = "processing"
        selection_obj.save()

        # 建立輸出資料夾
        simulation_result_dir = os.path.join(
            'simulation_result', 'phase_parameter_selection',
            str(selection_obj.f_user_uid.user_uid),
            str(phase_parameter_selection_uid)
        )
        os.makedirs(simulation_result_dir, exist_ok=True)
        print(f"Simulation result directory: {simulation_result_dir}")

        # 準備 Docker 參數
        container_name = f"phaseParameterSelection_{phase_parameter_selection_uid}"

        # 轉換參數成 JSON 字串
        if isinstance(selection_obj.phase_parameter_selection_parameter, dict):
            json_params = json.dumps(selection_obj.phase_parameter_selection_parameter)
        else:
            try:
                json_params = json.dumps(json.loads(selection_obj.phase_parameter_selection_parameter))
            except json.JSONDecodeError:
                json_params = selection_obj.phase_parameter_selection_parameter

        # 假設有一個對應的 Docker Image 來執行該模擬
        docker_cmd = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '28g',
            '--rm',
            '--name', container_name,
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'coverage_analysis_simulation:latest',  # Demo image，可自行修改
            'bash', '-c',
            f'/root/mercury/shell/simulation_script.sh \'{json_params}\' && '
            f'cp -r /root/mercury/build/service/*.csv /root/mercury/build/service/output/'
        ]
        print(f"Executing Docker command: {' '.join(docker_cmd)}")

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
                sim_job.phaseParameterSelectionJob_process_id = container_pid
                sim_job.save()

            # 設定超時 (1 小時)
            timeout = 60 * 60
            start_time = time.time()

            while True:
                if time.time() - start_time > timeout:
                    print(f"Simulation timeout: {phase_parameter_selection_uid}")
                    terminate_phase_parameter_selection_job(phase_parameter_selection_uid)
                    return

                # 檢查容器是否仍在運行
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
                    # 容器不在執行，且已產生結果文件
                    selection_obj.phase_parameter_selection_status = "completed"
                    selection_obj.save()

                    sim_job.phaseParameterSelectionJob_end_time = timezone.now()
                    sim_job.save()
                    print(f"Simulation completed: {phase_parameter_selection_uid}")
                    return

        except subprocess.TimeoutExpired:
            print(f"Docker command timeout: {phase_parameter_selection_uid}")
            terminate_phase_parameter_selection_job(phase_parameter_selection_uid)
        except Exception as e:
            print(f"Docker execution error: {str(e)}")
            raise

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_phase_parameter_selection_job(phase_parameter_selection_uid)


class phaseParameterSelectionJobManager:
    """
    與 CoverageAnalysisSimJobManager 類似的 Actor，
    用來啟動、刪除、或下載模擬結果等功能。
    """

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_phase_parameter_selection_job(request):
        """
        啟動模擬
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                phase_parameter_selection_uid = data.get('phase_parameter_selection_uid')

                if not phase_parameter_selection_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 phase_parameter_selection_uid 參數'
                    }, status=400)

                # 取主表
                try:
                    selection_obj = PhaseParameterSelection.objects.get(
                        phase_parameter_selection_uid=phase_parameter_selection_uid
                    )
                except PhaseParameterSelection.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 PhaseParameterSelection'
                    }, status=404)

                # 若缺乏模擬參數
                if not selection_obj.phase_parameter_selection_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'PhaseParameterSelection 缺少參數 phase_parameter_selection_parameter'
                    }, status=400)

                # ---- [業務邏輯補足 1] 檢查是否已有尚未結束的 job ----
                current_sim_job = PhaseParameterSelectionJob.objects.filter(
                    f_phase_parameter_selection_uid=selection_obj,
                    phaseParameterSelectionJob_end_time__isnull=True
                ).first()
                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此 PhaseParameterSelection 正在執行模擬',
                        'data': {
                            'phaseParameterSelectionJob_uid': str(current_sim_job.phaseParameterSelectionJob_uid),
                            'phase_parameter_selection_uid': str(phase_parameter_selection_uid),
                            'phase_parameter_selection_status': selection_obj.phase_parameter_selection_status
                        }
                    })

                # ---- [業務邏輯補足 2] 檢查同使用者是否已有其他模擬任務在執行（若不需要可移除） ----
                other_sim_job = PhaseParameterSelectionJob.objects.filter(
                    f_phase_parameter_selection_uid__f_user_uid=selection_obj.f_user_uid,
                    phaseParameterSelectionJob_end_time__isnull=True
                ).exclude(
                    f_phase_parameter_selection_uid__phase_parameter_selection_uid=phase_parameter_selection_uid
                ).select_related('f_phase_parameter_selection_uid').first()

                if other_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '使用者已有其他正在執行的模擬作業',
                        'data': {
                            'phaseParameterSelectionJob_uid': str(other_sim_job.phaseParameterSelectionJob_uid),
                            'phase_parameter_selection_uid': str(
                                other_sim_job.f_phase_parameter_selection_uid.phase_parameter_selection_uid
                            ),
                            'current_phase_parameter_selection_uid': str(phase_parameter_selection_uid),
                            'phase_parameter_selection_status':
                                other_sim_job.f_phase_parameter_selection_uid.phase_parameter_selection_status
                        }
                    })

                # ---- [業務邏輯補足 3] 若主表狀態為 completed，且結果檔案存在，就直接回傳 ----
                if selection_obj.phase_parameter_selection_status == "completed":
                    data_path = selection_obj.phase_parameter_selection_data_path
                    if data_path and os.path.exists(data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已經執行完成，結果可供使用',
                            'data': {
                                'phase_parameter_selection_uid': str(phase_parameter_selection_uid),
                                'phase_parameter_selection_status': selection_obj.phase_parameter_selection_status,
                                'phase_parameter_selection_data_path': data_path
                            }
                        })
                    else:
                        # 若檔案不在，改為 simulation_failed
                        selection_obj.phase_parameter_selection_status = "simulation_failed"
                        selection_obj.save()

                # 以執行緒方式啟動模擬
                simulation_thread = threading.Thread(
                    target=run_phase_parameter_selection_async,
                    args=(phase_parameter_selection_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'phase_parameter_selection_uid': str(phase_parameter_selection_uid),
                        'phase_parameter_selection_status': 'processing',
                        'phase_parameter_selection_parameter': selection_obj.phase_parameter_selection_parameter,
                        'phase_parameter_selection_data_path': selection_obj.phase_parameter_selection_data_path
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
    def delete_phase_parameter_selection_result(request):
        """
        刪除 PhaseParameterSelection 模擬結果
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                phase_parameter_selection_uid = data.get('phase_parameter_selection_uid')

                if not phase_parameter_selection_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'phase_parameter_selection_uid is required'
                    }, status=400)

                try:
                    selection_obj = PhaseParameterSelection.objects.get(
                        phase_parameter_selection_uid=phase_parameter_selection_uid
                    )
                except PhaseParameterSelection.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'PhaseParameterSelection not found'
                    }, status=404)

                # 刪除所有 Job
                PhaseParameterSelectionJob.objects.filter(
                    f_phase_parameter_selection_uid=selection_obj
                ).delete()

                # 刪除結果資料夾
                if not selection_obj.phase_parameter_selection_data_path:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No simulation result path found'
                    }, status=404)

                full_path = os.path.join('./simulation_result', selection_obj.phase_parameter_selection_data_path)
                if not os.path.exists(full_path):
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Simulation result directory not found: {selection_obj.phase_parameter_selection_data_path}'
                    }, status=404)

                shutil.rmtree(full_path)

                # 重置主表狀態
                selection_obj.phase_parameter_selection_status = "None"
                selection_obj.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'PhaseParameterSelection simulation result and related jobs deleted successfully'
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
    def download_phase_parameter_selection_result(request):
        """
        範例：下載 PDF 或其他檔案
        """
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                phase_parameter_selection_uid = data.get('phase_parameter_selection_uid')

                if not phase_parameter_selection_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'phase_parameter_selection_uid is required'
                    }, status=400)

                try:
                    selection_obj = PhaseParameterSelection.objects.get(
                        phase_parameter_selection_uid=phase_parameter_selection_uid
                    )
                except PhaseParameterSelection.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'PhaseParameterSelection not found'
                    }, status=404)

                if not selection_obj.phase_parameter_selection_data_path:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'PhaseParameterSelection data path not found'
                    }, status=404)

                # 假設要下載一個 PDF 結果檔案
                pdf_path = os.path.join(
                    selection_obj.phase_parameter_selection_data_path,
                    'phase_parameter_selection_simulation_report.pdf'
                )
                print(f"Attempting to download PDF from path: {pdf_path}")

                if not os.path.exists(pdf_path):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'PDF file not found'
                    }, status=404)

                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="phase_parameter_selection_simulation_report.pdf"'
                    return response

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

        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)
