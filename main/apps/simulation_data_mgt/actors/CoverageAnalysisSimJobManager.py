from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.CoverageAnalysisModel import CoverageAnalysis
from main.apps.simulation_data_mgt.models.CoverageAnalysisSimJobModel import CoverageAnalysisSimJob
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
import glob 

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

        # 建立結果目錄
        simulation_result_dir = os.path.join(
            'simulation_result', 'coverage_analysis_simulation',
            str(coverage_analysis.f_user_uid.user_uid),
            str(coverage_analysis_uid)
        )
        os.makedirs(simulation_result_dir, exist_ok=True)
        print(f"Simulation result directory: {simulation_result_dir}")

        # 準備 Docker 參數
        container_name = f"coverageAnalysisSimulation_{coverage_analysis_uid}"

        # 準備模擬參數
        if isinstance(coverage_analysis.coverage_analysis_parameter, dict):
            json_params = json.dumps(coverage_analysis.coverage_analysis_parameter)
        else:
            try:
                json_params = json.dumps(json.loads(coverage_analysis.coverage_analysis_parameter))
            except json.JSONDecodeError:
                json_params = coverage_analysis.coverage_analysis_parameter

        # 修改 Docker 命令，加入複製檔案的指令
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

        print(f"Executing Docker command: {' '.join(docker_cmd)}")

        # 執行 Docker 命令
        try:
            process = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 獲取容器 PID
            container_info = subprocess.run(
                ['docker', 'inspect', '--format', '{{.State.Pid}}', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if container_info.returncode == 0:
                container_pid = int(container_info.stdout.strip())
                sim_job.coverageAnalysisSimJob_process_id = container_pid
                sim_job.save()

            # 設置超時時間
            timeout = 60 * 60  # 1小時
            start_time = time.time()

            while True:
                if time.time() - start_time > timeout:
                    print(f"Simulation timeout for coverage_analysis_uid: {coverage_analysis_uid}")
                    terminate_coverage_analysis_sim_job(coverage_analysis_uid)
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
                
                # 在檢查結果時添加文件複製邏輯
                if results_exist and not container_exists:
                    try:
                        # 確保目標目錄存在
                        target_dir = os.path.join(
                            '/root/241124_Constellation_Simulation/constellation_simulation/simulation_result',
                            'coverage_analysis_simulation',
                            str(coverage_analysis.f_user_uid.user_uid),
                            str(coverage_analysis_uid)
                        )

                        # 檢查源路徑和目標路徑是否相同
                        abs_simulation_result_dir = os.path.abspath(simulation_result_dir)
                        abs_target_dir = os.path.abspath(target_dir)

                        if abs_simulation_result_dir != abs_target_dir:
                            # 如果路徑不同，則創建目標目錄並複製文件
                            os.makedirs(target_dir, exist_ok=True)

                            # 複製所有結果檔案到目標目錄
                            for file in os.listdir(simulation_result_dir):
                                if file.endswith('.csv'):
                                    source_file = os.path.join(simulation_result_dir, file)
                                    target_file = os.path.join(target_dir, file)
                                    if os.path.abspath(source_file) != os.path.abspath(target_file):
                                        shutil.copy2(source_file, target_file)
                        
                        # 更新資料庫中的路徑（使用絕對路徑）
                        coverage_analysis.coverage_analysis_status = "completed"
                        # coverage_analysis.coverage_analysis_data_path = abs_target_dir
                        coverage_analysis.save()

                        sim_job.coverageAnalysisSimJob_end_time = timezone.now()
                        sim_job.save()

                        print(f"Simulation completed and results stored in: {abs_target_dir}")
                        return

                    except Exception as e:
                        print(f"Error handling results: {str(e)}")
                        raise

        except subprocess.TimeoutExpired:
            print(f"Docker command timeout for coverage_analysis_uid: {coverage_analysis_uid}")
            terminate_coverage_analysis_sim_job(coverage_analysis_uid)
        except Exception as e:
            print(f"Docker execution error: {str(e)}")
            raise

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

            full_path = os.path.join('./simulation_result', coverage_analysis.coverage_analysis_data_path)
            print(full_path)
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

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def test_post(request):
        try:
            # 解析請求數據
            data = json.loads(request.body)
            
            # 準備 Docker 命令參數
            json_params = json.dumps({
                "constellation": data.get("constellation"),
                "minLatitude": data.get("minLatitude"),
                "maxLatitude": data.get("maxLatitude"),
                "leastSatCount": data.get("leastSatCount")
            })

            # 建立目標目錄（如果不存在）
            host_output_dir = "/root/241124_Constellation_Simulation/constellation_simulation/simulation_result/coverage_analysis"
            os.makedirs(host_output_dir, exist_ok=True)

            # 準備 Docker 運行命令
            container_name = "coverage_analysis_simulation_container"
            docker_cmd = f"""
            docker run \
                --oom-kill-disable=true \
                -m 28g \
                --rm \
                -v {host_output_dir}:/host_output \
                --name={container_name} \
                coverage_analysis_simulation:latest \
                bash -c '/root/mercury/shell/simulation_script.sh '"'"'{json_params}'"'"' && cp /root/mercury/build/service/*.csv /host_output/'
            """

            # 執行 Docker 命令，設置較長的超時時間（例如 3600 秒 = 1小時）
            try:
                result = subprocess.run(
                    docker_cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=3600  # 設置超時時間為1小時
                )
                
                # 輸出詳細的執行結果，用於調試
                print(f"Command output: {result.stdout}")
                print(f"Command errors: {result.stderr}")
                print(f"Return code: {result.returncode}")

                if result.returncode != 0:
                    raise Exception(f"Docker 執行失敗: {result.stderr}")

            except subprocess.TimeoutExpired:
                raise Exception("Docker 命令執行超時（超過1小時）")
            except subprocess.CalledProcessError as e:
                raise Exception(f"Docker 命令執行失敗: {str(e)}")

            # 檢查輸出文件是否存在
            csv_files = glob.glob(os.path.join(host_output_dir, "*.csv"))
            if not csv_files:
                raise Exception("沒有找到輸出的 CSV 文件")

            # 構建回應
            response_data = {
                "status": "success",
                "message": "模擬完成並已複製結果檔案",
                "output_directory": host_output_dir,
                "files_generated": [os.path.basename(f) for f in csv_files]
            }

            return JsonResponse(response_data)

        except json.JSONDecodeError:
            error_response = {
                "status": "error",
                "message": "無效的 JSON 格式"
            }
            return JsonResponse(error_response, status=400)
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e)
            }
            return JsonResponse(error_response, status=500)
