import torch
import torch.fx
from typing import Tuple
import operator

from dicp.dynamo_bridge.operator import Operator
from torch._subclasses import FakeTensorMode
aten = torch.ops.aten


def binary_dtype_check(name, lhs_t, rhs_t):
    assert lhs_t.dtype == rhs_t.dtype, \
        f"{name}: dtype of lhs - {lhs_t.dtype}, dtype of rhs - {rhs_t.dtype}"
    return lhs_t.dtype


def binary_device_check(name, lhs_t, rhs_t):
    assert lhs_t.device == rhs_t.device, \
        f"{name}: device of lhs - {lhs_t.device}, device of rhs - {rhs_t.device}"
    return lhs_t.device


class Add(Operator):
    def __init__(self, a, b, **kwargs):
        super().__init__("Add")
        self.a = a
        self.b = b
        self.kwargs = kwargs
        self.torch_op = aten.add.Tensor


class AddDefalut(Operator):
    def __init__(self, a, b):
        super().__init__("Add")
        self.a = a
        self.b = b
        self.torch_op = aten.add.default


class AddScalar(Operator):
    def __init__(self, a, b):
        super().__init__("Add")
        self.a = a
        self.b = b
        self.torch_op = aten.add.Scalar


class Abs(Operator):
    def __init__(self, a):
        super().__init__("Abs")
        self.a = a
        self.torch_op = aten.abs


