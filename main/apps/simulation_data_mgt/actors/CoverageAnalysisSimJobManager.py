from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.CoverageAnalysisModel import CoverageAnalysis
from main.apps.simulation_data_mgt.models.coverageAnalysisSimJobModel import CoverageAnalysisSimJob
from main.apps.simulation_data_mgt.services.analyzeCoverageAnalysisResult import analyzeCoverageAnalysisResult
from main.apps.simulation_data_mgt.services.genCoverageAnalysisResultPDF import genCoverageAnalysisResultPDF
from main.utils.logger import log_trigger, log_writer
from django.views.decorators.csrf import csrf_exempt
import os
import threading
from django.utils import timezone
import subprocess
import time
import shutil
from django.http import HttpResponse

@log_trigger('INFO')
def terminate_coverage_analysis_sim_job(coverage_analysis_uid):
    try:
        coverage_analysis = CoverageAnalysis.objects.get(coverage_analysis_uid=coverage_analysis_uid)

        sim_jobs = CoverageAnalysisSimJob.objects.filter(
            f_coverage_analysis_uid=coverage_analysis,
            coverageAnalysisSimJob_end_time__isnull=True
        )

        container_name = f"coverageAnalysisSimulation_{coverage_analysis_uid}"

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
            print(f"Docker container stop error: {str(e)}")

        sim_jobs.delete()

        coverage_analysis.coverage_analysis_status = "simulation_failed"
        coverage_analysis.save()

        print(f"All related simulation jobs terminated for coverage_analysis_uid: {coverage_analysis_uid}")
        return True

    except Exception as e:
        print(f"Simulation job termination error: {str(e)}")
        return False

