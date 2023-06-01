#include "RegisterDIPU.hpp"
#include <iostream>
namespace at {

void dipu_fallback(const c10::OperatorHandle& op, DispatchKeySet dispatch_keys,
    torch::jit::Stack* stack) {
  const auto name = c10::toString(op.operator_name());
  // std::cout << "fallback to cpu, name=" << c10::toString(op.operator_name()) << std::endl;
  at::native::cpu_fallback(op, stack);
}


namespace {
  // dipu native ops
  at::Tensor wrapper_empty_memory_format(at::IntArrayRef size, c10::optional<at::ScalarType> dtype_opt,
        c10::optional<at::Layout> layout_opt,
        c10::optional<at::Device> device_opt, c10::optional<bool> pin_memory_opt,
        c10::optional<at::MemoryFormat> memory_format_opt) {
    const DeviceGuard device_guard(device_or_default(device_opt));
    return dnative::empty(size, dtype_opt, layout_opt, device_opt, pin_memory_opt, memory_format_opt);
  }

  at::Tensor wrapper_empty_strided(at::IntArrayRef size, at::IntArrayRef stride, c10::optional<at::ScalarType> dtype_opt,
      c10::optional<at::Layout> layout_opt, c10::optional<at::Device> device_opt, c10::optional<bool> pin_memory_opt) {
    const DeviceGuard device_guard(device_or_default(device_opt));
    return dnative::empty_strided(size, stride, dtype_opt, layout_opt, device_opt, pin_memory_opt);
  }

  at::Tensor& wrapper_copy_(at::Tensor& self, const at::Tensor& src, bool non_blocking) {
    return dnative::copy_(self, src, non_blocking);
  }

  at::Tensor wrapper_conv2d_(const at::Tensor& input, const at::Tensor& weight, const c10::optional<at::Tensor>& bias, at::IntArrayRef stride, at::IntArrayRef padding, at::IntArrayRef dilation, int64_t groups) {
    std::cout << "zzzz wrapper_conv2d_" << std::endl;
    int64_t batch_size = input.size(0);
    int64_t height = input.size(2);
    int64_t width = input.size(3);
    int64_t out_channel = weight.size(0);
    auto kernel_size = weight.sizes().slice(2);
    int64_t out_height = (height + 2 * padding[0] - dilation[0] * (kernel_size[0] - 1) - 1) / stride[0] + 1;
    int64_t out_width = (width + 2 * padding[1] - dilation[1] * (kernel_size[1] - 1) - 1) / stride[1] + 1;
    c10::SmallVector<int64_t, 8> output_size = {batch_size, out_channel, out_height, out_width};
    at::Tensor out = at::empty(output_size, input.options());
    return out;
  }

  at::Tensor wrapper_DIPU___reshape_alias(const at::Tensor & self, c10::SymIntArrayRef size, c10::SymIntArrayRef stride) {
    return at::native::_reshape_alias(self, C10_AS_INTARRAYREF_SLOW(size), C10_AS_INTARRAYREF_SLOW(stride));
  }

  // only used by cpu_fallback.
  at::Tensor wrapper_DIPU___copy_from_and_resize(const at::Tensor & self, const at::Tensor& dst) {
    dst.resize_as_(self).copy_(self);
    return dst;
  }

  const at::Tensor& wrapper_resize_(const at::Tensor& self, at::IntArrayRef size, c10::optional<at::MemoryFormat> memory_format) {
    // add guard for device switch.
    return dnative::resize_(self, size, memory_format);
  }

  at::Tensor wrapper_DIPU__as_strided(const at::Tensor & self, c10::SymIntArrayRef size, c10::SymIntArrayRef stride, c10::optional<c10::SymInt> storage_offset) {
      // No device check
    // DeviceGuard omitted
    return at::native::as_strided_tensorimpl(self, C10_AS_INTARRAYREF_SLOW(size), C10_AS_INTARRAYREF_SLOW(stride), storage_offset.has_value() ? c10::make_optional(storage_offset->expect_int()) : c10::nullopt);
  }

  at::Tensor wrapper_DIPU__view(const at::Tensor & self, c10::SymIntArrayRef size) {
    // No device check
    // DeviceGuard omitted
    return at::native::view(self, C10_AS_INTARRAYREF_SLOW(size));
  }

  at::Tensor wrapper_DIPU__view_as_real(const at::Tensor & self) {
    // DeviceGuard omitted
    return at::native::view_as_real(self);
  }

  at::Tensor wrapper_DIPU__view_as_complex(const at::Tensor & self) {
    // DeviceGuard omitted
    return at::native::view_as_complex(self);
  }

  at::Tensor & wrapper_DIPU__zero_(at::Tensor & self) {
    const OptionalDeviceGuard device_guard(device_of(self));
    return at::native::zero_(self);
  }

  at::Scalar wrapper_DIPU___local_scalar_dense(const at::Tensor & self) {
    const OptionalDeviceGuard device_guard(device_of(self));
    return dnative::_local_scalar_dense_dipu(self);
  }

}  // inner anonymous namespace


TORCH_LIBRARY_IMPL(_, DIPU_DEVICE_TYPE_MACRO, m) {
    m.fallback(torch::CppFunction::makeFromBoxedFunction<&dipu_fallback>());
}

TORCH_LIBRARY_IMPL(aten, DIPU_DEVICE_TYPE_MACRO, m) {
  // always registered
  m.impl("empty.memory_format", TORCH_FN(wrapper_empty_memory_format));
  m.impl("empty_strided", TORCH_FN(wrapper_empty_strided));
  m.impl("copy_",  TORCH_FN(wrapper_copy_));
  m.impl("_reshape_alias", TORCH_FN(wrapper_DIPU___reshape_alias));
  m.impl("_copy_from_and_resize", TORCH_FN(wrapper_DIPU___copy_from_and_resize));
  m.impl("resize_", TORCH_FN(wrapper_resize_));
  m.impl("as_strided", TORCH_FN(wrapper_DIPU__as_strided));
  m.impl("view", TORCH_FN(wrapper_DIPU__view));
  m.impl("view_as_real", TORCH_FN(wrapper_DIPU__view_as_real));
  m.impl("view_as_complex", TORCH_FN(wrapper_DIPU__view_as_complex));
  m.impl("zero_", TORCH_FN(wrapper_DIPU__zero_));
  m.impl("_local_scalar_dense", TORCH_FN(wrapper_DIPU___local_scalar_dense));

  //DIOPI_ATEN_FUNC("conv2d", ::diopiConvolution2d, wrapper_conv2d_);
}

TORCH_LIBRARY_IMPL(aten, DIPU_AUTOGRAD_DEVICE_TYPE_MACRO, m) {
    
    //  m.impl("conv2d", TORCH_FN(wrapper_conv2d_));
    //DIOPI_ATEN_FUNC("conv2d", ::diopiConvolution2d, dipu::native::dipu_conv2d_wrapper);
    
}

}  //end ns at