class Less(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Less")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.lt.Tensor


class LessEqual(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("LessEqual")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.le.Scalar


class NotEqual(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("NotEqual")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.ne.Scalar

    def __call__(self, *args, **kwargs):
        new_args = args[1:]
        return super().__call__(*new_args, **kwargs)


class Mul(Operator):
    def __init__(self, a, b):
        super().__init__("Mul")
        self.a = a
        self.b = b
        self.torch_op = aten.mul


class ComplexMul(Operator):
    def __init__(self, a, b):
        super().__init__("ComplexMul")
        self.a = a
        self.b = b
        self.torch_op = aten.mul


class Div(Operator):
    def __init__(self, a, b):
        super().__init__("Div")
        self.a = a
        self.b = b
        self.torch_op = aten.div


class DivScalar(Operator):
    def __init__(self, a, b):
        super().__init__("Div")
        self.a = a
        self.b = b
        self.torch_op = aten.div.Scalar


class Sub(Operator):
    def __init__(self, a, b):
        super().__init__("Sub")
        self.a = a
        self.b = b
        self.torch_op = aten.sub


class Sqrt(Operator):
    def __init__(self, a):
        super().__init__("Sqrt")
        self.a = a
        self.torch_op = aten.sqrt


class Exp(Operator):
    def __init__(self, a):
        super().__init__("Exp")
        self.a = a
        self.torch_op = aten.exp


class Sin(Operator):
    def __init__(self, a):
        super().__init__("Sin")
        self.a = a
        self.torch_op = aten.sin


class Cos(Operator):
    def __init__(self, a):
        super().__init__("Cos")
        self.a = a
        self.torch_op = aten.cos


class Relu(Operator):
    def __init__(self, a):
        super().__init__("Relu")
        self.a = a
        self.torch_op = aten.relu


class Erf(Operator):
    def __init__(self, a):
        super().__init__("Erf")
        self.a = a
        self.torch_op = aten.erf


class ArgMax(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("ArgMax")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.argmax


class ArgMin(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("ArgMin")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.argmin


class ReduceSum(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("ReduceSum")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.sum


class ReduceMean(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("ReduceMean")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.mean


class ReduceMax(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("ReduceMax")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.amax


class Squeeze(Operator):
    def __init__(self, a, b):
        super().__init__("Squeeze")
        self.a = a
        self.b = b
        self.torch_op = aten.squeeze


class Unsqueeze(Operator):
    def __init__(self, a, b):
        super().__init__("Unsqueeze")
        self.a = a
        self.b = b
        self.torch_op = aten.unsqueeze


class Transpose(Operator):
    def __init__(self, a, b):
        super().__init__("Transpose")
        self.a = a
        self.b = b
        self.torch_op = aten.permute


class Transpose1(Operator):
    def __init__(self, a, b, c):
        super().__init__("Transpose")
        self.a = a
        self.b = b
        self.c = c
        self.torch_op = aten.transpose


class Hardswish(Operator):
    def __init__(self, a):
        super().__init__("Hardswish")
        self.a = a
        self.torch_op = aten.hardswish


class HardswishBackward(Operator):
    def __init__(self, a, b):
        super().__init__("HardswishBackward")
        self.a = a
        self.b = b
        self.torch_op = aten.hardswish_backward


class Clone(Operator):
    def __init__(self, *args, **kargs):
        super().__init__("Clone")
        self.args = args
        self.torch_op = aten.clone


class Alias(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Clone")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.alias


class Copy(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Copy")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.aten.copy


class Copy_(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Copy_")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.aten.copy_


class LiftFreshCopy(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("LiftFreshCopy")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.aten.lift_fresh_copy.default

    def __call__(self, *args, **kwargs):
        if hasattr(args[0], 'meta'):
            return args[0].meta['val']
        else:
            with FakeTensorMode():
                return torch.empty(())


class Neg(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Neg")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.neg


class Reshape(Operator):
    def __init__(self, a, b):
        super().__init__("Reshape")
        self.a = a
        self.b = b
        self.torch_op = aten.view


class Reciprocal(Operator):
    def __init__(self, a):
        super().__init__("Reciprocal")
        self.a = a
        self.torch_op = aten.reciprocal


class Rsqrt(Operator):
    def __init__(self, a):
        super().__init__("Rsqrt")
        self.a = a
        self.torch_op = aten.rsqrt


class Convolution(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Convolution")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.convolution

    def __call__(self, x, weight, bias, stride, padding, dilation,
                 transposed, output_padding, groups, is_clast=False):
        if not is_clast:
            return super().__call__(x, weight, bias, stride, padding, dilation,
                                    transposed, output_padding, groups)
        with x.meta["val"].fake_mode:
            shape = torch.Size((x.meta["val"].shape[0], x.meta["val"].shape[3],
                                x.meta["val"].shape[1], x.meta["val"].shape[2]))
            dtype = x.meta["val"].dtype
            device = x.meta["val"].device
            fake_value_x = torch.empty(shape, dtype=dtype, device=device)
        with weight.meta["val"].fake_mode:
            shape = torch.Size((weight.meta["val"].shape[3], weight.meta["val"].shape[2],
                                weight.meta["val"].shape[0], weight.meta["val"].shape[1]))
            dtype = weight.meta["val"].dtype
            device = weight.meta["val"].device
            fake_value_weight = torch.empty(shape, dtype=dtype, device=device)
        conv = super().__call__(fake_value_x, fake_value_weight, bias, stride, padding,
                                dilation, transposed, output_padding, groups)
        with conv.fake_mode:
            shape = torch.Size((conv.shape[0], conv.shape[2],
                                conv.shape[3], conv.shape[1]))
            dtype, device = conv.dtype, conv.device
            conv = torch.empty(shape, dtype=dtype, device=device)
        return conv


class ConvolutionBackward(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Conv2DBackward")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.convolution_backward.default

    def __call__(self, *args, **kwargs):
        new_args = args[1:]
        return super().__call__(*new_args, **kwargs)


class Max_pool2d_with_indices(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("MaxPool2D")
        self.args = args
        self.torch_op = aten.max_pool2d_with_indices

    def __call__(self, *args, **kwargs):
        new_args = args[1:]
        return super().__call__(*new_args, **kwargs)


class Max_pool2d_with_indices_backward(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("MaxPool2DBackward")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.max_pool2d_with_indices_backward


class Adaptive_avg_pool2d(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("AvgPool2D")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten._adaptive_avg_pool2d.default

    def __call__(self, *args, **kwargs):
        new_args = args[1:]
        return super().__call__(*new_args, **kwargs)


class Gather(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Gather")
        self.args = args
        self.torch_op = aten.gather


class Log(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Log")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.log


class NativeDropout(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("NativeDropout")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.aten.native_dropout.default

    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)[0]


class BatchNorm(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("BatchNorm")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten._native_batch_norm_legit_functional.default


class BatchNormBackward(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("BatchnormBackward")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.native_batch_norm_backward.default

"""
Enlarge torch_op scope to adjust args for aten._softmax.default,
because the parameter half_to_float isn't needed in hlir_builder Softmax.
"""
class Softmax(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Softmax")
        self.torch_op = aten.softmax


class Bmm(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Bmm")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.bmm.default


class DotGeneral(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("DotGeneral")

    def __call__(self, lhs, rhs, lhs_batch_dims, rhs_batch_dims, lhs_contract_dims, rhs_contract_dims):
        lhs_tensor = lhs.meta['val']
        rhs_tensor = rhs.meta['val']
        res_device = binary_device_check(self.name(), lhs_tensor, rhs_tensor)
        res_dtype = binary_dtype_check(self.name(), lhs_tensor, rhs_tensor)

        lhs_shape = lhs_tensor.shape
        rhs_shape = rhs_tensor.shape
        lhs_shape_set = set(range(len(lhs_tensor.shape)))
        rhs_shape_set = set(range(len(rhs_tensor.shape)))
        assert lhs_shape_set | set(lhs_batch_dims) | set(lhs_contract_dims) == lhs_shape_set, \
            f"{self.name()}: lhs_batch_dims: {lhs_batch_dims} or lhs_contract_dims: {lhs_contract_dims}" + \
            f" isn't fully contained in lhs_shape_set: {lhs_shape_set}"
        assert rhs_shape_set | set(rhs_batch_dims) | set(rhs_contract_dims) == rhs_shape_set, \
            f"{self.name()}: rhs_batch_dims: {rhs_batch_dims} or rhs_contract_dims: {rhs_contract_dims}" + \
            f" isn't fully contained in rhs_shape_set: {rhs_shape_set}"
        assert len(lhs_batch_dims) == len(rhs_batch_dims), \
            f"{self.name()}: batch_dims mismatch, lhs: {lhs_batch_dims}, rhs: {rhs_batch_dims}"
        for idx in range(len(lhs_batch_dims)):
            assert lhs_shape[lhs_batch_dims[idx]] == rhs_shape[rhs_batch_dims[idx]], \
                f"{self.name()}: batch_dims size mismatch, lhs_batch_dims: {lhs_batch_dims}, rhs_batch_dims: {rhs_batch_dims}; " + \
                f"lhs_shape[{lhs_batch_dims[idx]}]: {lhs_shape[lhs_batch_dims[idx]] } != " + \
                f"rhs_shape[{rhs_batch_dims[idx]}]: {rhs_shape[rhs_batch_dims[idx]]}"
        assert len(lhs_contract_dims) == 1 and len(rhs_contract_dims) == 1 \
            and lhs_shape[lhs_contract_dims[0]] == rhs_shape[rhs_contract_dims[0]], \
            f"{self.name()}: contract_dims mistmatch, lhs_contract_dims: {lhs_contract_dims}, rhs_contract_dims: {rhs_contract_dims}; " + \
            f"lhs_shape: {lhs_shape}, rhs_shape: {rhs_shape}"
        lhs_remain_dim = lhs_shape_set - \
            set(lhs_batch_dims) - set(lhs_contract_dims)
        assert len(
            lhs_remain_dim) == 1, f"{self.name()}: lhs_remain_dim mismatch, lhs_remain_dim: {lhs_remain_dim}"
        rhs_remain_dim = rhs_shape_set - \
            set(rhs_batch_dims) - set(rhs_contract_dims)
        assert len(
            rhs_remain_dim) == 1, f"{self.name()}: rhs_remain_dim mismatch, rhs_remain_dim: {rhs_remain_dim}"

        res_shape = []
        for i in lhs_batch_dims:
            res_shape.append(lhs_shape[i])
        res_shape.append(lhs_shape[lhs_remain_dim.pop()])
        res_shape.append(rhs_shape[rhs_remain_dim.pop()])
        with self.get_fake_mode_from_args([lhs_tensor, rhs_tensor]):
            fake_t = torch.empty(
                size=res_shape, dtype=res_dtype, device=res_device)
        return fake_t


class Dot(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Dot")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.mm


class Concatenate(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Concatenate")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.cat.default


class EmptyLike(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("EmptyLike")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.empty_like.default


class Bernoulli(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Bernoulli")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.bernoulli.p


class NewEmptyStrided(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("NewEmptyStrided")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.new_empty_strided.default


class Equal(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Equal")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.eq


class Expand(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Expand")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.expand.default

    # The third parameter broadcast_dims is only required in hlir_builder Expand.
    def __call__(self, *args, **kwargs):
        new_args = args[:2]
        return super().__call__(*new_args, **kwargs)


class Stack(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Stack")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.stack


class Full(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Full")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.full.default


class FullLike(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("FullLike")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.full_like.default


class Max(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Max")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.maximum.default


class Pow(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Pow")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.pow


class Square(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Square")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.square


class Sigmoid(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Sigmoid")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.sigmoid.default


class Slice(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Slice")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.slice.Tensor

    def __call__(self, *args, **kwargs):
        new_args = args[3:]
        return super().__call__(*new_args, **kwargs)


class SliceInDim(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("SliceInDim")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.slice.Tensor


class SliceScatter(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("SliceScatter")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.aten.slice_scatter.default


class Index(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Index")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.index.Tensor


class Where(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Where")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.where.self


class Select(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Select")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.select.int


# scatter_value = torch.ops.aten.scatter.value(fulllike, 1, unsqueeze, -1.0);  fulllike = unsqueeze = None
class Scatter(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Scatter")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.scatter.value


class ZerosLike(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("ZerosLike")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.zeros_like


class OnesLike(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("OnesLike")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.ones_like


class Scalar(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Scalar")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.scalar_tensor.default


class Embedding(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Embedding")
        self.args = args
        self.kargs = kwargs
        self.torch_op = aten.embedding.default


class Convert(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Convert")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.prims.convert_element_type.default


class ViewAsComplex(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("ViewAsComplex")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.aten.view_as_complex


class ViewAsReal(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("ViewAsReal")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.aten.view_as_real


class UnsafeView(Operator):
    def __init__(self, a, b):
        super().__init__("Reshape")
        self.a = a
        self.b = b
        self.torch_op = aten._unsafe_view.default


class Logsoftmax(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Logsoftmax")
        self.torch_op = aten._log_softmax.default


class Gelu(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Gelu")
        self.torch_op = aten.gelu.default

    def __call__(self, *args, **kwargs):
        new_args = (args[0],)
        return super().__call__(*new_args, **kwargs)


class GeluBackward(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("GeluBackward")
        self.torch_op = aten.gelu_backward.default

    def __call__(self, *args, **kwargs):
        new_args = (args[0], args[1])
        return super().__call__(*new_args, **kwargs)


class Iota(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("Iota")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = torch.ops.prims.iota.default


class GetTupleElement(Operator):
    def __init__(self, x, idx):
        self.x = x
        self.idx = idx
        self.torch_op = operator.getitem
        super().__init__("GetTupleElement")

    def __call__(self, x, idx):
        if hasattr(x, 'meta'):
            x = x.meta['val']

            if hasattr(x, 'dtype') and x.dtype in (torch.cfloat, torch.cdouble):
                data_type = torch.double if x.dtype == torch.cdouble else torch.float
                data_size = x.size()
                with FakeTensorMode():
                    return torch.empty(data_size, dtype=data_type)

        x = x[idx]
        if hasattr(x, 'meta'):
            x = x.meta['val']
        return x


class MakeTuple(Operator):
    def __init__(self, *args):
        super().__init__("MakeTuple")

    def __call__(self, *args):
        return tuple(arg.meta["val"] if hasattr(arg, "meta") else arg for arg in args)


class XlaGather(Operator):
    def __init__(self, operand, indices, offset_dims, collapsed_slice_dims,
                 start_index_map, index_vector_dim, slice_size, out_shape):
        super().__init__("XlaGather")

    def __call__(self, operand, indices, offset_dims, collapsed_slice_dims,
                 start_index_map, index_vector_dim, slice_size, out_shape):
        with operand.meta['val'].fake_mode:
            return aten.empty(out_shape, device=operand.meta["val"].device)


class GroupNorm(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("GroupNorm")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.native_group_norm
    
    def __call__(self, x, weight, bias, n, c, hw, group, eps, is_clast=False):
        if not is_clast:
            return super().__call__(x, weight, bias, n, c, hw, group, eps)
        with x.meta["val"].fake_mode:
            shape, dtype = x.meta["val"].shape, x.meta["val"].dtype
            return tuple((aten.empty(shape, dtype=dtype), aten.empty(shape[:2], dtype=dtype),
                          aten.empty(shape[:2], dtype=dtype)))


class LayerNorm(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("LayerNorm")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.native_layer_norm

    def __call__(self, x, normalized_shape, weight, bias, eps, is_clast=False):
        if not is_clast:
            return super().__call__(x, normalized_shape, weight, bias, eps)
        shape, dtype = x.meta["val"].shape, x.meta["val"].dtype
        with x.meta["val"].fake_mode:
            return tuple((aten.empty(shape, dtype=dtype), aten.empty(shape[:2], dtype=dtype),
                            aten.empty(shape[:2], dtype=dtype)))


class UpsampleNearest2d(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__("UpsampleNearest2d")
        self.args = args
        self.kwargs = kwargs
        self.torch_op = aten.upsample_nearest2d

    def __call__(self, x, output_size, scales_h, scales_w, is_clast=False):
        if not is_clast:
            return super().__call__(x, output_size, scales_h, scales_w)
        with x.meta["val"].fake_mode:
            x_shape = torch.Size((x.meta["val"].shape[0], x.meta["val"].shape[3],
                                  x.meta["val"].shape[1], x.meta["val"].shape[2]))
            x = aten.empty(x_shape, dtype=x.meta["val"].dtype, device=x.meta["val"].device)
        normal_res = super().__call__(x, output_size, scales_h, scales_w)
        with normal_res.fake_mode:
            clast_shape = torch.Size((normal_res.shape[0], normal_res.shape[2],
                                      normal_res.shape[3], normal_res.shape[1]))
            clast_res = aten.empty(clast_shape, dtype=normal_res.dtype, device=normal_res.device)
        return clast_res
