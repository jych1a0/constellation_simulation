from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json
from main.apps.meta_data_mgt.models.OneToMultiModel import OneToMulti
from main.apps.simulation_data_mgt.models.OneToMultiSimJobModel import OneToMultiSimJob
from main.apps.simulation_data_mgt.services.analyzeOneToMultiResult import analyzeOneToMultiResult
from main.apps.simulation_data_mgt.services.genOneToMultiResultPDF import genOneToMultiResultPDF
from main.utils.logger import log_trigger, log_writer
import os
import threading
from django.utils import timezone
import subprocess
import time
import shutil


@log_trigger('INFO')
def terminate_oneToMulti_sim_job(oneToMulti_uid):
    try:
        obj = OneToMulti.objects.get(oneToMulti_uid=oneToMulti_uid)
        sim_jobs = OneToMultiSimJob.objects.filter(
            f_oneToMulti_uid=obj,
            oneToMultiSimJob_end_time__isnull=True
        )

        container_name = f"oneToMultiSimulation_{oneToMulti_uid}"

        try:
            subprocess.run(['docker', 'stop', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', container_name])
        except Exception as e:
            print(f"Docker container stop error: {str(e)}")

        sim_jobs.delete()

        obj.oneToMulti_status = "simulation_failed"
        obj.save()

        print(f"All related simulation jobs terminated for oneToMulti_uid: {oneToMulti_uid}")
        return True

    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False


@log_trigger('INFO')
def run_oneToMulti_simulation_async(oneToMulti_uid):
    sim_job = None
    try:
        obj = OneToMulti.objects.get(oneToMulti_uid=oneToMulti_uid)
        sim_job = OneToMultiSimJob.objects.create(
            f_oneToMulti_uid=obj,
            oneToMultiSimJob_start_time=timezone.now()
        )

        obj.oneToMulti_status = "processing"
        obj.save()

        simulation_result_dir = os.path.join(
            'simulation_result', 'oneToMulti_simulation',
            str(obj.f_user_uid.user_uid),
            str(oneToMulti_uid)
        )
        print(f"Simulation result directory: {simulation_result_dir}")
        os.makedirs(simulation_result_dir, exist_ok=True)

        container_name = f"oneToMultiSimulation_{oneToMulti_uid}"

        if isinstance(obj.oneToMulti_parameter, dict):
            simulation_command = f"/root/mercury/shell/simulation_oneToMulti_script.sh '{json.dumps(obj.oneToMulti_parameter)}'"
        else:
            try:
                param_dict = json.loads(obj.oneToMulti_parameter)
                simulation_command = f"/root/mercury/shell/simulation_oneToMulti_script.sh '{json.dumps(param_dict)}'"
            except json.JSONDecodeError:
                simulation_command = obj.oneToMulti_parameter

        docker_command = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '28g',
            '-d',
            '--rm',
            f'--name={container_name}',
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'routingimage',
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
            sim_job.oneToMultiSimJob_process_id = container_pid
            sim_job.save()
        else:
            raise Exception("Unable to get container process ID")

        timeout = 60 * 60 * 8
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                print(f"Simulation timeout for oneToMulti_uid: {oneToMulti_uid}")
                terminate_oneToMulti_sim_job(oneToMulti_uid)
                return

            container_check = subprocess.run(['docker', 'ps', '-q', '-f', f'name={container_name}'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            container_exists = bool(container_check.stdout.decode().strip())

            results_exist = os.path.exists(simulation_result_dir) and os.listdir(simulation_result_dir)

            if results_exist and not container_exists:
                try:
                    sim_result = analyzeOneToMultiResult(simulation_result_dir)
                    if sim_result is not None:
                        obj.oneToMulti_simulation_result = sim_result
                        obj.oneToMulti_status = "completed"
                        obj.oneToMulti_data_path = simulation_result_dir
                        obj.save()

                        sim_job.oneToMultiSimJob_end_time = timezone.now()
                        sim_job.save()

                        pdf_path = genOneToMultiResultPDF(obj)
                        print(f"Simulation completed successfully, results saved for oneToMulti_uid: {oneToMulti_uid}")
                        print(f"PDF report generated at: {pdf_path}")
                        return
                    else:
                        obj.oneToMulti_status = "simulation_failed"
                        obj.save()
                        print(f"simulation_failed: No valid results for oneToMulti_uid: {oneToMulti_uid}")

                except Exception as e:
                    error_message = f"Error processing simulation results: {str(e)}"
                    obj.oneToMulti_status = "error"
                    obj.save()

            if not container_exists and not results_exist:
                raise Exception("Container stopped but no results found, simulation_failed")

            time.sleep(10)

            obj.refresh_from_db()
            if obj.oneToMulti_status == "simulation_failed":
                return

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_oneToMulti_sim_job(oneToMulti_uid)


class oneToMultiSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_oneToMulti_sim_job(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                oneToMulti_uid = data.get('oneToMulti_uid')
                if not oneToMulti_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 oneToMulti_uid 參數'
                    }, status=400)

                try:
                    obj = OneToMulti.objects.get(oneToMulti_uid=oneToMulti_uid)
                except OneToMulti.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 OneToMulti'
                    }, status=404)

                if not obj.oneToMulti_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'OneToMulti 缺少參數 oneToMulti_parameter'
                    }, status=400)

                current_sim_job = OneToMultiSimJob.objects.filter(
                    f_oneToMulti_uid=obj,
                    oneToMultiSimJob_end_time__isnull=True
                ).first()
                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此 OneToMulti 正在執行模擬作業中',
                        'data': {
                            'oneToMultiSimJob_uid': str(current_sim_job.oneToMultiSimJob_uid),
                            'oneToMulti_uid': str(oneToMulti_uid),
                            'oneToMulti_status': obj.oneToMulti_status
                        }
                    })

                other_sim_job = OneToMultiSimJob.objects.filter(
                    f_oneToMulti_uid__f_user_uid=obj.f_user_uid,
                    oneToMultiSimJob_end_time__isnull=True
                ).exclude(
                    f_oneToMulti_uid__oneToMulti_uid=oneToMulti_uid
                ).select_related(f"f_oneToMulti_uid").first()

                if other_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '使用者已有其他正在執行的模擬作業',
                        'data': {
                            'oneToMultiSimJob_uid': str(other_sim_job.oneToMultiSimJob_uid),
                            'oneToMulti_uid': str(other_sim_job.f_oneToMulti_uid.oneToMulti_uid),
                            'current_oneToMulti_uid': str(oneToMulti_uid),
                            'oneToMulti_status': other_sim_job.f_oneToMulti_uid.oneToMulti_status
                        }
                    })

                if obj.oneToMulti_status == "completed":
                    if obj.oneToMulti_data_path and os.path.exists(obj.oneToMulti_data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已經執行完成，結果可供使用',
                            'data': {
                                'oneToMulti_uid': str(oneToMulti_uid),
                                'oneToMulti_status': obj.oneToMulti_status,
                                'oneToMulti_data_path': obj.oneToMulti_data_path
                            }
                        })
                    else:
                        obj.oneToMulti_status = "simulation_failed"
                        obj.save()

                simulation_thread = threading.Thread(
                    target=run_oneToMulti_simulation_async,
                    args=(oneToMulti_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'oneToMulti_uid': str(oneToMulti_uid),
                        'oneToMulti_status': 'processing',
                        'oneToMulti_parameter': obj.oneToMulti_parameter,
                        'oneToMulti_data_path': obj.oneToMulti_data_path
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
    def delete_oneToMulti_sim_result(request):
        try:
            data = json.loads(request.body)
            oneToMulti_uid = data.get('oneToMulti_uid')
            if not oneToMulti_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'oneToMulti_uid is required'
                }, status=400)

            try:
                obj = OneToMulti.objects.get(oneToMulti_uid=oneToMulti_uid)
            except OneToMulti.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'OneToMulti not found'
                }, status=404)

            OneToMultiSimJob.objects.filter(f_oneToMulti_uid=obj).delete()

            if not obj.oneToMulti_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No simulation result path found'
                }, status=404)

            full_path = os.path.join('./', obj.oneToMulti_data_path)
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Simulation result directory not found: {obj.oneToMulti_data_path}'
                }, status=404)

            shutil.rmtree(full_path)

            obj.oneToMulti_status = "None"
            obj.save()

            return JsonResponse({
                'status': 'success',
                'message': 'OneToMulti simulation result and related jobs deleted successfully'
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
    def download_oneToMulti_sim_result(request):
        try:
            data = json.loads(request.body)
            oneToMulti_uid = data.get('oneToMulti_uid')
            if not oneToMulti_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'oneToMulti_uid is required'
                }, status=400)

            try:
                obj = OneToMulti.objects.get(oneToMulti_uid=oneToMulti_uid)
            except OneToMulti.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'OneToMulti not found'
                }, status=404)

            if not obj.oneToMulti_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'OneToMulti data path not found'
                }, status=404)

            pdf_path = os.path.join(obj.oneToMulti_data_path, 'oneToMulti_simulation_report.pdf')
            print(f"Attempting to download PDF from path: {pdf_path}")

            if not os.path.exists(pdf_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'PDF file not found'
                }, status=404)

            try:
                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="oneToMulti_simulation_report.pdf"'
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
