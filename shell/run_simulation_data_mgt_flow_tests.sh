#!/usr/bin/env bash
set -e  # 遇到錯誤即停止

echo "=== Running handover_sim_job_flow tests ==="
python manage.py test main.apps.simulation_data_mgt.tests.flow.test_handover_sim_job_flow

# echo "=== Running coverage_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_coverage_sim_job_flow

# echo "=== Running connectedDuration_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_connectedDuration_sim_job_flow

# echo "=== Running phase_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_phase_sim_job_flow

# echo "=== Running constellationStrategy_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_constellationStrategy_sim_job_flow

# echo "=== Running islHopping_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_islHopping_sim_job_flow

# echo "=== Running modifyRegenRouting_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_modifyRegenRouting_sim_job_flow

# echo "=== Running oneToMulti_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_oneToMulti_sim_job_flow

# echo "=== Running multiToMulti_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_multiToMulti_sim_job_flow

# echo "=== Running saveErRouting_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_saveErRouting_sim_job_flow

# echo "=== Running endToEndRouting_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_endToEndRouting_sim_job_flow

# echo "=== Running singleBeam_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_singleBeam_sim_job_flow

# echo "=== Running gso_sim_job_flow tests ==="
# python manage.py test main.apps.simulation_data_mgt.tests.flow.test_gso_sim_job_flow

echo "All simulation_data_mgt sim_job flow tests executed successfully!"
