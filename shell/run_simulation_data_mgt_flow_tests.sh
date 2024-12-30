#!/usr/bin/env bash
set -e  # 遇到錯誤即停止

# echo "=== Running handoverSimJobManager_flow tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_handoverSimJobManager_flow.py

# echo "=== Running coverageSimJobManager_flow tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_coverageSimJobManager_flow.py

echo "=== Running phaseSimJobManager tests ==="
python main/apps/simulation_data_mgt/tests/flow/test_phaseSimJobManager_flow.py

# echo "=== Running connectedDurationSimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_connectedDurationSimJobManager_flow.py

# echo "=== Running constellationStrategySimJobManager tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_constellationStrategySimJobManager_flow.py