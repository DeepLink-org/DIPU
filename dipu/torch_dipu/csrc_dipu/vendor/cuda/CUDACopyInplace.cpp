// Copyright (c) 2023, DeepLink.

#include <c10/util/Exception.h>

#include <csrc_dipu/aten/ops/DIPUCopy.hpp>
#include <csrc_dipu/common.h>
#include <csrc_dipu/diopirt/diopirt_impl.h>
#include <csrc_dipu/runtime/core/DIPUStream.h>

namespace dipu {

using dipu::native::dipu_wrap_diopi_copy_inp;
class CUDACopyInplace : public DIPUCopyInplace<true, false> {
 public:
  CUDACopyInplace() = default;
  ~CUDACopyInplace() = default;

  // diopi-cuda copy use aten, so it can handle between-device case.
  void copyNodirectBetweenDevices(at::Tensor& dst, const at::Tensor& src,
                                  bool non_blocking,
                                  CopyParamsInfo& info) override {
    dipu_wrap_diopi_copy_inp(dst, src, non_blocking);
  }
};

// vendor which has incomplete diopiCopy implementation need write a subclass
// and override copyNodirectOnDevice like this.
/*
class VendorCopyInplcae: public DIPUCopyInplace<true, false> {
public:
  VendorCopyInplcae() = default;
  ~VendorCopyInplcae() = default;
  void copyNodirectOnDevice(at::Tensor& dst, const at::Tensor& src,
                            bool non_blocking, CopyParamsInfo& info) override {
    check_if_diopi_copy_can_handle: {
      dipu_wrap_diopi_copy_inp(self, src, non_blocking);
      or
      DIPUCopyInplace::copyNodirectOnDevice(XXX);
    } else {
      doCpuRelayCopy(...);
    }
  }
};
*/

static CUDACopyInplace cuda_copy_inplace;
static int32_t cuda_init = []() {
  setDipuCopyInstance(&cuda_copy_inplace);
  return 1;
}();

}  // namespace dipu