@log_trigger('INFO')
def run_coverage_analysis_simulation_async(coverage_analysis_uid):
    sim_job = None
    try:
        coverage_analysis = CoverageAnalysis.objects.get(coverage_analysis_uid=coverage_analysis_uid)

        sim_job = CoverageAnalysisSimJob.objects.create(
            f_coverage_analysis_uid=coverage_analysis,
            coverageAnalysisSimJob_start_time=timezone.now()
        )

        coverage_analysis.coverage_analysis_status = "processing"
        coverage_analysis.save()

        simulation_result_dir = os.path.join(
            'simulation_result', 'coverage_analysis_simulation',
            str(coverage_analysis.f_user_uid.user_uid),
            str(coverage_analysis_uid)
        )
        print(f"Simulation result directory: {simulation_result_dir}")

        os.makedirs(simulation_result_dir, exist_ok=True)

        container_name = f"coverageAnalysisSimulation_{coverage_analysis_uid}"

        if isinstance(coverage_analysis.coverage_analysis_parameter, dict):
            simulation_command = f"/root/mercury/shell/simulation_script.sh '{json.dumps(coverage_analysis.coverage_analysis_parameter)}'"
        else:
            try:
                param_dict = json.loads(coverage_analysis.coverage_analysis_parameter)
                simulation_command = f"/root/mercury/shell/simulation_script.sh '{json.dumps(param_dict)}'"
            except json.JSONDecodeError:
                simulation_command = coverage_analysis.coverage_analysis_parameter

        docker_command = [
            'docker', 'run',
            '--oom-kill-disable=true',
            '-m', '28g',
            '-d',
            '--rm',
            f'--name={container_name}',
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'coverageanalysissimulationimage',
            'bash', '-c', simulation_command
        ]

        print(f"Docker command: {' '.join(docker_command)}")

        simulation_process = subprocess.Popen(
            docker_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = simulation_process.communicate()

        if simulation_process.returncode != 0:
            raise Exception(f"Unable to start Docker container: {stderr.decode()}")

        container_info = subprocess.run(
            ['docker', 'inspect', '--format', '{{.State.Pid}}', container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if container_info.returncode == 0:
            container_pid = int(container_info.stdout.decode().strip())
            sim_job.coverageAnalysisSimJob_process_id = container_pid
            sim_job.save()
        else:
            raise Exception("Unable to get container process ID")

        timeout = 60 * 60
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                print(f"Simulation timeout for coverage_analysis_uid: {coverage_analysis_uid}")
                terminate_coverage_analysis_sim_job(coverage_analysis_uid)
                return

            container_check = subprocess.run(
                ['docker', 'ps', '-q', '-f', f'name={container_name}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            container_exists = bool(container_check.stdout.decode().strip())

            results_exist = os.path.exists(simulation_result_dir) and os.listdir(simulation_result_dir)

            if results_exist and not container_exists:
                try:
                    coverage_analysis_simulation_result = analyzeCoverageAnalysisResult(simulation_result_dir)

                    if coverage_analysis_simulation_result is not None:
                        coverage_analysis.coverage_analysis_simulation_result = coverage_analysis_simulation_result
                        coverage_analysis.coverage_analysis_status = "completed"
                        coverage_analysis.coverage_analysis_data_path = simulation_result_dir
                        coverage_analysis.save()

                        sim_job.coverageAnalysisSimJob_end_time = timezone.now()
                        sim_job.save()

                        pdf_path = genCoverageAnalysisResultPDF(coverage_analysis)

                        print(f"Simulation completed successfully, results saved for coverage_analysis_uid: {coverage_analysis_uid}")
                        print(f"PDF report generated at: {pdf_path}")
                        return
                    else:
                        coverage_analysis.coverage_analysis_status = "simulation_failed"
                        coverage_analysis.save()

                        print(f"simulation_failed: No valid results for coverage_analysis_uid: {coverage_analysis_uid}")

                except Exception as e:
                    error_message = f"Error processing simulation results: {str(e)}"
                    coverage_analysis.coverage_analysis_status = "error"
                    coverage_analysis.save()

            if not container_exists and not results_exist:
                raise Exception("Container stopped but no results found, simulation_failed")

            time.sleep(10)

            coverage_analysis.refresh_from_db()
            if coverage_analysis.coverage_analysis_status == "simulation_failed":
                return

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_coverage_analysis_sim_job(coverage_analysis_uid)

class CoverageAnalysisSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_coverage_analysis_sim_job(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                coverage_analysis_uid = data.get('coverage_analysis_uid')

                if not coverage_analysis_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 coverage_analysis_uid 參數'
                    }, status=400)

                try:
                    coverage_analysis = CoverageAnalysis.objects.get(coverage_analysis_uid=coverage_analysis_uid)
                except CoverageAnalysis.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到對應的 Coverage Analysis'
                    }, status=404)

                if not coverage_analysis.coverage_analysis_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage Analysis 缺少參數 coverage_analysis_parameter'
                    }, status=400)

                current_sim_job = CoverageAnalysisSimJob.objects.filter(
                    f_coverage_analysis_uid=coverage_analysis,
                    coverageAnalysisSimJob_end_time__isnull=True
                ).first()

                if current_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '此 Coverage Analysis 正在執行模擬作業中',
                        'data': {
                            'coverageAnalysisSimJob_uid': str(current_sim_job.coverageAnalysisSimJob_uid),
                            'coverage_analysis_uid': str(coverage_analysis_uid),
                            'coverage_analysis_status': coverage_analysis.coverage_analysis_status
                        }
                    })

                other_sim_job = CoverageAnalysisSimJob.objects.filter(
                    f_coverage_analysis_uid__f_user_uid=coverage_analysis.f_user_uid,
                    coverageAnalysisSimJob_end_time__isnull=True
                ).exclude(
                    f_coverage_analysis_uid__coverage_analysis_uid=coverage_analysis_uid
                ).select_related('f_coverage_analysis_uid').first()

                if other_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '使用者已有其他正在執行的模擬作業',
                        'data': {
                            'coverageAnalysisSimJob_uid': str(other_sim_job.coverageAnalysisSimJob_uid),
                            'coverage_analysis_uid': str(other_sim_job.f_coverage_analysis_uid.coverage_analysis_uid),
                            'current_coverage_analysis_uid': str(coverage_analysis_uid),
                            'coverage_analysis_status': other_sim_job.f_coverage_analysis_uid.coverage_analysis_status
                        }
                    })

                if coverage_analysis.coverage_analysis_status == "completed":
                    if coverage_analysis.coverage_analysis_data_path and os.path.exists(coverage_analysis.coverage_analysis_data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模擬已經執行完成，結果可供使用',
                            'data': {
                                'coverage_analysis_uid': str(coverage_analysis_uid),
                                'coverage_analysis_status': coverage_analysis.coverage_analysis_status,
                                'coverage_analysis_data_path': coverage_analysis.coverage_analysis_data_path
                            }
                        })
                    else:
                        coverage_analysis.coverage_analysis_status = "simulation_failed"
                        coverage_analysis.save()

                simulation_thread = threading.Thread(
                    target=run_coverage_analysis_simulation_async,
                    args=(coverage_analysis_uid,)
                )
                simulation_thread.start()

                return JsonResponse({
                    'status': 'success',
                    'message': '模擬作業已成功啟動',
                    'data': {
                        'coverage_analysis_uid': str(coverage_analysis_uid),
                        'coverage_analysis_status': 'processing',
                        'coverage_analysis_parameter': coverage_analysis.coverage_analysis_parameter,
                        'coverage_analysis_data_path': coverage_analysis.coverage_analysis_data_path
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
    def delete_coverage_analysis_sim_result(request):
        try:
            data = json.loads(request.body)
            coverage_analysis_uid = data.get('coverage_analysis_uid')

            if not coverage_analysis_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'coverage_analysis_uid is required'
                }, status=400)

            try:
                coverage_analysis = CoverageAnalysis.objects.get(coverage_analysis_uid=coverage_analysis_uid)
            except CoverageAnalysis.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Coverage Analysis not found'
                }, status=404)

            CoverageAnalysisSimJob.objects.filter(
                f_coverage_analysis_uid=coverage_analysis
            ).delete()

            if not coverage_analysis.coverage_analysis_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No simulation result path found'
                }, status=404)

            full_path = os.path.join('./', coverage_analysis.coverage_analysis_data_path)
            if not os.path.exists(full_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Simulation result directory not found: {coverage_analysis.coverage_analysis_data_path}'
                }, status=404)

            shutil.rmtree(full_path)

            coverage_analysis.coverage_analysis_status = "None"
            coverage_analysis.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Coverage Analysis simulation result and related jobs deleted successfully'
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
    def download_coverage_analysis_sim_result(request):
        try:
            data = json.loads(request.body)
            coverage_analysis_uid = data.get('coverage_analysis_uid')

            if not coverage_analysis_uid:
                return JsonResponse({
                    'status': 'error',
                    'message': 'coverage_analysis_uid is required'
                }, status=400)

            try:
                coverage_analysis = CoverageAnalysis.objects.get(coverage_analysis_uid=coverage_analysis_uid)
            except CoverageAnalysis.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Coverage Analysis not found'
                }, status=404)

            if not coverage_analysis.coverage_analysis_data_path:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Coverage Analysis data path not found'
                }, status=404)

            pdf_path = os.path.join(
                coverage_analysis.coverage_analysis_data_path, 
                'coverage_analysis_simulation_report.pdf'
            )
            print(f"Attempting to download PDF from path: {pdf_path}")

            if not os.path.exists(pdf_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'PDF file not found'
                }, status=404)

            try:
                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(
                        pdf_file.read(), 
                        content_type='application/pdf'
                    )
                    response['Content-Disposition'] = f'attachment; filename="coverage_analysis_simulation_report.pdf"'
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

