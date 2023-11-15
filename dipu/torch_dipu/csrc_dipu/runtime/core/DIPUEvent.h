// Copyright (c) 2023, DeepLink.
#pragma once

#include "DIPUStream.h"
#include "DIPUGuard.h"
#include <csrc_dipu/runtime/devproxy/deviceproxy.h>
#include <cstdint>
#include <utility>


namespace dipu {
/*
* DIPUEvents are movable not copyable wrappers around DIPU's events.
* DIPUEvents are constructed lazily when first recorded.
*/
class DIPU_API DIPUEvent {
public:
  // Constructors
  // Default value for `flags` is specified below
  DIPUEvent() {}

  // add flags in future
  // DIPUEvent(unsigned int flags) : flags_{flags} {}

  // dipu do not support IpcEventHandle until now

  ~DIPUEvent() {
    try {
      if (isCreated()) {
        DIPUGuard guard(device_index_);
        devproxy::destroyEvent(event_);
      }
    } catch (...) { /* No throw */ }
  }

  DIPUEvent(const DIPUEvent&) = delete;
  DIPUEvent& operator=(const DIPUEvent&) = delete;

  DIPUEvent(DIPUEvent&& other) { moveHelper(std::move(other)); }
  DIPUEvent& operator=(DIPUEvent&& other) {
    moveHelper(std::move(other));
    return *this;
  }

  operator deviceEvent_t() const { return rawevent(); }

  // aclrtEvent do not support Less than operator until now

  c10::optional<at::Device> device() const {
    if (isCreated()) {
      return at::Device(dipu::DIPU_DEVICE_TYPE, device_index_);
    } else {
      return {};
    }
  }

  bool isCreated() const { return event_ != nullptr; }
  c10::DeviceIndex device_index() const {return device_index_;}
  deviceEvent_t rawevent() const { return event_; }

  bool query() const {
    if (!isCreated()) {
      return true;
    }
    DIPUGuard guard(device_index_);
    auto currStatus  = devproxy::getEventStatus(event_);
    if (currStatus == devapis::EventStatus::READY) {
      return true;
    }
    return false;
  }

  void record() { record(getCurrentDIPUStream()); }

  void recordOnce(const DIPUStream& stream) {
    if (!was_recorded_) record(stream);
  }

  void record(const DIPUStream& stream) {
    if (!isCreated()) {
      createEvent(stream.device_index());
    }
    TORCH_CHECK(device_index_ == stream.device_index(), "Event device ", device_index_,
        " does not match recording stream's device ", stream.device_index(), ".");
    DIPUGuard guard(device_index_);
    devproxy::recordEvent(event_, stream);
    was_recorded_ = true;
  }

  void wait(const DIPUStream& stream) {
    if (isCreated()) {
      DIPUGuard guard(stream.device_index());
      devproxy::streamWaitEvent(stream, event_);
    }
  }

  float elapsed_time(const DIPUEvent& other) const {
    TORCH_CHECK(isCreated() && other.isCreated(),
        "Both events must be recorded before calculating elapsed time.");
    float time_ms = 0;
    devproxy::eventElapsedTime(&time_ms, event_, other.event_);
    return time_ms;
  }

  void synchronize() const {
    if (isCreated()) {
      devproxy::waitEvent(event_);
    }
  }

  // dipu do not support IpcEventHandle until now

private:
  unsigned int flags_ = 0;
  bool was_recorded_ = false;
  c10::DeviceIndex device_index_ = -1;
  deviceEvent_t event_ = nullptr;

  void createEvent(c10::DeviceIndex device_index) {
    device_index_ = device_index;
    DIPUGuard guard(device_index_);
    devproxy::createEvent(&event_);
  }

  void moveHelper(DIPUEvent&& other) {
    std::swap(flags_, other.flags_);
    std::swap(was_recorded_, other.was_recorded_);
    std::swap(device_index_, other.device_index_);
    std::swap(event_, other.event_);
  }
};

} // namespace c10_dipu

