import torch.nn as nn
from .decom_net import DecomNet
from .enhance_net import EnhanceNet

class RetinexNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.decom = DecomNet()
        self.enhance = EnhanceNet()

    def forward(self, x):
        R, I = self.decom(x)
        I_enhanced = self.enhance(I)
        out = R * I_enhanced
        return out, R, I, I_enhanced
