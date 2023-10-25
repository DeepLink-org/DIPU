#!/usr/bin/env bash

DIOPI_IMPL=${3:-droplet}
DIPU_DEVICE=${2:-droplet}

function build_dipu_py() {
    echo "building dipu_py:$(pwd)"
    echo "building dipu_py PYTORCH_DIR: ${PYTORCH_DIR}"
    export CMAKE_BUILD_TYPE=debug
    export _GLIBCXX_USE_CXX11_ABI=1
    export MAX_JOBS=12
    # PYTORCH_INSTALL_DIR is /you_pytorch/torch20/pytorch/torch
    # python  setup.py build_clib 2>&1 | tee ./build1.log
    python setup.py build_ext 2>&1 | tee ./build1.log
    mv build/python_ext/torch_dipu/_C.cpython*.so torch_dipu
}

function config_dipu_droplet_cmake() {
    mkdir -p build && cd ./build && rm -rf ./*
    echo "config_dipu_nv_cmake PYTORCH_DIR: ${PYTORCH_DIR}"
    echo "config_dipu_nv_cmake PYTHON_INCLUDE_DIR: ${PYTHON_INCLUDE_DIR}"
    cmake ../  -DCMAKE_BUILD_TYPE=Debug \
     -DDEVICE=${DIPU_DEVICE} -DPYTORCH_DIR=${PYTORCH_DIR} \
     -DPYTHON_INCLUDE_DIR=${PYTHON_INCLUDE_DIR}
      # -DCMAKE_C_FLAGS_DEBUG="-g -O0" \
      # -DCMAKE_CXX_FLAGS_DEBUG="-g -O0"
    cd ../
}

function autogen_diopi_wrapper() {
    python scripts/autogen_diopi_wrapper/autogen_diopi_wrapper.py \
        --config scripts/autogen_diopi_wrapper/diopi_functions.yaml \
        --out torch_dipu/csrc_dipu/aten/ops/AutoGenedKernels.cpp \
        --use_diopi_adapter False
        # --diopi_adapter_header torch_dipu/csrc_dipu/vendor/droplet/diopi_adapter.hpp
}

function build_diopi_lib() {
    echo "开始编译DIOPI..."
    cd third_party/DIOPI/
    git checkout .
    cd impl
    which cmake
    sh scripts/build_impl.sh clean
    #TODO: need to change if droplet decides to be exposed as shared lib
    sh scripts/build_impl.sh droplet || exit -1

    cd ../../..
}

function build_dipu_lib() { 
    echo "building dipu_lib:$(pwd)"
    echo  "DIOPI_ROOT:${DIOPI_ROOT}"
    echo  "PYTORCH_DIR:${PYTORCH_DIR}"
    echo  "PYTHON_INCLUDE_DIR:${PYTHON_INCLUDE_DIR}"
    export LIBRARY_PATH=$DIOPI_ROOT:$LIBRARY_PATH;
    config_dipu_droplet_cmake 2>&1 | tee ./cmake_droplet.log
    cd build && make -j8  2>&1 | tee ./build.log &&  cd ..
    mv ./build/torch_dipu/csrc_dipu/libtorch_dipu.so   ./torch_dipu
    mv ./build/torch_dipu/csrc_dipu/libtorch_dipu_python.so   ./torch_dipu
}

case $1 in
    build_diopi)
        (
            build_diopi_lib
        ) \
        || exit -1;;
    build_dipu)
        (
            bash scripts/ci/ci_build_third_party.sh
            build_diopi_lib
            autogen_diopi_wrapper
            build_dipu_lib
            build_dipu_py
        ) \
        || exit -1;;
    build_dipu_only)
        (
            bash scripts/ci/ci_build_third_party.sh
            autogen_diopi_wrapper
            build_dipu_lib
            build_dipu_py
        ) \
        || exit -1;;
    *)
        echo -e "[ERROR] Incorrect option:" $1;
esac
exit 0
