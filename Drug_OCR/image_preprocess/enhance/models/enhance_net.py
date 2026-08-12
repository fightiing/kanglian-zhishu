import torch.nn as nn

class EnhanceNet(nn.Module):
    """
    只增强 illumination I（1通道），输出 I_enhanced ∈ [0,1]
    """
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 32, 3, 1, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, 3, 1, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 3, 1, 1),
            nn.Sigmoid()
        )

    def forward(self, I):
        return self.net(I)
