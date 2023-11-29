import logging
import traceback
import torch
from abc import ABC

from torch._functorch import config
from torch.utils._pytree import tree_map, tree_flatten
from torch.fx.experimental.symbolic_shapes import ShapeEnv
from contextlib import nullcontext
from torch._subclasses import FakeTensor, FakeTensorMode
from dicp.dynamo_bridge.utils import TensorInfo

reqValOPList=[ # need to pass inputs without constructing fake tensor
    "Const",
]

viewLikeOPList=[  # operators changing "view" without modifing real storage
    "Slice",
    "Reshape"
]

class Operator(ABC):
    __name__: str
    _singleton = None

    def __init__(self, name_):
        super().__init__()
        self.__name__ = name_
        if torch.__version__.startswith("2.0"):
            self.shape_env = ShapeEnv() if config.use_dynamic_shapes else None
            self.fake_mode = (
                FakeTensorMode(shape_env=self.shape_env)
                if config.use_fake_tensor
                else nullcontext()
            )
        elif torch.__version__.startswith("2.1"):
            self.shape_env = ShapeEnv() if torch._dynamo.config.dynamic_shapes else None
            self.fake_mode = (
                FakeTensorMode(shape_env=self.shape_env)
                if config.fake_tensor_allow_meta
                else nullcontext()
            )
        else:
            raise ValueError(f"unsupported dicp torch version: {torch.__version__}")

    @classmethod
    def get_singleton(cls):
        args = [None] * (cls.__init__.__code__.co_argcount - 1)
        if cls._singleton is None:
            cls._singleton = cls(*args)
        return cls._singleton

    def name(self):
        return self.__name__

    # @abstractmethod
    # def infer_result(self, *args, **kwargs):
    #     pass

    def get_fake_mode_from_args(self, args):
        fake_mode = None
        tmp_args, _ = tree_flatten(args)
        for arg in tmp_args:
            if isinstance(arg, FakeTensor):
                fake_mode = arg.fake_mode
                break
        fake_mode = self.fake_mode if fake_mode is None else fake_mode
        return fake_mode

    def __call__(self, *args, **kwargs):
        def get_meta(x):
            return x if not hasattr(x, "meta") else x.meta["val"]

        new_args = tree_map(get_meta, args)

        fake_mode = self.get_fake_mode_from_args(new_args)

        def make_faketensor(x):
            if not isinstance(x, torch.Tensor) or (
                isinstance(x, FakeTensor) and x.fake_mode == fake_mode
            ):
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
            print("operator: ",self)
            try:
                if hasattr(self, "infer_result"):
                    if self.__name__ in reqValOPList: # directly pass input to next op
                        return new_args, kwargs
                    if self.__name__ in viewLikeOPList:# reset stride and storage_offset in op's infer_result
                        return self.infer_result(*new_args, **kwargs)
                    info: TensorInfo = self.infer_result(*new_args, **kwargs)
                    return torch.empty(info.shape, dtype=info.dtype, memory_format=info.memory_format)
                elif hasattr(self, "torch_op"):
                    return self.torch_op(*new_args, **kwargs)
            except Exception as e:
                print("torch_op: ", self.torch_op if hasattr(self, "torch_op") else "")
                print(new_args, kwargs)
                print(e.args)
                print(traceback.format_exc())
                log = logging.getLogger(__name__)
                if hasattr(self, "infer_result"):
                    log.warning("infer shape and dtype failed")
                elif hasattr(self, "torch_op"):
                    log.warning("torch_op error")
