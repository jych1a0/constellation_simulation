from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json
from main.apps.meta_data_mgt.models.IslHoppingModel import IslHopping
from main.apps.simulation_data_mgt.models.IslHoppingSimJobModel import IslHoppingSimJob
# from main.apps.simulation_data_mgt.services.analyzeIslHoppingResult import analyzeIslHoppingResult
# from main.apps.simulation_data_mgt.services.genIslHoppingResultPDF import genIslHoppingResultPDF
from main.utils.logger import log_trigger, log_writer
import os
import threading
from django.utils import timezone
import subprocess
import time
import shutil


@log_trigger('INFO')
def terminate_islHopping_sim_job(islHopping_uid):
    try:
        obj = IslHopping.objects.get(islHopping_uid=islHopping_uid)
        sim_jobs = IslHoppingSimJob.objects.filter(
            f_islHopping_uid=obj,
            islHoppingSimJob_end_time__isnull=True
        )

        container_name = f"islHoppingSimulation_{islHopping_uid}"

        try:
            subprocess.run(['docker', 'stop', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', container_name])
        except Exception as e:
            print(f"Docker container stop error: {str(e)}")

        sim_jobs.delete()

        obj.islHopping_status = "simulation_failed"
        obj.save()

        print(f"All related simulation jobs terminated for islHopping_uid: {islHopping_uid}")
        return True

    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False


@log_trigger('INFO')
def run_islHopping_simulation_async(islHopping_uid):
    sim_job = None
    try:
        obj = IslHopping.objects.get(islHopping_uid=islHopping_uid)
        sim_job = IslHoppingSimJob.objects.create(
            f_islHopping_uid=obj,
            islHoppingSimJob_start_time=timezone.now()
        )

        obj.islHopping_status = "processing"
        obj.save()

        simulation_result_dir = os.path.join(
            'simulation_result', 'islHopping_simulation',
            str(obj.f_user_uid.user_uid),
            str(islHopping_uid)
        )
        print(f"Simulation result directory: {simulation_result_dir}")
        os.makedirs(simulation_result_dir, exist_ok=True)

        container_name = f"islHoppingSimulation_{islHopping_uid}"

        if isinstance(obj.islHopping_parameter, dict):
            simulation_command = f"/root/mercury/shell/simulation_islHopping_script.sh '{json.dumps(obj.islHopping_parameter)}'"
        else:
            try:
                param_dict = json.loads(obj.islHopping_parameter)
                simulation_command = f"/root/mercury/shell/simulation_islHopping_script.sh '{json.dumps(param_dict)}'"
            except json.JSONDecodeError:
                simulation_command = obj.islHopping_parameter

        docker_command = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '28g',
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
            sim_job.islHoppingSimJob_process_id = container_pid
            sim_job.save()
        else:
            raise Exception("Unable to get container process ID")

        timeout = 60 * 60
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                print(f"Simulation timeout for islHopping_uid: {islHopping_uid}")
                terminate_islHopping_sim_job(islHopping_uid)
                return

            container_check = subprocess.run(['docker', 'ps', '-q', '-f', f'name={container_name}'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            container_exists = bool(container_check.stdout.decode().strip())

            results_exist = os.path.exists(simulation_result_dir) and os.listdir(simulation_result_dir)

            if results_exist and not container_exists:
                try:
                    sim_result = analyzeIslHoppingResult(simulation_result_dir)
                    if sim_result is not None:
                        obj.islHopping_simulation_result = sim_result
                        obj.islHopping_status = "completed"
                        obj.islHopping_data_path = simulation_result_dir
                        obj.save()

                        sim_job.islHoppingSimJob_end_time = timezone.now()
                        sim_job.save()

                        pdf_path = genIslHoppingResultPDF(obj)
                        print(f"Simulation completed successfully, results saved for islHopping_uid: {islHopping_uid}")
                        print(f"PDF report generated at: {pdf_path}")
                        return
                    else:
                        obj.islHopping_status = "simulation_failed"
                        obj.save()
                        print(f"simulation_failed: No valid results for islHopping_uid: {islHopping_uid}")

                except Exception as e:
                    error_message = f"Error processing simulation results: {str(e)}"
                    obj.islHopping_status = "error"
                    obj.save()

            if not container_exists and not results_exist:
                raise Exception("Container stopped but no results found, simulation_failed")

            time.sleep(10)

            obj.refresh_from_db()
            if obj.islHopping_status == "simulation_failed":
                return

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_islHopping_sim_job(islHopping_uid)


class islHoppingSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_islHopping_sim_job(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                islHopping_uid = data.get('islHopping_uid')
                if not islHopping_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 islHopping_uid 參數'
                    }, status=400)

                try:
                    obj = IslHopping.objects.get(islHopping_uid=islHopping_uid)
                except IslHopping.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 IslHopping'
                    }, status=404)

                if not obj.islHopping_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'IslHopping 缺少參數 islHopping_parameter'
                    }, status=400)

                current_sim_job = IslHoppingSimJob.objects.filter(
                    f_islHopping_uid=obj,
                    islHoppingSimJob_end_time__isnull=True
                ).first()
                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此 IslHopping 正在執行模擬作業中',
                        'data': {
                            'islHoppingSimJob_uid': str(current_sim_job.islHoppingSimJob_uid),
                            'islHopping_uid': str(islHopping_uid),
                            'islHopping_status': obj.islHopping_status
                        }
                    })

                other_sim_job = IslHoppingSimJob.objects.filter(
                    f_islHopping_uid__f_user_uid=obj.f_user_uid,
                    islHoppingSimJob_end_time__isnull=True
                ).exclude(
                    f_islHopping_uid__islHopping_uid=islHopping_uid
                ).select_related(f"f_islHopping_uid").first()

                if other_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '使用者已有其他正在執行的模擬作業',
                        'data': {
                            'islHoppingSimJob_uid': str(other_sim_job.islHoppingSimJob_uid),
                            'islHopping_uid': str(other_sim_job.f_islHopping_uid.islHopping_uid),
                            'current_islHopping_uid': str(islHopping_uid),
                            'islHopping_status': other_sim_job.f_islHopping_uid.islHopping_status
                        }
                    })

                if obj.islHopping_status == "completed":
                    if obj.islHopping_data_path and os.path.exists(obj.islHopping_data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已經執行完成，結果可供使用',
                            'data': {
                                'islHopping_uid': str(islHopping_uid),
                                'islHopping_status': obj.islHopping_status,
                                'islHopping_data_path': obj.islHopping_data_path
                            }
                        })
                    else:
                        obj.islHopping_status = "simulation_failed"
                        obj.save()

                simulation_thread = threading.Thread(
                    target=run_islHopping_simulation_async,
                    args=(islHopping_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'islHopping_uid': str(islHopping_uid),
                        'islHopping_status': 'processing',
                        'islHopping_parameter': obj.islHopping_parameter,
                        'islHopping_data_path': obj.islHopping_data_path
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
    def delete_islHopping_sim_result(request):
        try:
            data = json.loads(request.body)
            islHopping_uid = data.get('islHopping_uid')
            if not islHopping_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'islHopping_uid is required'
                }, status=400)

            try:
                obj = IslHopping.objects.get(islHopping_uid=islHopping_uid)
            except IslHopping.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'IslHopping not found'
                }, status=404)

            IslHoppingSimJob.objects.filter(f_islHopping_uid=obj).delete()

            if not obj.islHopping_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No simulation result path found'
                }, status=404)

            full_path = os.path.join('./', obj.islHopping_data_path)
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Simulation result directory not found: {obj.islHopping_data_path}'
                }, status=404)

            shutil.rmtree(full_path)

            obj.islHopping_status = "None"
            obj.save()

            return JsonResponse({
                'status': 'success',
                'message': 'IslHopping simulation result and related jobs deleted successfully'
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
    def download_islHopping_sim_result(request):
        try:
            data = json.loads(request.body)
            islHopping_uid = data.get('islHopping_uid')
            if not islHopping_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'islHopping_uid is required'
                }, status=400)

            try:
                obj = IslHopping.objects.get(islHopping_uid=islHopping_uid)
            except IslHopping.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'IslHopping not found'
                }, status=404)

            if not obj.islHopping_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'IslHopping data path not found'
                }, status=404)

            pdf_path = os.path.join(obj.islHopping_data_path, 'islHopping_simulation_report.pdf')
            print(f"Attempting to download PDF from path: {pdf_path}")

            if not os.path.exists(pdf_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'PDF file not found'
                }, status=404)

            try:
                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="islHopping_simulation_report.pdf"'
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
