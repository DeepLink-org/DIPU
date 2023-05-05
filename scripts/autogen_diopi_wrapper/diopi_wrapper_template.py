diopi_wrapper_file_template_content = \
"""
// autogened file
#include <ATen/Tensor.h>

#include "csrc_dipu/aten/DIPUATenFunctions.h"
#include "csrc_dipu/aten/RegisterDIPU.hpp"
#include "csrc_dipu/diopirt/diopirt_impl.h"

$header_include_code

namespace dipu::native {

bool checkDiopiReturnValue() {
    static bool enable = std::getenv("DIPU_DISABLE_CHECK_DIOPI_RETURN_VALUE") == nullptr;
    return enable;
}

using namespace dipu::diopi_helper;

$functions_code

}  // namespace dipu::native

namespace at {

TORCH_LIBRARY_IMPL(aten, DIPU_DEVICE_TYPE_MACRO, m) {
    $op_register_code
}

TORCH_LIBRARY_IMPL(aten, DIPU_AUTOGRAD_DEVICE_TYPE_MACRO, m) {
    $autograd_op_register_code
}

}  // namespace at

"""

diopi_wrapper_function_template_content = \
"""
//  $comment
$cppsignautre {
    ::diopiContext context(dipu::getCurrentDIPUStream().rawstream());
    auto ctx = &context;

    $custom_code_at_the_beginning

    $input_process_code

    $output_process_code

    $attrs_process_code

    $custom_code_before_call_diopi

    ::diopiError_t ret = $diopi_fun_call_code
    if (checkDiopiReturnValue()) {
        TORCH_CHECK(ret == ::diopiSuccess, __FILE__, ":", __LINE__,"'$diopi_fun_call_code' error, error code is ", ret, "error message is ", diopiGetLastErrorString());
    }

    $custom_code_before_return

    $return_code
}
"""

op_register_template_content = \
"""
DIOPI_ATEN_FUNC("$register_name", $diopi_fun_name, $aten_fun_name);
"""
