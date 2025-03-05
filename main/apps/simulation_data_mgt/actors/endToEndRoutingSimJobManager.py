from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json
from main.apps.meta_data_mgt.models.EndToEndRoutingModel import EndToEndRouting
from main.apps.simulation_data_mgt.models.EndToEndRoutingSimJobModel import EndToEndRoutingSimJob
from main.apps.simulation_data_mgt.services.analyzeEndToEndRoutingResult import analyzeEndToEndRoutingResult
from main.apps.simulation_data_mgt.services.genEndToEndRoutingResultPDF import genEndToEndRoutingResultPDF
from main.utils.logger import log_trigger, log_writer
import os
import threading
from django.utils import timezone
import subprocess
import time
import shutil


@log_trigger('INFO')
def terminate_endToEndRouting_sim_job(endToEndRouting_uid):
    try:
        obj = EndToEndRouting.objects.get(endToEndRouting_uid=endToEndRouting_uid)
        sim_jobs = EndToEndRoutingSimJob.objects.filter(
            f_endToEndRouting_uid=obj,
            endToEndRoutingSimJob_end_time__isnull=True
        )

        container_name = f"endToEndRoutingSimulation_{endToEndRouting_uid}"

        try:
            subprocess.run(['docker', 'stop', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', container_name])
        except Exception as e:
            print(f"Docker container stop error: {str(e)}")

        sim_jobs.delete()

        obj.endToEndRouting_status = "simulation_failed"
        obj.save()

        print(f"All related simulation jobs terminated for endToEndRouting_uid: {endToEndRouting_uid}")
        return True

    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False


@log_trigger('INFO')
def run_endToEndRouting_simulation_async(endToEndRouting_uid):
    sim_job = None
    try:
        obj = EndToEndRouting.objects.get(endToEndRouting_uid=endToEndRouting_uid)
        sim_job = EndToEndRoutingSimJob.objects.create(
            f_endToEndRouting_uid=obj,
            endToEndRoutingSimJob_start_time=timezone.now()
        )

        obj.endToEndRouting_status = "processing"
        obj.save()

        simulation_result_dir = os.path.join(
            'simulation_result', 'endToEndRouting_simulation',
            str(obj.f_user_uid.user_uid),
            str(endToEndRouting_uid)
        )
        print(f"Simulation result directory: {simulation_result_dir}")
        os.makedirs(simulation_result_dir, exist_ok=True)

        container_name = f"endToEndRoutingSimulation_{endToEndRouting_uid}"

        if isinstance(obj.endToEndRouting_parameter, dict):
            simulation_command = f"/root/mercury/shell/simulation_endToEndRouting_script.sh '{json.dumps(obj.endToEndRouting_parameter)}'"
        else:
            try:
                param_dict = json.loads(obj.endToEndRouting_parameter)
                simulation_command = f"/root/mercury/shell/simulation_endToEndRouting_script.sh '{json.dumps(param_dict)}'"
            except json.JSONDecodeError:
                simulation_command = obj.endToEndRouting_parameter

        docker_command = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '28g',
            '-d',
            '--rm',
            f'--name={container_name}',
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'chiao2',
            'bash', '-c', simulation_command
        ]

        print(f"Docker command: {' '.join(docker_command)}")

        simulation_process = subprocess.Popen(docker_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = simulation_process.communicate()
        if simulation_process.returncode != 0:
            raise Exception(f"Unable to start Docker container: {stderr.decode()}")

        container_info = subprocess.run(['docker', 'inspect', '--format', '{{.State.Pid}}', container_name],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if container_info.returncode == 0:
            container_pid = int(container_info.stdout.decode().strip())
            sim_job.endToEndRoutingSimJob_process_id = container_pid
            sim_job.save()
        else:
            raise Exception("Unable to get container process ID")

        timeout = 60 * 60
        start_time = time.time()

        while True:
            # 檢查是否超時
            if time.time() - start_time > timeout:
                print(f"Simulation timeout for endToEndRouting_uid: {endToEndRouting_uid}")
                terminate_endToEndRouting_sim_job(endToEndRouting_uid)
                return

            # 檢查容器是否存在
            container_check = subprocess.run(
                ['docker', 'ps', '-q', '-f', f'name={container_name}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            container_exists = bool(container_check.stdout.decode().strip())

            # 檢查是否有結果資料夾與檔案
            results_exist = os.path.exists(simulation_result_dir) and os.listdir(simulation_result_dir)

            # == 這裡加上除錯訊息 ==
            print("=== Debug Info ===")
            print(f"Time elapsed: {time.time() - start_time:.2f}s / Timeout: {timeout}s")
            print(f"container_exists: {container_exists}")
            print(f"simulation_result_dir: {simulation_result_dir}")
            if os.path.exists(simulation_result_dir):
                print(f"simulation_result_dir contents: {os.listdir(simulation_result_dir)}")
            else:
                print("simulation_result_dir does not exist yet.")
            print(f"results_exist: {bool(results_exist)}")
            print("==================\n")

            if results_exist and not container_exists:
                try:
                    sim_result = analyzeEndToEndRoutingResult(simulation_result_dir)
                    if sim_result is not None:
                        obj.endToEndRouting_simulation_result = sim_result
                        obj.endToEndRouting_status = "completed"
                        obj.endToEndRouting_data_path = simulation_result_dir
                        obj.save()

                        sim_job.endToEndRoutingSimJob_end_time = timezone.now()
                        sim_job.save()

                        pdf_path = genEndToEndRoutingResultPDF(obj)
                        print(f"Simulation completed successfully, results saved for endToEndRouting_uid: {endToEndRouting_uid}")
                        print(f"PDF report generated at: {pdf_path}")
                        return
                    else:
                        obj.endToEndRouting_status = "simulation_failed"
                        obj.save()
                        print(f"simulation_failed: No valid results for endToEndRouting_uid: {endToEndRouting_uid}")

                except Exception as e:
                    error_message = f"Error processing simulation results: {str(e)}"
                    obj.endToEndRouting_status = "error"
                    obj.save()
                    print(error_message)

            if not container_exists and not results_exist:
                raise Exception("Container stopped but no results found, simulation_failed")

            time.sleep(10)

            obj.refresh_from_db()
            if obj.endToEndRouting_status == "simulation_failed":
                return

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_endToEndRouting_sim_job(endToEndRouting_uid)


class endToEndRoutingSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_endToEndRouting_sim_job(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                endToEndRouting_uid = data.get('endToEndRouting_uid')
                if not endToEndRouting_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 endToEndRouting_uid 參數'
                    }, status=400)

                try:
                    obj = EndToEndRouting.objects.get(endToEndRouting_uid=endToEndRouting_uid)
                except EndToEndRouting.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 EndToEndRouting'
                    }, status=404)

                if not obj.endToEndRouting_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'EndToEndRouting 缺少參數 endToEndRouting_parameter'
                    }, status=400)

                current_sim_job = EndToEndRoutingSimJob.objects.filter(
                    f_endToEndRouting_uid=obj,
                    endToEndRoutingSimJob_end_time__isnull=True
                ).first()
                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此 EndToEndRouting 正在執行模擬作業中',
                        'data': {
                            'endToEndRoutingSimJob_uid': str(current_sim_job.endToEndRoutingSimJob_uid),
                            'endToEndRouting_uid': str(endToEndRouting_uid),
                            'endToEndRouting_status': obj.endToEndRouting_status
                        }
                    })

                other_sim_job = EndToEndRoutingSimJob.objects.filter(
                    f_endToEndRouting_uid__f_user_uid=obj.f_user_uid,
                    endToEndRoutingSimJob_end_time__isnull=True
                ).exclude(
                    f_endToEndRouting_uid__endToEndRouting_uid=endToEndRouting_uid
                ).select_related(f"f_endToEndRouting_uid").first()

                if other_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '使用者已有其他正在執行的模擬作業',
                        'data': {
                            'endToEndRoutingSimJob_uid': str(other_sim_job.endToEndRoutingSimJob_uid),
                            'endToEndRouting_uid': str(other_sim_job.f_endToEndRouting_uid.endToEndRouting_uid),
                            'current_endToEndRouting_uid': str(endToEndRouting_uid),
                            'endToEndRouting_status': other_sim_job.f_endToEndRouting_uid.endToEndRouting_status
                        }
                    })

                if obj.endToEndRouting_status == "completed":
                    if obj.endToEndRouting_data_path and os.path.exists(obj.endToEndRouting_data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已經執行完成，結果可供使用',
                            'data': {
                                'endToEndRouting_uid': str(endToEndRouting_uid),
                                'endToEndRouting_status': obj.endToEndRouting_status,
                                'endToEndRouting_data_path': obj.endToEndRouting_data_path
                            }
                        })
                    else:
                        obj.endToEndRouting_status = "simulation_failed"
                        obj.save()

                simulation_thread = threading.Thread(
                    target=run_endToEndRouting_simulation_async,
                    args=(endToEndRouting_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'endToEndRouting_uid': str(endToEndRouting_uid),
                        'endToEndRouting_status': 'processing',
                        'endToEndRouting_parameter': obj.endToEndRouting_parameter,
                        'endToEndRouting_data_path': obj.endToEndRouting_data_path
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
    def delete_endToEndRouting_sim_result(request):
        try:
            data = json.loads(request.body)
            endToEndRouting_uid = data.get('endToEndRouting_uid')
            if not endToEndRouting_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'endToEndRouting_uid is required'
                }, status=400)

            try:
                obj = EndToEndRouting.objects.get(endToEndRouting_uid=endToEndRouting_uid)
            except EndToEndRouting.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'EndToEndRouting not found'
                }, status=404)

            EndToEndRoutingSimJob.objects.filter(f_endToEndRouting_uid=obj).delete()

            if not obj.endToEndRouting_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No simulation result path found'
                }, status=404)

            full_path = os.path.join('./', obj.endToEndRouting_data_path)
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Simulation result directory not found: {obj.endToEndRouting_data_path}'
                }, status=404)

            shutil.rmtree(full_path)

            obj.endToEndRouting_status = "None"
            obj.save()

            return JsonResponse({
                'status': 'success',
                'message': 'EndToEndRouting simulation result and related jobs deleted successfully'
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
    def download_endToEndRouting_sim_result(request):
        try:
            data = json.loads(request.body)
            endToEndRouting_uid = data.get('endToEndRouting_uid')
            if not endToEndRouting_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'endToEndRouting_uid is required'
                }, status=400)

            try:
                obj = EndToEndRouting.objects.get(endToEndRouting_uid=endToEndRouting_uid)
            except EndToEndRouting.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'EndToEndRouting not found'
                }, status=404)

            if not obj.endToEndRouting_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'EndToEndRouting data path not found'
                }, status=404)

            pdf_path = os.path.join(obj.endToEndRouting_data_path, 'endToEndRouting_simulation_report.pdf')
            print(f"Attempting to download PDF from path: {pdf_path}")

            if not os.path.exists(pdf_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'PDF file not found'
                }, status=404)

            try:
                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="endToEndRouting_simulation_report.pdf"'
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
