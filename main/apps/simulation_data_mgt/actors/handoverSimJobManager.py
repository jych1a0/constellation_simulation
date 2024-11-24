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

        # 找到所有相关的未完成模拟作业
        sim_jobs = HandoverSimJob.objects.filter(
            f_handover_uid=handover,
            handoverSimJob_end_time__isnull=True
        )

        container_name = f"handoverSimulation_{handover_uid}"

        # 尝试停止和移除 Docker 容器
        try:
            # 使用 docker stop 命令终止容器
            subprocess.run(
                ['docker', 'stop', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # 设置超时时间
            )

            # 确保容器被移除
            subprocess.run(
                ['docker', 'rm', '-f', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
        except subprocess.TimeoutExpired:
            # 如果 docker stop 超时，强制移除容器
            subprocess.run(
                ['docker', 'rm', '-f', container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"停止 Docker 容器错误: {str(e)}")

        # 删除所有相关的未完成模拟作业
        sim_jobs.delete()

        # 更新 handover 状态
        handover.handover_status = "simulation fail"
        handover.save()

        print(f"已终止所有相关模拟作业 handover_uid: {handover_uid}")
        return True

    except Exception as e:
        print(f"终止模拟作业错误: {str(e)}")
        return False


def run_handover_simulation_async(handover_uid):
    sim_job = None
    try:
        # 获取 handover 实例
        handover = Handover.objects.get(handover_uid=handover_uid)

        # 创建新的 HandoverSimJob 记录
        sim_job = HandoverSimJob.objects.create(
            f_handover_uid=handover,
            handoverSimJob_start_time=timezone.now()
        )

        # 更新状态为执行中
        handover.handover_status = "processing"
        handover.save()

        # 定义输出目录，包含用户UID和handover_uid
        simulation_result_dir = os.path.join(
            'simulation_result', 'handover_simulation',
            str(handover.f_user_uid.user_uid),
            str(handover_uid)
        )
        print(f"Simulation result directory: {simulation_result_dir}")

        # 确保输出目录存在
        os.makedirs(simulation_result_dir, exist_ok=True)

        # 构建 docker run 命令
        container_name = f"handoverSimulation_{handover_uid}"

        # 如果 handover_parameter 是字典，转换为正确格式的字符串
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
            '-d',  # 在后台运行
            '--rm',  # 容器停止后自动移除
            f'--name={container_name}',
            '-v', f'{os.path.abspath(simulation_result_dir)}:/root/mercury/build/service/output',
            'handoversimulationimage',
            'bash', '-c', simulation_command
        ]

        print(f"Docker command: {' '.join(docker_command)}")

        # 执行 docker 命令
        simulation_process = subprocess.Popen(
            docker_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 等待容器启动并获取容器 ID
        stdout, stderr = simulation_process.communicate()

        if simulation_process.returncode != 0:
            raise Exception(f"无法启动 Docker 容器: {stderr.decode()}")

        # 获取容器的进程 ID
        container_info = subprocess.run(
            ['docker', 'inspect', '--format',
                '{{.State.Pid}}', container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if container_info.returncode == 0:
            container_pid = int(container_info.stdout.decode().strip())
            # 保存容器的进程 ID
            sim_job.handoverSimJob_process_id = container_pid
            sim_job.save()
        else:
            raise Exception("无法获取容器进程 ID")

        # 设置超时时间（例如：60分钟）
        timeout = 60 * 60  # 秒
        start_time = time.time()

        while True:
            # 检查是否超时
            if time.time() - start_time > timeout:
                print(f"模拟超时 handover_uid: {handover_uid}")
                terminate_handover_sim_job(handover_uid)
                return

            # 检查 Docker 容器是否存在
            container_check = subprocess.run(
                ['docker', 'ps', '-q', '-f', f'name={container_name}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            container_exists = bool(container_check.stdout.decode().strip())

            # 检查结果文件是否存在且有内容
            results_exist = os.path.exists(
                simulation_result_dir) and os.listdir(simulation_result_dir)

            if results_exist and not container_exists:
                # 如果有结果文件且容器不存在，标记为完成
                sim_job.handoverSimJob_end_time = timezone.now()
                sim_job.save()
                handover.handover_status = "completed"
                # 更新 handover_data_path
                handover.handover_data_path = simulation_result_dir
                handover.save()
                print(f"模拟成功完成，结果已保存 handover_uid: {handover_uid}")
                return

            # 如果容器已经停止但没有结果文件，判为失败
            if not container_exists and not results_exist:
                raise Exception("容器已停止但未找到结果文件，模拟失败")

            # 等待一段时间再检查
            time.sleep(10)

            # 重新从数据库获取 handover 状态
            handover.refresh_from_db()
            if handover.handover_status == "simulation fail":
                return

    except Exception as e:
        print(f"模拟错误: {str(e)}")
        if sim_job is not None:
            sim_job.delete()
        terminate_handover_sim_job(handover_uid)
        # 不需要再次更新 handover 状态，terminate_handover_sim_job 已经处理


class handoverSimJobManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def run_handover_sim_job(request):
        if request.method == 'POST':
            try:
                # 解析 JSON 数据
                data = json.loads(request.body)

                # 获取必要的参数
                handover_uid = data.get('handover_uid')

                # 验证必要参数
                if not handover_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': '缺少 handover_uid 参数'
                    }, status=400)

                # 检查 handover 是否存在
                try:
                    handover = Handover.objects.get(handover_uid=handover_uid)
                except Handover.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': '找不到对应的 Handover'
                    }, status=404)

                # 检查是否有 handover_parameter
                if not handover.handover_parameter:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Handover 缺少参数 handover_parameter'
                    }, status=400)

                # 检查当前状态是否为执行中
                if handover.handover_status == "processing":
                    return JsonResponse({
                        'status': 'info',
                        'message': '模拟正在执行中，请稍后查询结果',
                        'data': {
                            'handover_uid': str(handover_uid),
                            'handover_status': handover.handover_status
                        }
                    })

                # 检查是否有正在执行的模拟作业
                active_sim_job = HandoverSimJob.objects.filter(
                    f_handover_uid=handover,
                    handoverSimJob_end_time__isnull=True
                ).first()

                if active_sim_job:
                    return JsonResponse({
                        'status': 'info',
                        'message': '已存在正在执行的模拟作业',
                        'data': {
                            'handoverSimJob_uid': str(active_sim_job.handoverSimJob_uid),
                            'handover_status': handover.handover_status
                        }
                    })

                # 检查当前状态和数据路径
                if handover.handover_status == "completed":
                    if handover.handover_data_path and os.path.exists(handover.handover_data_path):
                        return JsonResponse({
                            'status': 'success',
                            'message': '模拟已经执行完成，结果可供使用',
                            'data': {
                                'handover_uid': str(handover_uid),
                                'handover_status': handover.handover_status,
                                'handover_data_path': handover.handover_data_path
                            }
                        })
                    else:
                        # 如果状态是 completed 但找不到数据，设置状态为 simulation fail 并继续
                        handover.handover_status = "simulation fail"
                        handover.save()

                # 在新的线程中执行模拟
                simulation_thread = threading.Thread(
                    target=run_handover_simulation_async,
                    args=(handover_uid,)
                )
                simulation_thread.start()

                # 立即返回响应
                return JsonResponse({
                    'status': 'success',
                    'message': '模拟作业已成功启动',
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
                    'message': '无效的 JSON 数据'
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
            # 解析請求數據
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