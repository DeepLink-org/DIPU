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
    def forward(self, a, b):
        res_Tensor = torch.ops.aten.add.Tensor(a, b)
        a.copy_(res_Tensor)
        return res_Tensor


model = OpModule()
args = parse_args()
compiled_model = compile_model(model, args.backend, args.dynamic)


class TestInplaceCopy():
    @pytest.mark.parametrize("dtype", [torch.float32])
    @pytest.mark.parametrize("sizes", [Size((5,), (5, 3)), Size((3, 5), (5, 3)), Size((2, 3, 4), (2, 4))])
    @pytest.mark.parametrize("compiled_model", compiled_model)
    def test_torch_add(self, sizes, dtype, compiled_model):
        device = get_device()
        size = sizes.dynamic if compiled_model.dynamic else sizes.static
        input1 = torch.ones(size, dtype=dtype)
        input2 = torch.ones(size, dtype=dtype)

        dicp_input1 = input1.to(device)
        dicp_input2 = input2.to(device)

        output = model(input1, input2)
        dynamo.reset()
        update_dynamo_config(compiled_model.dynamic)
        dicp_output = compiled_model.model(dicp_input1, dicp_input2)

        for i, item in enumerate(output):
            if isinstance(item, torch.Tensor):
                assert torch.allclose(item, dicp_output[i].cpu(), equal_nan=True)
            else:
                assert item == dicp_output[i]

        # Confirm the correctness of the inplace copy result.
        assert torch.allclose(dicp_input1.cpu(), dicp_output.cpu(), equal_nan=True)
