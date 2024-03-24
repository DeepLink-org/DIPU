// Copyright (c) 2023, DeepLink.
#pragma once

#include <ATen/TensorUtils.h>
#include <ATen/core/Generator.h>
#include <c10/core/Device.h>
#include <c10/core/GeneratorImpl.h>

namespace dipu {
class DIPUGeneratorImpl : public c10::GeneratorImpl {
 public:
  // Constructors
  explicit DIPUGeneratorImpl(at::DeviceIndex device_index = -1);
  ~DIPUGeneratorImpl() override = default;

  std::shared_ptr<DIPUGeneratorImpl> clone() const;
  void set_current_seed(uint64_t seed) override;
  uint64_t current_seed() const override;
  uint64_t seed() override;
  static at::DeviceType device_type();
  c10::intrusive_ptr<c10::TensorImpl> get_state() const override;

// todo:(fandaoyi) for 3rd lib to use dipu, need add dipu_cfg.h to contain
// DIPU_TORCH_VERSION.
// To temp support 3rd lib, The order of compatible versions written here does
// not match the order elsewhere. we will change to keep the order from
// oldest-compatiable to latest vesion.
#if DIPU_TORCH_VERSION == 20100 || DIPU_TORCH_VERSION == 20101
  void set_offset(uint64_t offset) override { offset_ = offset; }
  uint64_t get_offset() const override { return offset_; }

#else  // # temp solution, default use torch2.0.0
  virtual void set_offset(uint64_t offset) { offset_ = offset; }
  virtual uint64_t get_offset() const { return offset_; }

#endif

 protected:
  void set_state_flag(bool flag);
  virtual void update_state() const = 0;

  DIPUGeneratorImpl* clone_impl() const override;
  volatile uint64_t offset_;
  uint64_t seed_ = c10::default_rng_seed_val;
  mutable at::Tensor state_;
  mutable bool state_need_reset_;
};

at::Generator& getDefaultDIPUGenerator(at::DeviceIndex device_index = -1);
at::Generator createDIPUGenerator(at::DeviceIndex device_index = -1);

void manual_seed(at::DeviceIndex idx, uint64_t seed);
void seed(at::DeviceIndex idx);
uint64_t initial_seed(at::DeviceIndex idx);
at::Tensor get_rng_state(at::DeviceIndex idx);
void set_rng_state(at::DeviceIndex idx, at::Tensor state);

const at::Generator vendorMakeGenerator(at::DeviceIndex device_index = -1);

void releaseAllGenerator();

}  // namespace dipu
