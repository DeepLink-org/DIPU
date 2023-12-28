# ENV_NAME=dipu_poc

# edit your path
export CONDA_ROOT=/home/cse/miniconda3
export PYTORCH_DIR=/home/cse/src/pytorch
export DIPU_LOCAL_DIR=/path/to/dipu

export DIOPI_ROOT=${DIPU_LOCAL_DIR}/third_party/DIOPI/impl/lib
export DIPU_ROOT=${DIPU_LOCAL_DIR}/torch_dipu
export LD_LIBRARY_PATH=$DIPU_ROOT:$DIOPI_ROOT:$LD_LIBRARY_PATH
export PYTHONPATH=${CONDA_ROOT}/envs/dipu/lib/python3.8:${DIPU_LOCAL_DIR}:${PYTHONPATH}
export PATH=${PYTORCH_DIR}/build/bin:${CONDA_ROOT}/envs/dipu/bin:${CONDA_ROOT}/bin:${PATH}

# this is for mmcv
export VENDOR_INCLUDE_DIRS=/usr/include/tops
export DIOPI_PATH=${DIPU_LOCAL_DIR}/third_party/DIOPI/proto
export DIPU_PATH=${DIPU_ROOT}

export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1

# source activate $ENV_NAME
