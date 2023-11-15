import pytest
from common.utils import (
    torch,
    dynamo,
    parse_args,
    compile_model,
    get_device,
    Size,
    update_dynamo_config,
)


class OpModule(torch.nn.Module):
    def forward(self, a):
        res_default = torch.ops.aten._softmax.default(a, dim=0, half_to_float=False)
        return res_default


model = OpModule()
args = parse_args()
compiled_model = compile_model(model, args.backend, args.dynamic)


class TestSoftmax():
    @pytest.mark.parametrize("dtype", [torch.float32])
    @pytest.mark.parametrize("sizes", [Size((5,), (5, 3)), Size((3, 5), (5, 3)), Size((2, 3, 4), (2, 4))])
    @pytest.mark.parametrize("compiled_model", compiled_model)
    def test_torch__softmax(self, sizes, dtype, compiled_model):
        device = get_device()
        size = sizes.dynamic if compiled_model.dynamic else sizes.static
        input1 = torch.randn(size, dtype=dtype)

        dicp_input1 = input1.to(device)

        output = model(input1)
        dynamo.reset()
        update_dynamo_config(compiled_model.dynamic)
        dicp_output = compiled_model.model(dicp_input1)

        assert torch.allclose(output, dicp_output.cpu(), equal_nan=True)
