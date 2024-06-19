# !/bin/bash
set -exo pipefail

source tests/common.sh

function run_dipu_tests {
    # TODO: Add PyTorch tests
    # run_test tests/test_ops/archived/test_tensor_add.py
    python tests/python/individual_scripts/test_rt_ddp.py
}

if [ "$LOGFILE" != "" ]; then
  run_dipu_tests 2>&1 | tee $LOGFILE
else
  run_dipu_tests
fi
