#!/usr/bin/env bash
set -e  # 遇到錯誤即停止

# echo "=== Running handoverSimJobManager_flow tests ==="
# python main/apps/simulation_data_mgt/tests/flow/test_handoverSimJobManager_flow.py

echo "=== Running handoverSimJobManager_flow tests ==="
python main/apps/simulation_data_mgt/tests/flow/test_coverageSimJobManager_flow.py
