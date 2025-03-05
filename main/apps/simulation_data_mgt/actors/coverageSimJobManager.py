from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json
from main.apps.meta_data_mgt.models.CoverageModel import Coverage
from main.apps.simulation_data_mgt.models.CoverageSimJobModel import CoverageSimJob
from main.apps.simulation_data_mgt.services.analyzeCoverageAnalysisResult import analyzeCoverageAnalysisResult
from main.apps.simulation_data_mgt.services.genCoverageAnalysisResultPDF import genCoverageAnalysisResultPDF
from main.utils.logger import log_trigger, log_writer
import os
import threading
from django.utils import timezone
import subprocess
import time
import shutil


@log_trigger('INFO')
def terminate_coverage_sim_job(coverage_uid):
    try:
        obj = Coverage.objects.get(coverage_uid=coverage_uid)
        sim_jobs = CoverageSimJob.objects.filter(
            f_coverage_uid=obj,
            coverageSimJob_end_time__isnull=True
        )

        container_name = f"coverageSimulation_{coverage_uid}"

        try:
            subprocess.run(['docker', 'stop', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            subprocess.run(['docker', 'rm', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', container_name])
        except Exception as e:
            print(f"Docker container stop error: {str(e)}")

        sim_jobs.delete()

        obj.coverage_status = "simulation_failed"
        obj.save()

        print(f"All related simulation jobs terminated for coverage_uid: {coverage_uid}")
        return True

    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False


@log_trigger('INFO')
def run_coverage_simulation_async(coverage_uid):
    sim_job = None
    try:
        obj = Coverage.objects.get(coverage_uid=coverage_uid)
        sim_job = CoverageSimJob.objects.create(
            f_coverage_uid=obj,
            coverageSimJob_start_time=timezone.now()
        )

        obj.coverage_status = "processing"
        obj.save()

        simulation_result_dir = os.path.join(
            'simulation_result', 'coverage_simulation',
            str(obj.f_user_uid.user_uid),
            str(coverage_uid)
        )
        print(f"Simulation result directory: {simulation_result_dir}")
        os.makedirs(simulation_result_dir, exist_ok=True)

        container_name = f"coverageSimulation_{coverage_uid}"

        if isinstance(obj.coverage_parameter, dict):
            simulation_command = f"/root/mercury/shell/simulation_coverage_script.sh '{json.dumps(obj.coverage_parameter)}'"
        else:
            try:
                param_dict = json.loads(obj.coverage_parameter)
                simulation_command = f"/root/mercury/shell/simulation_coverage_script.sh '{json.dumps(param_dict)}'"
            except json.JSONDecodeError:
                simulation_command = obj.coverage_parameter

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
            sim_job.coverageSimJob_process_id = container_pid
            sim_job.save()
        else:
            raise Exception("Unable to get container process ID")

        timeout = 60 * 60 * 8
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                print(f"Simulation timeout for coverage_uid: {coverage_uid}")
                terminate_coverage_sim_job(coverage_uid)
                return

            container_check = subprocess.run(['docker', 'ps', '-q', '-f', f'name={container_name}'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            container_exists = bool(container_check.stdout.decode().strip())

            results_exist = os.path.exists(simulation_result_dir) and os.listdir(simulation_result_dir)

            if results_exist and not container_exists:
                try:
                    sim_result = analyzeCoverageAnalysisResult(simulation_result_dir)
                    if sim_result is not None:
                        obj.coverage_simulation_result = sim_result
                        obj.coverage_status = "completed"
                        obj.coverage_data_path = simulation_result_dir
                        obj.save()

                        sim_job.coverageSimJob_end_time = timezone.now()
                        sim_job.save()

                        pdf_path = genCoverageAnalysisResultPDF(obj)
                        print(f"Simulation completed successfully, results saved for coverage_uid: {coverage_uid}")
                        print(f"PDF report generated at: {pdf_path}")
                        return
                    else:
                        obj.coverage_status = "simulation_failed"
                        obj.save()
                        print(f"simulation_failed: No valid results for coverage_uid: {coverage_uid}")

                except Exception as e:
                    error_message = f"Error processing simulation results: {str(e)}"
                    obj.coverage_status = "error"
                    obj.save()

            if not container_exists and not results_exist:
                raise Exception("Container stopped but no results found, simulation_failed")

            time.sleep(10)

            obj.refresh_from_db()
            if obj.coverage_status == "simulation_failed":
                return

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_coverage_sim_job(coverage_uid)


class coverageSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_coverage_sim_job(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                coverage_uid = data.get('coverage_uid')
                if not coverage_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 coverage_uid 參數'
                    }, status=400)

                try:
                    obj = Coverage.objects.get(coverage_uid=coverage_uid)
                except Coverage.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 Coverage'
                    }, status=404)

                if not obj.coverage_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage 缺少參數 coverage_parameter'
                    }, status=400)

                current_sim_job = CoverageSimJob.objects.filter(
                    f_coverage_uid=obj,
                    coverageSimJob_end_time__isnull=True
                ).first()
                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此 Coverage 正在執行模擬作業中',
                        'data': {
                            'coverageSimJob_uid': str(current_sim_job.coverageSimJob_uid),
                            'coverage_uid': str(coverage_uid),
                            'coverage_status': obj.coverage_status
                        }
                    })

                other_sim_job = CoverageSimJob.objects.filter(
                    f_coverage_uid__f_user_uid=obj.f_user_uid,
                    coverageSimJob_end_time__isnull=True
                ).exclude(
                    f_coverage_uid__coverage_uid=coverage_uid
                ).select_related(f"f_coverage_uid").first()

                if other_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '使用者已有其他正在執行的模擬作業',
                        'data': {
                            'coverageSimJob_uid': str(other_sim_job.coverageSimJob_uid),
                            'coverage_uid': str(other_sim_job.f_coverage_uid.coverage_uid),
                            'current_coverage_uid': str(coverage_uid),
                            'coverage_status': other_sim_job.f_coverage_uid.coverage_status
                        }
                    })

                if obj.coverage_status == "completed":
                    if obj.coverage_data_path and os.path.exists(obj.coverage_data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已經執行完成，結果可供使用',
                            'data': {
                                'coverage_uid': str(coverage_uid),
                                'coverage_status': obj.coverage_status,
                                'coverage_data_path': obj.coverage_data_path
                            }
                        })
                    else:
                        obj.coverage_status = "simulation_failed"
                        obj.save()

                simulation_thread = threading.Thread(
                    target=run_coverage_simulation_async,
                    args=(coverage_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'coverage_uid': str(coverage_uid),
                        'coverage_status': 'processing',
                        'coverage_parameter': obj.coverage_parameter,
                        'coverage_data_path': obj.coverage_data_path
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
    def delete_coverage_sim_result(request):
        try:
            data = json.loads(request.body)
            coverage_uid = data.get('coverage_uid')
            if not coverage_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'coverage_uid is required'
                }, status=400)

            try:
                obj = Coverage.objects.get(coverage_uid=coverage_uid)
            except Coverage.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Coverage not found'
                }, status=404)

            CoverageSimJob.objects.filter(f_coverage_uid=obj).delete()

            if not obj.coverage_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No simulation result path found'
                }, status=404)

            full_path = os.path.join('./', obj.coverage_data_path)
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Simulation result directory not found: {obj.coverage_data_path}'
                }, status=404)

            shutil.rmtree(full_path)

            obj.coverage_status = "None"
            obj.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Coverage simulation result and related jobs deleted successfully'
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
    def download_coverage_sim_result(request):
        try:
            data = json.loads(request.body)
            coverage_uid = data.get('coverage_uid')
            if not coverage_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'coverage_uid is required'
                }, status=400)

            try:
                obj = Coverage.objects.get(coverage_uid=coverage_uid)
            except Coverage.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Coverage not found'
                }, status=404)

            if not obj.coverage_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Coverage data path not found'
                }, status=404)

            pdf_path = os.path.join(obj.coverage_data_path, 'coverage_simulation_report.pdf')
            print(f"Attempting to download PDF from path: {pdf_path}")

            if not os.path.exists(pdf_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'PDF file not found'
                }, status=404)

            try:
                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="coverage_simulation_report.pdf"'
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
