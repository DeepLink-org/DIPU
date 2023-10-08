// Copyright (c) 2023, DeepLink.
#pragma once

#include <deque>
#include <mutex>
#include <torch/library.h>

namespace dipu {

bool get_force_fallback(const char* opname);

};  // namespace dipu

namespace at {

 void dipu_fallback(const c10::OperatorHandle& op, DispatchKeySet dispatch_keys,
    torch::jit::Stack* stack);

#define DIPU_REGISTER_LOG(x)                                     \
    {                                                            \
        static bool should_print = true;                         \
        const char* env = std::getenv("DIPU_DUMP_OP_ARGS");      \
        int env_value = (env != nullptr) ? std::atoi(env) : 0;   \
        if (should_print && env_value >= 0) {                    \
            std::cout << x;                                      \
            should_print = false;                                \
        }                                                        \
    }

// Temporarily not implement 'sub-dispatch from box' (from torch box func -> ourself unbox func)
// which described in design doc.
// because: 1. it need many add type trait code. 2. pytorch seems are sorting out infer and other pre/post code.
// so we shouldn't created a new preprocess logic?
//so just do a simple runtime cpu fallback to support diopi func loss
#define DIOPI_ATEN_FUNC(opname, diopiFunc, wapperFunc) do {                                                             \
    if ((reinterpret_cast<void*>(diopiFunc) != nullptr) && (!dipu::get_force_fallback(opname))) {                       \
        m.impl(opname, TORCH_FN(wapperFunc));                                                                           \
    }  else {                                                                                                           \
        if ((reinterpret_cast<void*>(diopiFunc) == nullptr)) {                                                          \
            DIPU_REGISTER_LOG(#diopiFunc << " is not yet implemented, ");                                               \
        } else {                                                                                                        \
            DIPU_REGISTER_LOG("force fallback has been set, ");                                                         \
        }                                                                                                               \
        DIPU_REGISTER_LOG(opname << " will be fallback to cpu" << std::endl);                                           \
        m.impl(opname, torch::CppFunction::makeFromBoxedFunction<&dipu_fallback>());                                    \
    }                                                                                                                   \
} while (false);

#define DIOPI_ATEN_FUNC_CUSTOM_FALLBACK(opname, diopi_func, force_fallback, wapper_func, custom_fallback_func) do {     \
    if ((reinterpret_cast<void*>(diopi_func) != nullptr) && !(force_fallback || dipu::get_force_fallback(opname))) {    \
        m.impl(opname, TORCH_FN(wapper_func));                                                                          \
    }  else {                                                                                                           \
        if ((reinterpret_cast<void*>(diopi_func) == nullptr)) {                                                         \
            DIPU_REGISTER_LOG(#diopi_func << " is not yet implemented, ")  ;                                            \
        } else {                                                                                                        \
            DIPU_REGISTER_LOG("force fallback has been set, ");                                                         \
        }                                                                                                               \
        DIPU_REGISTER_LOG(opname << " will be fallback to cpu" << std::endl);                                           \
        m.impl(opname, TORCH_FN(custom_fallback_func));                                                                 \
    }                                                                                                                   \
} while (false);


class DIPUOpRegister {
public:
    typedef void (*OpRegFunPtr)(torch::Library&);
private:
    OpRegFunPtr fun_ptr_;
    torch::Library lib_;
    static std::deque<std::tuple<torch::Library*, OpRegFunPtr>> dipuOpRegisterList;
    static std::mutex mutex_;
public:
    DIPUOpRegister(OpRegFunPtr fun_ptr, const char* ns, c10::optional<c10::DispatchKey> key, const char* file, int line): lib_(torch::Library::IMPL, ns, key, file, line), fun_ptr_(fun_ptr) {
        const char* env = std::getenv("DIPU_IMMEDIATE_REGISTER_OP");
        if (env != nullptr && std::atoi(env) > 0) {
            fun_ptr_(lib_);
        } else {
            std::lock_guard<std::mutex> guard(mutex_);
            dipuOpRegisterList.push_back(std::make_tuple(&lib_, fun_ptr_));
        }
    }

    static void register_op();
};

} //end ns at

namespace {

#define DIPU_LIBRARY_IMPL(ns, k, m) _DIPU_LIBRARY_IMPL(ns, k, m, C10_UID)

#define _DIPU_LIBRARY_IMPL(ns, k, m, uid)                               \
  static void C10_CONCATENATE(                                          \
      DIPU_LIBRARY_IMPL_init_##ns##_##k##_, uid)(torch::Library&);      \
  static const ::at::DIPUOpRegister C10_CONCATENATE(                    \
      DIPU_LIBRARY_IMPL_static_init_##ns##_##k##_, uid)(                \
      c10::guts::if_constexpr<c10::impl::dispatch_key_allowlist_check(  \
          c10::DispatchKey::k)>(                                        \
          []() {                                                        \
           return &C10_CONCATENATE(                                     \
                DIPU_LIBRARY_IMPL_init_##ns##_##k##_, uid);             \
          },                                                            \
          []() { return [](torch::Library&) -> void {}; }),             \
      #ns,                                                              \
      c10::make_optional(c10::DispatchKey::k),                          \
      __FILE__,                                                         \
      __LINE__);                                                        \
  void C10_CONCATENATE(                                                 \
      DIPU_LIBRARY_IMPL_init_##ns##_##k##_, uid)(torch::Library & m)

} // namespace
