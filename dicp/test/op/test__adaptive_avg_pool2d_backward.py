import pytest
from ..common.utils import (
    torch,
    dynamo,
    parse_args,
    compile_model,
    get_device,
    Size,
    update_dynamo_config,
)


class OpModule(torch.nn.Module):
    def forward(self, inputs, outputs, device="cpu"):
        pool = torch.nn.AdaptiveAvgPool2d((1, 1))
        pool.to(device)
        res_default = pool(inputs)
        loss = torch.nn.MSELoss()
        res_loss = loss(res_default, outputs)
        res_loss.backward()
        return res_default


model = OpModule()
args = parse_args()
compiled_model = compile_model(model, args.backend, args.dynamic)


class TestAdaptiveAvgPool2dBackward():
    @pytest.mark.parametrize("dtype", [torch.float32])
    @pytest.mark.parametrize("sizes", [Size(((8, 16, 32, 64), (8, 16, 1, 1)), ((8, 16, 32, 64), (8, 16, 1, 1))),
                                       Size(((20, 16, 50, 100), (20, 16, 1, 1)), ((20, 16, 50, 100), (20, 16, 1, 1)))])
    @pytest.mark.parametrize("compiled_model", compiled_model)
    def test_torch__adpative_avg_pool2d_backward(self, sizes, dtype, compiled_model):
        device = get_device()
        size = sizes.dynamic if compiled_model.dynamic else sizes.static
        inputs = torch.randn(size[0], dtype=dtype)
        outputs = torch.randn(size[1], dtype=dtype, requires_grad=True)

        dicp_inputs = inputs.to(device)
        dicp_outputs = outputs.to(device)

        output = model(inputs, outputs)
        dynamo.reset()
        update_dynamo_config(compiled_model.dynamic)
        dicp_output = compiled_model.model(dicp_inputs, dicp_outputs, device)

        assert torch.allclose(output.detach(), dicp_output.cpu().detach(), atol=1e-02, equal_nan=True)
