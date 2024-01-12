import torch
import torch.fx
from torch.fx import replace_pattern
from torch.fx.node import Argument, Target
from typing import Optional
from torch._subclasses import FakeTensor, FakeTensorMode
from torch.utils._pytree import tree_map, tree_flatten
import torch.fx.traceback as fx_traceback
from torch.fx.proxy import Proxy
from typing import Any, Dict, Tuple
from dicp.dynamo_bridge.compile_fx import is_torch_210
from dicp.vendor.AscendGraph.codegen.utils import symint_in_shape
from torch.fx.passes.shape_prop import _extract_tensor_metadata, TensorMetadata
from contextlib import nullcontext
from torch._functorch import config
from torch.fx.experimental.symbolic_shapes import ShapeEnv


class OpSetTransformer:
    def __init__(self, patterns):
        self._patterns = patterns

    def transform(self, module: torch.fx.GraphModule):
        # first step: replace pattern
        for pat in self._patterns:
            replace_pattern(module, pat.pattern, pat.replacement)
        return module


class SingleOpTransformer(torch.fx.Transformer):
    def __init__(self, module, conversions):
        super().__init__(module)
        self._conversions = conversions
        self.sym_to_inputs = {}
        self.sym_in_args = {}

    def placeholder(self, target: 'Target', args: Tuple[Argument, ...], kwargs: Dict[str, Any]) -> Proxy:
        proxy = super().placeholder(target, args, kwargs)
        proxy.node.meta = fx_traceback.get_current_meta()
        fake_tensor = proxy.node.meta['val']
        if isinstance(fake_tensor, torch.SymInt):
            self.sym_to_inputs[fake_tensor.node.str()] = proxy
        elif symint_in_shape(fake_tensor.shape):
            # mention symint position in args
            # dynamic shape feature
            for idx, dim in enumerate(fake_tensor.shape):
                if isinstance(dim, torch.SymInt):
                    st = dim.node.str()
                    if st not in self.sym_in_args:
                        self.sym_in_args[st] = (proxy, idx)
        return proxy

    def get_proxy(self, target, args: Tuple[Argument, ...], kwargs: Dict[str, Any] = {}):
        proxy = self.tracer.create_proxy(
            'call_function', target.get_singleton(), args, kwargs)
        return proxy

    def get_proxy_from_node(self, node):
        return self.tracer.proxy(node)

    def call_function(self, target: Target, args: Tuple[Argument, ...], kwargs: Dict[str, Any]) -> Any:
        if target in self._conversions:
            converted_target = self._conversions[target]
            if isinstance(converted_target, tuple):
                # converted_target: (Operation, process_args_kwargs_fn)
                out, process_fn = converted_target
                args, kwargs = process_fn(args, kwargs)
            else:
                out = self._conversions[target](self, *args, **kwargs)
            if isinstance(out, Proxy):
                out.node.meta = fx_traceback.get_current_meta()
                return out
            proxy = self.tracer.create_proxy(
                'call_function', out, args, kwargs)
            proxy.node.meta = fx_traceback.get_current_meta()
            return proxy
        return super().call_function(target, args, kwargs)

    def get_attr(self, target: 'Target', args: Tuple[Argument, ...], kwargs: Dict[str, Any]) -> Proxy:
        proxy = super().get_attr(target, args, kwargs)
        proxy.node.meta = fx_traceback.get_current_meta()
        if 'val' not in proxy.node.meta:
            proxy.node.meta['val'] = self.fetch_attr(target)
        return proxy


