import torch.nn as nn

class DecomNet(nn.Module):
    """
    输出 4 通道：R(3) + I(1)，均 Sigmoid 限制到 [0,1]
    """
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 64, 3, 1, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, 1, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 4, 3, 1, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        out = self.net(x)
        R = out[:, :3, :, :]
        I = out[:, 3:, :, :]
        return R, I
