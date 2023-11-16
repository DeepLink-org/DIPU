import pytest
from common.utils import (
    torch,
    dynamo,
    random,
    parse_args,
    compile_model,
    get_device,
    Size,
    update_dynamo_config,
)


class OpModule(torch.nn.Module):
    def forward(self, x, mask, value):
        res_Scalar = torch.ops.aten.masked_fill.Scalar(x, mask, value)
        return res_Scalar


model = OpModule()
args = parse_args()
compiled_model = compile_model(model, args.backend, args.dynamic)


class TestMaskedFill():
    @pytest.mark.parametrize("dtype", [torch.float32])
    @pytest.mark.parametrize("sizes", [Size((5,), (5, 3)), Size((3, 5), (5, 3)), Size((2, 3, 4), (2, 4))])
    @pytest.mark.parametrize("mask", [False, True])
    @pytest.mark.parametrize("compiled_model", compiled_model)
    def test_torch_masked_fill(self, sizes, mask, dtype, compiled_model):
        device = get_device()
        size = sizes.dynamic if compiled_model.dynamic else sizes.static
        inputs = torch.randn(size, dtype=dtype)
        mask = torch.tensor(mask)
        value = round(random.random(), 4)

        dicp_inputs = inputs.to(device)
        dicp_mask = mask.to(device)

        output = model(inputs, mask, value)
        dynamo.reset()
        update_dynamo_config(compiled_model.dynamic)
        dicp_output = compiled_model.model(dicp_inputs, dicp_mask, value)

        assert torch.allclose(output, dicp_output.cpu(), equal_nan=True)
