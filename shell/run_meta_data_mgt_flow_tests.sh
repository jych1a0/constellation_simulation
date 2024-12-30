#!/usr/bin/env bash
set -e  # 遇到錯誤即停止

echo "=== Running coverage_flow tests ==="
python manage.py test main.apps.meta_data_mgt.tests.flow.test_coverage_flow

# echo "=== Running connectedDuration_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_connectedDuration_flow

# echo "=== Running constellationStrategy_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_constellationStrategy_flow

# echo "=== Running endToEndRouting_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_endToEndRouting_flow

# echo "=== Running gso_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_gso_flow

# echo "=== Running islHopping_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_islHopping_flow

# echo "=== Running modifyRegenRouting_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_modifyRegenRouting_flow

# echo "=== Running multiToMulti_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_multiToMulti_flow

# echo "=== Running oneToMulti_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_oneToMulti_flow

# echo "=== Running phase_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_phase_flow

# echo "=== Running saveErRouting_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_saveErRouting_flow

# echo "=== Running singleBeam_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_singleBeam_flow

# echo "=== Running handover_flow tests ==="
# python manage.py test main.apps.meta_data_mgt.tests.flow.test_handover_flow

echo "All flow tests executed successfully!"
