import torch
import torch.nn as nn
import numpy as np
import torch_dipu

class Model(nn.Module):
    def __init__(self, in_channels):
        super(Model, self).__init__()
        self.op1 = nn.nn.Embedding(10, 3)

    def forward(self, x):
        x = self.op1(x)
        return x


def test_batchnorm_backward_eval():
    model = Model()
    cpu_tensor = torch.randn(2, 16, 1, 1)
    device = torch.device('dipu')
    dipu_tensor = cpu_tensor.to(device)
    cpu_tensor.requires_grad = True
    dipu_tensor.requires_grad = True

    for i in range(1):
        out = model(cpu_tensor)
        loss = out.sum()
        loss.backward()
        cpu_grad_list = []
        for _, module in model.named_parameters():
            cpu_grad_list.append(module.grad)
            module.grad = None

        model = model.to(device)
        out = model(dipu_tensor)
        loss = out.sum()
        loss.backward()
        dipu_grad_list = []
        for _, module in model.named_parameters():
            dipu_grad_list.append(module.grad.cpu())

        cpu_grad = cpu_tensor.grad
        dipu_grad = dipu_tensor.grad
        rtol = 1e-7
        atol = 1e-7
        assert np.allclose(cpu_grad.numpy(), dipu_grad.cpu().numpy(), rtol, atol, True)
        for cpu_grad, dipu_grad in zip(cpu_grad_list, dipu_grad_list):
            assert np.allclose(cpu_grad.numpy(), dipu_grad.cpu().numpy(), rtol, atol, True)