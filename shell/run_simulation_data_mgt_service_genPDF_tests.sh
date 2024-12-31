#!/usr/bin/env bash
set -e  # 遇到錯誤即停止

# echo "=== Running handoverSimJobManager_genPDF tests ==="
# python main/apps/simulation_data_mgt/tests/service/genPDF/test_coverageSimJobManager_genPDF.py

echo "=== Running test_connectedDurationSimJobManager_genPDF tests ==="
python main/apps/simulation_data_mgt/tests/service/genPDF/test_connectedDurationSimJobManager_genPDF.py