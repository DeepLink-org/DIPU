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
        res_Tensor = torch.ops.aten.index.Tensor(a, b)
        return res_Tensor


model = OpModule()
args = parse_args()
compiled_model = compile_model(model, args.backend, args.dynamic)


class TestIndex():
    @pytest.mark.skipif(args.backend != "ascendgraph",
                        reason="This is the test case for index in ascendgraph!")
    @pytest.mark.parametrize("dtype", [torch.float32])
    @pytest.mark.parametrize("sizes", [Size((5, 3), (5, 3)), Size((3, 5), (5, 3)), Size((4, 2), (4, 2))])
    @pytest.mark.parametrize("compiled_model", compiled_model)
    def test_torch_index_ascend(self, sizes, dtype, compiled_model):
        device = get_device()
        size = sizes.dynamic if compiled_model.dynamic else sizes.static
        input1 = torch.randn(size, dtype=dtype)
        input2 = [torch.tensor([0, 2])]

        dicp_input1 = input1.to(device)
        dicp_input2 = [torch.tensor([0, 2], device=device)]

        output = model(input1, input2)
        dynamo.reset()
        update_dynamo_config(compiled_model.dynamic)
        dicp_output = compiled_model.model(dicp_input1, dicp_input2)
        assert torch.allclose(output, dicp_output.cpu(), equal_nan=True)

    @pytest.mark.skipif(args.backend != "topsgraph",
                        reason="This is the test case for index in topsgraph!")
    @pytest.mark.parametrize("dtype", [torch.float32])
    @pytest.mark.parametrize("sizes", [Size(((10, 15), (None, [0, 2],)), ((10, 15), (None, [0, 2],))),
                                       Size(((10, 15, 20), ([[1], [2]], [[3, 4]])),
                                            ((15, 20), ([[1], [2]], [[3, 4]]))),
                                       Size(((10, 15, 20, 25), (None, [[2, 2]], [[1, 3], [4, 5]], [[1], [2]])),
                                            ((10, 25), ([[1], [2]], [5])))])
    @pytest.mark.parametrize("compiled_model", compiled_model)
    def test_torch_index_tops(self, sizes, dtype, compiled_model):
        device = get_device()
        size = sizes.dynamic if compiled_model.dynamic else sizes.static
        input1 = torch.randn(size[0], dtype=dtype)
        input2 = [item if item is None else torch.tensor(item) for item in size[1]]

        dicp_input1 = input1.to(device)
        dicp_input2 = [item if item is None else torch.tensor(item).to(device) for item in size[1]]

        output = model(input1, input2)
        dynamo.reset()
        update_dynamo_config(compiled_model.dynamic)
        dicp_output = compiled_model.model(dicp_input1, dicp_input2)

        assert torch.allclose(output, dicp_output.cpu(), equal_nan=True)
