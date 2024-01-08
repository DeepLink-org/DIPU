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
    def forward(self, a, b):
        res_Tensor = torch.ops.aten.lt.Tensor(a, b)
        return res_Tensor


model = OpModule()
args = parse_args()
compiled_model = compile_model(model, args.backend, args.dynamic)


class TestLt():
    @pytest.mark.parametrize("dtype", [torch.float32])
    @pytest.mark.parametrize("sizes", [[Size((5,), (5, 3)), Size((5,), (5, 3))], [Size((3, 5), (5, 3)), Size((3, 5), (5, 3))], [Size((2, 3, 4), (2, 4)), Size((2, 3, 4), (2, 4))], [Size((4,), (4,)), Size((4, 1), (4, 1))]])
    @pytest.mark.parametrize("compiled_model", compiled_model)
    def test_torch_lt(self, sizes, dtype, compiled_model):
        device = get_device()
        size1 = sizes[0].dynamic if compiled_model.dynamic else sizes[0].static
        size2 = sizes[1].dynamic if compiled_model.dynamic else sizes[1].static
        input1 = torch.randn(size1, dtype=dtype)
        input2 = torch.randn(size2, dtype=dtype)

        # for case number 4
        if size1 != size2:
            input1 = torch.tensor([0, 1, 2, 3])
            input2 = torch.tensor([[1], [2], [3], [4]])

        dicp_input1 = input1.to(device)
        dicp_input2 = input2.to(device)

        output = model(input1, input2)
        dynamo.reset()
        update_dynamo_config(compiled_model.dynamic)
        dicp_output = compiled_model.model(dicp_input1, dicp_input2)

        assert torch.allclose(output, dicp_output.cpu(), equal_nan=True)
