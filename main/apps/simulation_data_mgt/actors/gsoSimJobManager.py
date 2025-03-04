from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json
from main.apps.meta_data_mgt.models.GsoModel import Gso
from main.apps.simulation_data_mgt.models.GsoSimJobModel import GsoSimJob
from main.apps.simulation_data_mgt.services.analyzeGsoResult import analyzeGsoResult
from main.apps.simulation_data_mgt.services.genGsoResultPDF import genGsoResultPDF
from main.utils.logger import log_trigger, log_writer
import os
import threading
from django.utils import timezone
import subprocess
import time
import shutil


@log_trigger('INFO')
def terminate_gso_sim_job(gso_uid):
    try:
        obj = Gso.objects.get(gso_uid=gso_uid)
        sim_jobs = GsoSimJob.objects.filter(
            f_gso_uid=obj,
            gsoSimJob_end_time__isnull=True
        )

        container_name = f"gsoSimulation_{gso_uid}"

        try:
            subprocess.run(['docker', 'stop', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', container_name])
        except Exception as e:
            print(f"Docker container stop error: {str(e)}")

        sim_jobs.delete()

        obj.gso_status = "simulation_failed"
        obj.save()

        print(f"All related simulation jobs terminated for gso_uid: {gso_uid}")
        return True

    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False


@log_trigger('INFO')
def run_gso_simulation_async(gso_uid):
    sim_job = None
    try:
        obj = Gso.objects.get(gso_uid=gso_uid)
        sim_job = GsoSimJob.objects.create(
            f_gso_uid=obj,
            gsoSimJob_start_time=timezone.now()
        )

        obj.gso_status = "processing"
        obj.save()

        simulation_result_dir = os.path.join(
            'simulation_result', 'gso_simulation',
            str(obj.f_user_uid.user_uid),
            str(gso_uid)
        )
        print(f"Simulation result directory: {simulation_result_dir}")
        os.makedirs(simulation_result_dir, exist_ok=True)

        container_name = f"gsoSimulation_{gso_uid}"

        if isinstance(obj.gso_parameter, dict):
            simulation_command = f"/root/mercury/shell/simulation_gso_script.sh '{json.dumps(obj.gso_parameter)}'"
        else:
            try:
                param_dict = json.loads(obj.gso_parameter)
                simulation_command = f"/root/mercury/shell/simulation_gso_script.sh '{json.dumps(param_dict)}'"
            except json.JSONDecodeError:
                simulation_command = obj.gso_parameter

        docker_command = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '150g',
            '-d',
            '--rm',
            f'--name={container_name}',
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'handoversimulationimage_test',
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
            sim_job.gsoSimJob_process_id = container_pid
            sim_job.save()
        else:
            raise Exception("Unable to get container process ID")

        timeout = 60 * 60 * 8
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                print(f"Simulation timeout for gso_uid: {gso_uid}")
                terminate_gso_sim_job(gso_uid)
                return

            container_check = subprocess.run(['docker', 'ps', '-q', '-f', f'name={container_name}'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            container_exists = bool(container_check.stdout.decode().strip())

            results_exist = os.path.exists(simulation_result_dir) and os.listdir(simulation_result_dir)

            if results_exist and not container_exists:
                try:
                    sim_result = analyzeGsoResult(simulation_result_dir)
                    if sim_result is not None:
                        obj.gso_simulation_result = sim_result
                        obj.gso_status = "completed"
                        obj.gso_data_path = simulation_result_dir
                        obj.save()

                        sim_job.gsoSimJob_end_time = timezone.now()
                        sim_job.save()

                        pdf_path = genGsoResultPDF(obj)
                        print(f"Simulation completed successfully, results saved for gso_uid: {gso_uid}")
                        print(f"PDF report generated at: {pdf_path}")
                        return
                    else:
                        obj.gso_status = "simulation_failed"
                        obj.save()
                        print(f"simulation_failed: No valid results for gso_uid: {gso_uid}")

                except Exception as e:
                    error_message = f"Error processing simulation results: {str(e)}"
                    obj.gso_status = "error"
                    obj.save()

            if not container_exists and not results_exist:
                raise Exception("Container stopped but no results found, simulation_failed")

            time.sleep(10)

            obj.refresh_from_db()
            if obj.gso_status == "simulation_failed":
                return

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_gso_sim_job(gso_uid)


class gsoSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_gso_sim_job(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                gso_uid = data.get('gso_uid')
                if not gso_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 gso_uid 參數'
                    }, status=400)

                try:
                    obj = Gso.objects.get(gso_uid=gso_uid)
                except Gso.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 Gso'
                    }, status=404)

                if not obj.gso_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Gso 缺少參數 gso_parameter'
                    }, status=400)

                current_sim_job = GsoSimJob.objects.filter(
                    f_gso_uid=obj,
                    gsoSimJob_end_time__isnull=True
                ).first()
                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此 Gso 正在執行模擬作業中',
                        'data': {
                            'gsoSimJob_uid': str(current_sim_job.gsoSimJob_uid),
                            'gso_uid': str(gso_uid),
                            'gso_status': obj.gso_status
                        }
                    })

                other_sim_job = GsoSimJob.objects.filter(
                    f_gso_uid__f_user_uid=obj.f_user_uid,
                    gsoSimJob_end_time__isnull=True
                ).exclude(
                    f_gso_uid__gso_uid=gso_uid
                ).select_related(f"f_gso_uid").first()

                if other_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '使用者已有其他正在執行的模擬作業',
                        'data': {
                            'gsoSimJob_uid': str(other_sim_job.gsoSimJob_uid),
                            'gso_uid': str(other_sim_job.f_gso_uid.gso_uid),
                            'current_gso_uid': str(gso_uid),
                            'gso_status': other_sim_job.f_gso_uid.gso_status
                        }
                    })

                if obj.gso_status == "completed":
                    if obj.gso_data_path and os.path.exists(obj.gso_data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已經執行完成，結果可供使用',
                            'data': {
                                'gso_uid': str(gso_uid),
                                'gso_status': obj.gso_status,
                                'gso_data_path': obj.gso_data_path
                            }
                        })
                    else:
                        obj.gso_status = "simulation_failed"
                        obj.save()

                simulation_thread = threading.Thread(
                    target=run_gso_simulation_async,
                    args=(gso_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'gso_uid': str(gso_uid),
                        'gso_status': 'processing',
                        'gso_parameter': obj.gso_parameter,
                        'gso_data_path': obj.gso_data_path
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
    def delete_gso_sim_result(request):
        try:
            data = json.loads(request.body)
            gso_uid = data.get('gso_uid')
            if not gso_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'gso_uid is required'
                }, status=400)

            try:
                obj = Gso.objects.get(gso_uid=gso_uid)
            except Gso.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Gso not found'
                }, status=404)

            GsoSimJob.objects.filter(f_gso_uid=obj).delete()

            if not obj.gso_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No simulation result path found'
                }, status=404)

            full_path = os.path.join('./', obj.gso_data_path)
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Simulation result directory not found: {obj.gso_data_path}'
                }, status=404)

            shutil.rmtree(full_path)

            obj.gso_status = "None"
            obj.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Gso simulation result and related jobs deleted successfully'
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
    def download_gso_sim_result(request):
        try:
            data = json.loads(request.body)
            gso_uid = data.get('gso_uid')
            if not gso_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'gso_uid is required'
                }, status=400)

            try:
                obj = Gso.objects.get(gso_uid=gso_uid)
            except Gso.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Gso not found'
                }, status=404)

            if not obj.gso_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Gso data path not found'
                }, status=404)

            pdf_path = os.path.join(obj.gso_data_path, 'gso_simulation_report.pdf')
            print(f"Attempting to download PDF from path: {pdf_path}")

            if not os.path.exists(pdf_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'PDF file not found'
                }, status=404)

            try:
                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="gso_simulation_report.pdf"'
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
