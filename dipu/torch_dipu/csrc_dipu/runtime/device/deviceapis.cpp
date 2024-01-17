// Copyright (c) 2023, DeepLink.

#include "csrc_dipu/utils/vender_helper.hpp"

#include "basedef.h"

namespace dipu {

#ifndef DIPU_VENDOR_NAME
#error "DIPU_VENDOR_NAME must be defined"
#else
extern const devapis::VendorDeviceType kDipuVendorDeviceType =
    VendorNameToDeviceType(DIPU_STRINGIFY_AFTER_EXPANSION(DIPU_VENDOR_NAME));
#endif

}  // namespace dipu