if is_torch_210:
    import functools
    from typing import List
    from torch.fx.experimental.proxy_tensor import maybe_disable_fake_tensor_mode
    from torch._subclasses.fake_tensor import FakeTensorMode
    from torch._inductor.pattern_matcher import (
        PatternMatcherPass,
        stable_topological_sort,
        register_replacement,
    )

    def symbolic_trace_ignore_args(fn, args):
        return torch.fx.symbolic_trace(fn)

    class BackendPatternBase:
        @staticmethod
        def pattern(*args, **kwargs):
            raise NotImplementedError("pattern is not implemented")

        @staticmethod
        def replacement(*args, **kwargs):
            raise NotImplementedError("replacement is not implemented")

        @classmethod
        def gen_args(cls):
            return [None] * (cls.pattern.__code__.co_argcount)

        @staticmethod
        def check_fn(match):
            return True

        @classmethod
        @functools.lru_cache(None)
        def register(cls, backend_patterns):
            register_replacement(
                cls.pattern,
                cls.replacement,
                cls.gen_args(),
                symbolic_trace_ignore_args,
                backend_patterns,
                extra_check=cls.check_fn,
            )

    def register_backend_patterns(patterns_cls_list: List[BackendPatternBase], Pattern: BackendPatternBase):
        patterns_cls_list.append(Pattern)
        return Pattern

    @functools.lru_cache(None)
    def lazy_register_backend_patterns(patterns: PatternMatcherPass, patterns_cls_list: Tuple[BackendPatternBase]):
        with torch._guards.tracing(
            None
        ), maybe_disable_fake_tensor_mode(), FakeTensorMode():
            for pattern in patterns_cls_list:
                pattern.register(patterns)

    class BackendPatternMatcherTransformer:
        def __init__(self, patterns: PatternMatcherPass, patterns_cls_list: List[BackendPatternBase]):
            self._patterns = patterns
            lazy_register_backend_patterns(
                self._patterns, tuple(patterns_cls_list))

        # TODO refine code
        def infer_shape_dtype(self, module: torch.fx.GraphModule):
            def make_tensor_meta(x) -> Optional[TensorMetadata]:
                if isinstance(x, FakeTensor):
                    return _extract_tensor_metadata(x)
                else:
                    return None

            def get_fake_mode_from_args(args):
                shape_env = ShapeEnv() if torch._dynamo.config.dynamic_shapes else None
                fake_mode = None
                tmp_args, _ = tree_flatten(args)
                for arg in tmp_args:
                    if isinstance(arg, FakeTensor):
                        fake_mode = arg.fake_mode
                        break
                fake_mode = (FakeTensorMode(shape_env=shape_env) if config.fake_tensor_allow_meta else nullcontext()) if fake_mode is None else fake_mode
                return fake_mode

            def get_meta_val(node, *args, **kwargs):
                def get_meta(x):
                    return x if not hasattr(x, "meta") else x.meta["val"]
                new_args = tree_map(get_meta, args)

                fake_mode = get_fake_mode_from_args(new_args)

                def make_faketensor(x):
                    if not isinstance(x, torch.Tensor) or (isinstance(x, FakeTensor) and x.fake_mode == fake_mode):
                        return x
                    if isinstance(x, FakeTensor):
                        x.fake_mode = fake_mode
                        return x
                    return FakeTensor.from_tensor(x, fake_mode)
                new_args = tree_map(make_faketensor, new_args)

                def make_cpu(x):
                    if isinstance(x, torch.Tensor):
                        return x.to("cpu")
                    return x
                new_args = tree_map(make_cpu, new_args)

                with fake_mode:
                    try:
                        return node.target(*new_args, **kwargs)
                    except Exception as e:
                        raise RuntimeError("infer shape and dtype failed")

            for n in module.graph.nodes:
                if n.op == "call_function" and "val" not in n.meta and "tuple" not in n.name:
                    n.meta["val"] = get_meta_val(n, *n.args, **n.kwargs)
                    n.meta["tensor_meta"] = make_tensor_meta(n.meta["val"])

        def transform(self, module: torch.fx.GraphModule):
            match_count = self._patterns.apply(module)
            if match_count:
                stable_topological_sort(module.graph)
                module.graph.lint()
                module.recompile()
                self.infer_shape_dtype(module)
            return module
