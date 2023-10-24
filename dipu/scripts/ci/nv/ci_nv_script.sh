# !/bin/bash
set -e
echo "pwd: $(pwd)"

function build_dipu_py() {
    echo "building dipu_py:$(pwd)"
    export CMAKE_BUILD_TYPE=Release
    export MAX_JOBS=12
    python setup.py build_ext 2>&1 | tee ./setup.log
    mv build/python_ext/torch_dipu/_C.cpython-*.so torch_dipu
}

function config_dipu_nv_cmake() {
    # export NCCL_ROOT="you nccl path should exist"

    mkdir -p build && cd ./build && rm -rf ./*
    cmake ../  -DCMAKE_BUILD_TYPE=Release \
        -DDEVICE=cuda \
        -DENABLE_COVERAGE=${USE_COVERAGE}
    cd ../
}

function autogen_diopi_wrapper() {
    python scripts/autogen_diopi_wrapper/autogen_diopi_wrapper.py                   \
        --config scripts/autogen_diopi_wrapper/diopi_functions.yaml                 \
        --out torch_dipu/csrc_dipu/aten/ops/AutoGenedKernels.cpp                    \
        --use_diopi_adapter False                                                   \
        --autocompare False                                                         \
        --print_func_call_info True                                                 \
        --print_op_arg True                                                         \
        --fun_config_dict '{"current_device": "cuda"}'
}

function build_diopi_lib() {
    cd third_party/DIOPI/
    cd impl
    which cmake
    sh scripts/build_impl.sh clean
    sh scripts/build_impl.sh torch || exit -1

    cd ../../..
    unset Torch_DIR
}

function build_dipu_lib() {
    echo "building dipu_lib:$(pwd)"
    echo  "DIOPI_ROOT:${DIOPI_ROOT}"
    export DIOPI_BUILD_TESTRT=1
    export LIBRARY_PATH=$DIOPI_ROOT:$LIBRARY_PATH;
    config_dipu_nv_cmake 2>&1 | tee ./cmake_nv.log
    cd build && make -j8  2>&1 | tee ./build.log &&  cd ..
    mv ./build/torch_dipu/csrc_dipu/libtorch_dipu.so   ./torch_dipu
    mv ./build/torch_dipu/csrc_dipu/libtorch_dipu_python.so   ./torch_dipu
}

case $1 in
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
