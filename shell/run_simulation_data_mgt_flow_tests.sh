#!/usr/bin/env bash
set -e  # 遇到錯誤即停止

# echo "=== Running handoverSimJobManager_flow tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_handoverSimJobManager_flow.py

# echo "=== Running coverageSimJobManager_flow tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_coverageSimJobManager_flow.py

# echo "=== Running phaseSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_phaseSimJobManager_flow.py

# echo "=== Running connectedDurationSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_connectedDurationSimJobManager_flow.py

# echo "=== Running constellationStrategySimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_constellationStrategySimJobManager_flow.py

# echo "=== Running singleBeamSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_singleBeamSimJobManager_flow.py

# echo "=== Running modifyRegenRoutingSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_modifyRegenRoutingSimJobManager_flow.py

# echo "=== Running islHoppingSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_islHoppingSimJobManager_flow.py

# echo "=== Running oneToMultiSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_oneToMultiSimJobManager_flow.py

echo "=== Running multiToMultiSimJobManager tests ==="
python main/apps/simulation_data_mgt/tests/flow/test_multiToMultiSimJobManager_flow.py

# echo "=== Running saveErRoutingSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_saveErRoutingSimJobManager_flow.py

# echo "=== Running endToEndRoutingSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_endToEndRoutingSimJobManager_flow.py