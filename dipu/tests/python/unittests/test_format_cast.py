# Copyright (c) 2023, DeepLink.
import torch
import torch_dipu
import numpy as np

from torch_dipu.testing._internal.common_utils import TestCase, run_tests, onlyOn

dipu = torch_dipu.dipu.diputype
device_dipu = torch.device(dipu)

class TestFormatCast(TestCase):
    def create_single_tensor(self, item, minvalue, maxvalue):
        dtype = item[0]
        shape = item[1]
        input = np.random.uniform(minvalue, maxvalue, shape).astype(dtype)
        return torch.from_numpy(input).to(device_dipu)
        
    def check_and_get_format_tensor(self, a, native_memory_format):
        b = torch_dipu.native_memory_format_cast(a, native_memory_format)
        self.assertEqual(torch_dipu.get_native_memory_format(b), native_memory_format)
        return b

    @onlyOn("NPU")
    def test_format_cast(self):
        shape_format1 = [np.float16, (2, 2, 4, 4)]
        shape_format2 = [np.float16, (2, 2, 2, 2, 4)]
        dipu_tensor1 = self.create_single_tensor(shape_format1, 1, 5)
        dipu_tensor2 = self.create_single_tensor(shape_format2, 1, 5)
       
        
        dipu_format_list = [torch_dipu.NativeMemoryFormat.NCHW,
                            torch_dipu.NativeMemoryFormat.ND,
                            torch_dipu.NativeMemoryFormat.NCHW,
                            torch_dipu.NativeMemoryFormat.FRACTAL_Z,
                            torch_dipu.NativeMemoryFormat.NCHW,
                            torch_dipu.NativeMemoryFormat.FRACTAL_NZ,
                            torch_dipu.NativeMemoryFormat.NCHW,
                            torch_dipu.NativeMemoryFormat.ND,
                            torch_dipu.NativeMemoryFormat.FRACTAL_Z,
                            torch_dipu.NativeMemoryFormat.NCHW,     
                            torch_dipu.NativeMemoryFormat.ND,
                            torch_dipu.NativeMemoryFormat.FRACTAL_NZ,
                            torch_dipu.NativeMemoryFormat.NCHW,
                            torch_dipu.NativeMemoryFormat.NC1HWC0]
        
        for dipu_format in dipu_format_list:
            dipu_tensor1 = self.check_and_get_format_tensor(dipu_tensor1, dipu_format)
    
        dipu_format_list = [torch_dipu.NativeMemoryFormat.NCDHW,
                            torch_dipu.NativeMemoryFormat.FRACTAL_Z_3D,
                            torch_dipu.NativeMemoryFormat.NCDHW,
                            torch_dipu.NativeMemoryFormat.ND,
                            torch_dipu.NativeMemoryFormat.FRACTAL_Z_3D,
                            torch_dipu.NativeMemoryFormat.ND,
                            torch_dipu.NativeMemoryFormat.NCDHW,
                            torch_dipu.NativeMemoryFormat.NDC1HWC0,
                            torch_dipu.NativeMemoryFormat.NCDHW,
                            torch_dipu.NativeMemoryFormat.ND,
                            torch_dipu.NativeMemoryFormat.NDC1HWC0,
                            torch_dipu.NativeMemoryFormat.ND]
        for dipu_format in dipu_format_list:
            dipu_tensor2 = self.check_and_get_format_tensor(dipu_tensor2, dipu_format)


if __name__ == "__main__":
    run_tests()
