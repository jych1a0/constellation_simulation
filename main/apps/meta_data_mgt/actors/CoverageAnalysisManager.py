from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.apps.meta_data_mgt.models.UserModel import User
from main.apps.meta_data_mgt.models.CoverageAnalysisModel import CoverageAnalysis
from main.utils.logger import log_trigger, log_writer
from django.views.decorators.csrf import csrf_exempt
import os
import threading
class CoverageAnalysisManager:
    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def create_coverage_analysis(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                coverage_analysis_name = data.get('coverage_analysis_name')
                coverage_analysis_parameter = data.get('coverage_analysis_parameter')
                f_user_uid = data.get('f_user_uid')

                if not all([coverage_analysis_name, coverage_analysis_parameter, f_user_uid]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required parameters'
                    }, status=400)

                existing_coverage = CoverageAnalysis.objects.filter(
                    coverage_analysis_parameter=coverage_analysis_parameter,
                    f_user_uid_id=f_user_uid
                ).first()

                if existing_coverage:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage analysis with the same parameters already exists',
                        'existing_coverage': {
                            'id': existing_coverage.id,
                            'coverage_uid': str(existing_coverage.coverage_analysis_uid),
                            'coverage_name': existing_coverage.coverage_analysis_name,
                            'coverage_status': existing_coverage.coverage_analysis_status,
                            'coverage_parameter': existing_coverage.coverage_analysis_parameter,
                            'coverage_data_path': existing_coverage.coverage_analysis_data_path
                        }
                    }, status=400)

                coverage = CoverageAnalysis.objects.create(
                    coverage_analysis_name=coverage_analysis_name,
                    coverage_analysis_parameter=coverage_analysis_parameter,
                    coverage_analysis_status="None",
                    f_user_uid_id=f_user_uid
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Coverage analysis created successfully',
                    'data': {
                        'id': coverage.id,
                        'coverage_analysis_uid': str(coverage.coverage_analysis_uid),
                        'coverage_analysis_name': coverage.coverage_analysis_name,
                        'coverage_analysis_status': coverage.coverage_analysis_status,
                        'coverage_analysis_parameter': coverage.coverage_analysis_parameter,
                        'coverage_analysis_data_path': coverage.coverage_analysis_data_path
                    }
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def query_coverage_analysis_by_user(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                user_uid = data.get('user_uid')

                if not user_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing user_uid parameter'
                    }, status=400)

                try:
                    user = User.objects.get(user_uid=user_uid)
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'User not found'
                    }, status=404)

                coverages = CoverageAnalysis.objects.filter(f_user_uid=user_uid)

                coverage_analysis_list = []
                for coverage in coverages:
                    coverage_analysis_list.append({
                        'id': coverage.id,
                        'coverage_analysis_uid': str(coverage.coverage_analysis_uid),  # 改為 coverage_analysis_uid
                        'coverage_analysis_name': coverage.coverage_analysis_name,  # 改為 coverage_analysis_name
                        'coverage_analysis_status': coverage.coverage_analysis_status,  # 改為 coverage_analysis_status
                        'coverage_analysis_parameter': coverage.coverage_analysis_parameter,  # 改為 coverage_analysis_parameter
                        'coverage_analysis_data_path': coverage.coverage_analysis_data_path,  # 改為 coverage_analysis_data_path
                        'coverage_analysis_simulation_result': coverage.coverage_analysis_simulation_result,  # 改為 coverage_analysis_simulation_result
                        'coverage_analysis_create_time': coverage.coverage_analysis_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if coverage.coverage_analysis_create_time else None,  # 改為 coverage_analysis_create_time
                        'coverage_analysis_update_time': coverage.coverage_analysis_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if coverage.coverage_analysis_update_time else None  # 改為 coverage_analysis_update_time
                    })

                return JsonResponse({
                    'status': 'success',
                    'message': 'Coverage analysis data retrieved successfully',
                    'data': {
                        'user_uid': str(user.user_uid),
                        'user_name': user.user_name,
                        'coverages_analysis': coverage_analysis_list
                    }
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def delete_coverage_analysis(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                coverage_analysis_uid = data.get('coverage_analysis_uid')

                if not coverage_analysis_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing coverage_analysis_uid parameter'
                    }, status=400)

                try:
                    coverage = CoverageAnalysis.objects.get(coverage_analysis_uid=coverage_analysis_uid)
                except CoverageAnalysis.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage analysis not found'
                    }, status=404)

                deleted_coverage_info = {
                    'id': coverage.id,
                    'coverage_analysis_uid': str(coverage.coverage_analysis_uid),
                    'coverage_analysis_name': coverage.coverage_analysis_name,
                    'coverage_analysis_status': coverage.coverage_analysis_status,
                    'coverage_analysis_parameter': coverage.coverage_analysis_parameter,
                    'coverage_analysis_create_time': coverage.coverage_analysis_create_time.strftime('%Y-%m-%dT%H:%M:%SZ') if coverage.coverage_analysis_create_time else None,
                    'coverage_analysis_update_time': coverage.coverage_analysis_update_time.strftime('%Y-%m-%dT%H:%M:%SZ') if coverage.coverage_analysis_update_time else None
                }

                coverage.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Coverage analysis deleted successfully',
                    'data': deleted_coverage_info
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

    @log_trigger('INFO')
    @require_http_methods(["POST"])
    @csrf_exempt
    def update_coverage_analysis(request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                coverage_analysis_uid = data.get('coverage_analysis_uid')

                if not coverage_analysis_uid:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing coverage_analysis_uid parameter'
                    }, status=400)

                if 'coverage_analysis_parameter' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage parameter cannot be modified'
                    }, status=400)

                try:
                    coverage = CoverageAnalysis.objects.get(coverage_analysis_uid=coverage_analysis_uid)
                except CoverageAnalysis.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Coverage analysis not found'
                    }, status=404)

                has_changes = False

                if 'coverage_name' in data and data['coverage_analysis_name'] != coverage.coverage_analysis_name:
                    has_changes = True

                if 'coverage_status' in data and data['coverage_analysis_status'] != coverage.coverage_analysis_status:
                    has_changes = True

                if not has_changes:
                    return JsonResponse({
                        'status': 'info',
                        'message': 'No changes detected. Data remains the same.',
                        'data': {
                            'id': coverage.id,
                            'coverage_analysis_uid': str(coverage.coverage_analysis_uid),
                            'coverage_analysis_name': coverage.coverage_analysis_name,
                            'coverage_analysis_status': coverage.coverage_analysis_status,
                            'coverage_analysis_parameter': coverage.coverage_analysis_parameter,
                            'coverage_analysis_data_path': coverage.coverage_analysis_data_path,
                            'coverage_analysis_create_time': coverage.coverage_analysis_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'coverage_analysis_update_time': coverage.coverage_analysis_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        }
                    })

                if 'coverage_analysis_name' in data:
                    coverage.coverage_analysis_name = data['coverage_analysis_name']

                if 'coverage_analysis_status' in data:
                    coverage.coverage_analysis_status = data['coverage_analysis_status']

                coverage.save()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Coverage analysis updated successfully',
                    'data': {
                        'id': coverage.id,
                        'coverage_analysis_uid': str(coverage.coverage_analysis_uid),
                        'coverage_analysis_name': coverage.coverage_analysis_name,
                        'coverage_analysis_status': coverage.coverage_analysis_status,
                        'coverage_analysis_parameter': coverage.coverage_analysis_parameter,
                        'coverage_analysis_data_path': coverage.coverage_analysis_data_path,
                        'coverage_analysis_create_time': coverage.coverage_analysis_create_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'coverage_analysis_update_time': coverage.coverage_analysis_update_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                })

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
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
