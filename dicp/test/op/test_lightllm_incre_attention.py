import pytest

from dicp.vendor.AscendGraph import ext_ops
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
    def forward(self, q, k, v, int_index_list, max_seq_length):
        res = torch.ops.lightllm.flash_attention_inference.default(q, k, v, int_index_list, max_seq_length, -1, -1, -1)
        return res


model = OpModule()
args = parse_args()
compiled_model = compile_model(model, args.backend, args.dynamic)


class TestLightllmIncreAttention():
    @pytest.mark.parametrize("dtype", [torch.float32])
    @pytest.mark.parametrize("sizes", [Size(((8, 16), (9,)), ((8, 16), (9,))), Size(((8, 32), (9,)), ((8, 32), (9,)))])
    @pytest.mark.parametrize("compiled_model", compiled_model)
    def test_lightllm_incre_attention(self, sizes, dtype, compiled_model):
        device = get_device()
        size = sizes.dynamic if compiled_model.dynamic else sizes.static
        input1 = torch.randn((1,) + size[0], dtype=dtype)
        input2 = torch.randn(size[1] + size[0], dtype=dtype)
        input3 = torch.randn(size[1] + size[0], dtype=dtype)
        input4 = list(size[1])
        max_seq_length = size[1][0]

        dicp_input1 = input1.to(device)
        dicp_input2 = input2.to(device)
        dicp_input3 = input3.to(device)
        dicp_input4 = input4

        output = model(input1, input2, input3, input4, max_seq_length)
        dynamo.reset()
        update_dynamo_config(compiled_model.dynamic)
        dicp_output = compiled_model.model(dicp_input1, dicp_input2, dicp_input3, dicp_input4, max_seq_length)

        assert torch.allclose(output, dicp_output.cpu(), rtol=1e-02, atol=1e-02, equal_nan=True)
