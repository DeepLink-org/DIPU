#pragma once
#include <cstdio>

#include "pccl.h"
#include <tang_runtime.h>

#include <c10/util/Exception.h>

#include "csrc_dipu/vendor/droplet/pccl.h"
#include <csrc_dipu/common.h>

namespace dipu {

#define DIPU_CALLDROPLET(Expr)                                              \
  {                                                                         \
    tangError_t ret = Expr;                                                 \
    if (ret != tangSuccess) {                                               \
      printf("call a tangrt function (%s) failed. return code=%d\n", #Expr, \
             ret);                                                          \
      fflush(stdout);                                                       \
      throw std::runtime_error("dipu device error");                        \
    }                                                                       \
  }

using deviceStream_t = tangStream_t;
#define deviceDefaultStreamLiteral nullptr
using deviceEvent_t = tangEvent_t;
using deviceHandle_t = tangContext_t*;
using diclComm_t = pcclComm_t;
using commUniqueId = pcclUniqueId;

}  // namespace dipu
