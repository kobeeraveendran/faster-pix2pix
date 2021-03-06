import torch
import torch.nn as nn
from torchvision import models

#############################################################
# unet
#############################################################

class EncoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=4, stride=2, padding=1, dilation=1, groups=1, bias=False,
                 do_norm=True, norm = 'batch', do_activation = True): # bias default is True in Conv2d
        super(EncoderBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, groups=groups, bias=bias)
        self.leakyRelu = nn.LeakyReLU(0.2, True)
        self.do_norm = do_norm
        self.do_activation = do_activation
        if do_norm:
            if norm == 'batch':
                self.norm = nn.BatchNorm2d(out_channels)
            elif norm == 'instance':
                self.norm = nn.InstanceNorm2d(out_channels)
            elif norm == 'none':
                self.do_norm = False
            else:
                raise NotImplementedError("norm error")

    def forward(self, x):
        if self.do_activation:
            x = self.leakyRelu(x)

        x = self.conv(x)

        if self.do_norm:
            x = self.norm(x)

        return x

class DecoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=4, stride=2, padding=1, bias=False,
                 do_norm=True, norm = 'batch',do_activation = True, dropout_prob=0.0):
        super(DecoderBlock, self).__init__()

        self.convT = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding, bias=bias)
        self.relu = nn.ReLU()
        self.dropout_prob = dropout_prob
        self.drop = nn.Dropout2d(dropout_prob)
        self.do_norm = do_norm
        self.do_activation = do_activation
        if do_norm:
            if norm == 'batch':
                self.norm = nn.BatchNorm2d(out_channels)
            elif norm == 'instance':
                self.norm = nn.InstanceNorm2d(out_channels)
            elif norm == 'none':
                self.do_norm = False
            else:
                raise NotImplementedError("norm error")

    def forward(self, x):
        if self.do_activation:
            x = self.relu(x)

        x = self.convT(x)

        if self.do_norm:
           x = self.norm(x)

        if self.dropout_prob != 0:
            x= self.drop(x)

        return x

class Generator(nn.Module):
    def __init__(self, in_channels=3, out_channels=3, bias = False, dropout_prob=0.5, norm = 'batch'):
        super(Generator, self).__init__()

        # 8-step encoder
        self.encoder1 = EncoderBlock(in_channels, 64, bias=bias, do_norm=False, do_activation=False)
        self.encoder2 = EncoderBlock(64, 128, bias=bias, norm=norm)
        self.encoder3 = EncoderBlock(128, 256, bias=bias, norm=norm)
        self.encoder4 = EncoderBlock(256, 512, bias=bias, norm=norm)
        self.encoder5 = EncoderBlock(512, 512, bias=bias, norm=norm)
        self.encoder6 = EncoderBlock(512, 512, bias=bias, norm=norm)
        self.encoder7 = EncoderBlock(512, 512, bias=bias, norm=norm)
        self.encoder8 = EncoderBlock(512, 512, bias=bias, do_norm=False)

        # 8-step UNet decoder
        self.decoder1 = DecoderBlock(512, 512, bias=bias, norm=norm)
        self.decoder2 = DecoderBlock(1024, 512, bias=bias, norm=norm, dropout_prob=dropout_prob)
        self.decoder3 = DecoderBlock(1024, 512, bias=bias, norm=norm, dropout_prob=dropout_prob)
        self.decoder4 = DecoderBlock(1024, 512, bias=bias, norm=norm, dropout_prob=dropout_prob)
        self.decoder5 = DecoderBlock(1024, 256, bias=bias, norm=norm)
        self.decoder6 = DecoderBlock(512, 128, bias=bias, norm=norm)
        self.decoder7 = DecoderBlock(256, 64, bias=bias, norm=norm)
        self.decoder8 = DecoderBlock(128, out_channels, bias=bias, do_norm=False)

    def forward(self, x):
        # 8-step encoder
        encode1 = self.encoder1(x)
        encode2 = self.encoder2(encode1)
        encode3 = self.encoder3(encode2)
        encode4 = self.encoder4(encode3)
        encode5 = self.encoder5(encode4)
        encode6 = self.encoder6(encode5)
        encode7 = self.encoder7(encode6)
        encode8 = self.encoder8(encode7)

        # 8-step UNet decoder
        decode1 = torch.cat([self.decoder1(encode8), encode7],1)
        decode2 = torch.cat([self.decoder2(decode1), encode6],1)
        decode3 = torch.cat([self.decoder3(decode2), encode5],1)
        decode4 = torch.cat([self.decoder4(decode3), encode4],1)
        decode5 = torch.cat([self.decoder5(decode4), encode3],1)
        decode6 = torch.cat([self.decoder6(decode5), encode2],1)
        decode7 = torch.cat([self.decoder7(decode6), encode1],1)
        decode8 = self.decoder8(decode7)
        final = nn.Tanh()(decode8)
        return final

class GeneratorUResNet(nn.Module):
    def __init__(self, in_channels = 3, out_channels = 3, bias = False, dropout_prob = 0.5, norm = 'batch'):
        super(GeneratorUResNet, self).__init__()

        
        # encoder section
        self.encoder1 = EncoderBlock(in_channels, 64, bias = bias, do_norm = False, do_activation = False)
        self.encoder2 = EncoderBlock(64, 128, bias = bias, norm = norm)
        self.encoder3 = EncoderBlock(128, 256, bias = bias, norm = norm)
        self.encoder4 = EncoderBlock(256, 256, bias = bias, do_norm = False)

        # resnet blocks
        self.resnet1 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet2 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet3 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet4 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet5 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet6 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)

        # decoder section
        self.decoder1 = DecoderBlock(512, 256, bias = bias, norm = norm)
        self.decoder2 = DecoderBlock(512, 128, bias = bias, norm = norm)
        self.decoder3 = DecoderBlock(256, 64, bias = bias, norm = norm)
        self.decoder4 = DecoderBlock(128, out_channels, bias = bias, do_norm = False)

    def forward(self, x):

        
        e1 = self.encoder1(x)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)
        e4 = self.encoder4(e3)

        r1 = self.resnet1(e4)
        r2 = self.resnet2(r1)
        r3 = self.resnet3(r2)
        r4 = self.resnet4(r3)
        r5 = self.resnet5(r4)
        r6 = self.resnet6(r5)

        cat1 = torch.cat([r6, e4], 1)
        d1 = self.decoder1(cat1)
        cat2 = torch.cat([d1, e3], 1)
        d2 = self.decoder2(cat2)
        cat3 = torch.cat([d2, e2], 1)
        d3 = self.decoder3(cat3)
        cat4 = torch.cat([d3, e1], 1)
        d4 = self.decoder4(cat4)

        final = nn.Tanh()(d4)

        return final

class GeneratorUResNet9(nn.Module):
    
    def __init__(self, in_channels = 3, out_channels = 3, bias = False, dropout_prob = 0.5, norm = 'batch'):
        super(GeneratorUResNet9, self).__init__()

        
        # encoder section
        self.encoder1 = EncoderBlock(in_channels, 64, bias = bias, do_norm = False, do_activation = False)
        self.encoder2 = EncoderBlock(64, 128, bias = bias, norm = norm)
        self.encoder3 = EncoderBlock(128, 256, bias = bias, norm = norm)
        self.encoder4 = EncoderBlock(256, 256, bias = bias, do_norm = False)

        # resnet blocks
        self.resnet1 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet2 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet3 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet4 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet5 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet6 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet7 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet8 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)
        self.resnet9 = ResidualLayer(256, (3, 3), final_relu = False, bias = bias)

        # decoder section
        self.decoder1 = DecoderBlock(512, 256, bias = bias, norm = norm)
        self.decoder2 = DecoderBlock(512, 128, bias = bias, norm = norm)
        self.decoder3 = DecoderBlock(256, 64, bias = bias, norm = norm)
        self.decoder4 = DecoderBlock(128, out_channels, bias = bias, do_norm = False)

    def forward(self, x):

        
        e1 = self.encoder1(x)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)
        e4 = self.encoder4(e3)

        r1 = self.resnet1(e4)
        r2 = self.resnet2(r1)
        r3 = self.resnet3(r2)
        r4 = self.resnet4(r3)
        r5 = self.resnet5(r4)
        r6 = self.resnet6(r5)
        r7 = self.resnet7(r6)
        r8 = self.resnet8(r7)
        r9 = self.resnet9(r8)

        cat1 = torch.cat([r9, e4], 1)
        d1 = self.decoder1(cat1)
        cat2 = torch.cat([d1, e3], 1)
        d2 = self.decoder2(cat2)
        cat3 = torch.cat([d2, e2], 1)
        d3 = self.decoder3(cat3)
        cat4 = torch.cat([d3, e1], 1)
        d4 = self.decoder4(cat4)

        final = nn.Tanh()(d4)

        return final


#############################################################
# patchGAN
#############################################################

class Discriminator(nn.Module):
    def __init__(self, in_channels=3, out_channels=1, bias = False, norm = 'batch', sigmoid=True):
        super(Discriminator, self).__init__()
        self.sigmoid = sigmoid

        # 70x70 discriminator
        self.disc1 = EncoderBlock(in_channels * 2, 64, bias=bias, do_norm=False, do_activation=False)
        self.disc2 = EncoderBlock(64, 128, bias=bias, norm=norm)
        self.disc3 = EncoderBlock(128, 256, bias=bias, norm=norm)
        self.disc4 = EncoderBlock(256, 512, bias=bias, norm=norm, stride=1)
        self.disc5 = EncoderBlock(512, out_channels, bias=bias, stride=1, do_norm=False)

    def forward(self, x, ref):
        d1 = self.disc1(torch.cat([x, ref],1))
        d2 = self.disc2(d1)
        d3 = self.disc3(d2)
        d4 = self.disc4(d3)
        d5 = self.disc5(d4)
        if self.sigmoid:
            final = nn.Sigmoid()(d5)
        else:
            final = d5
        return final

#############################################################
# imageGAN
#############################################################

class Discriminator286(nn.Module):
    def __init__(self, in_channels=3, out_channels=1, bias = False, norm = 'batch', sigmoid=True):
        super(Discriminator286, self).__init__()

        self.sigmoid = sigmoid

        # 286x286 discriminator
        self.disc1 = EncoderBlock(in_channels * 2, 64, bias=bias, do_norm=False, do_activation=False)
        self.disc2 = EncoderBlock(64, 128, bias=bias, norm=norm)
        self.disc3 = EncoderBlock(128, 256, bias=bias, norm=norm)
        self.disc4 = EncoderBlock(256, 512, bias=bias, norm=norm)
        self.disc5 = EncoderBlock(512, 512, bias=bias, norm=norm)
        self.disc6 = EncoderBlock(512, 512, bias=bias, stride=1, norm=norm)
        self.disc7 = EncoderBlock(512, out_channels, bias=bias, stride=1, do_norm=False)

    def forward(self, x, ref):
        d1 = self.disc1(torch.cat([x, ref],1))
        d2 = self.disc2(d1)
        d3 = self.disc3(d2)
        d4 = self.disc4(d3)
        d5 = self.disc5(d4)
        d6 = self.disc6(d5)
        d7 = self.disc7(d6)
        if self.sigmoid:
            final = nn.Sigmoid()(d7)
        else:
            final = d7
        return final


#############################################################
# resnet6
#############################################################


def norm_relu_layer(out_channel, do_norm, norm, relu):
    if do_norm:
        if norm == 'instance':
            norm_layer = nn.InstanceNorm2d(out_channel)
        elif norm == 'batch':
            norm_layer = nn.BatchNorm2d(out_channel)
        else:
            raise NotImplementedError("norm error")
    else:
        norm_layer = nn.Dropout2d(0)  # Identity

    if relu is None:
        relu_layer = nn.ReLU()
    else:
        relu_layer = nn.LeakyReLU(relu, inplace=True)

    return norm_layer, relu_layer

def Conv_Norm_ReLU(in_channel, out_channel, kernel, padding=0, dilation=1, groups=1, stride=1, bias=True,
                   do_norm=True, norm='batch', relu=None):
    """
    Convolutional -- Norm -- ReLU Unit
    :param norm: 'batchnorm' --> use BatchNorm2D, 'instancenorm' --> use InstanceNorm2D, 'none' --> Identity()
    :param relu: None -> Use vanilla ReLU; float --> Use LeakyReLU(relu)

    :input (N x in_channel x H x W)
    :return size same as nn.Conv2D
    """
    norm_layer, relu_layer = norm_relu_layer(out_channel, do_norm, norm, relu)

    return nn.Sequential(
        nn.Conv2d(in_channel, out_channel, kernel, padding=padding, stride=stride,
                  dilation=dilation, groups=groups, bias=bias),
        norm_layer,
        relu_layer
    )

def Deconv_Norm_ReLU(in_channel, out_channel, kernel, padding=0, output_padding=0, stride=1, groups=1,
                     bias=True, dilation=1, do_norm=True, norm='batch'):
    """
    Deconvolutional -- Norm -- ReLU Unit
    :param norm: 'batchnorm' --> use BatchNorm2D, 'instancenorm' --> use InstanceNorm2D, 'none' --> Identity()
    :param relu: None -> Use vanilla ReLU; float --> Use LeakyReLU(relu)

    :input (N x in_channel x H x W)
    :return size same as nn.ConvTranspose2D
    """
    norm_layer, relu_layer = norm_relu_layer(out_channel, do_norm, norm, relu=None)
    return nn.Sequential(
        nn.ConvTranspose2d(in_channel, out_channel, kernel, padding=padding, output_padding=output_padding,
                           stride=stride, groups=groups, bias=bias, dilation=dilation),
        norm_layer,
        relu_layer
    )

class ResidualLayer(nn.Module):
    """
    Residual block used in Johnson's network model:
    Our residual blocks each contain two 3×3 convolutional layers with the same number of filters on both
    layer. We use the residual block design of Gross and Wilber [2] (shown in Figure 1), which differs from
    that of He et al [3] in that the ReLU nonlinearity following the addition is removed; this modified design
    was found in [2] to perform slightly better for image classification.
    """

    def __init__(self, channels, kernel_size, final_relu=False, bias=False, do_norm=True, norm='batch'):
        super().__init__()
        self.kernel_size = kernel_size
        self.channels = channels
        self.padding = (self.kernel_size[0] - 1) // 2
        self.final_relu = final_relu

        norm_layer, relu_layer = norm_relu_layer(self.channels, do_norm, norm, relu=None)
        self.layers = nn.Sequential(
            nn.Conv2d(self.channels, self.channels, self.kernel_size, padding=self.padding, bias=bias),
            norm_layer,
            nn.ReLU(),
            nn.Conv2d(self.channels, self.channels, self.kernel_size, padding=self.padding, bias=bias),
            norm_layer
        )

    def forward(self, input):
        # input (N x channels x H x W)
        # output (N x channels x H x W)
        out = self.layers(input)
        if self.final_relu:
            return nn.ReLU(out + input)
        else:
            return out + input
'''
class ResNeXtLayer(nn.Module):
    
    # ResNeXt block based on the ResNeXt model proposed in Facebook AI's paper
    # "Aggregated Residual Transformations for Deep Neural Networks"
    

    def __init__(self, in_channels, out_channels, stride, cardinality = 4, bottleneck_width, widen_factor = 1):
        super(ResNeXtLayer, self).__init__()
        
        width_ratio = out_channels / (widen_factor * 64.0)
        D = cardinality * int(base_width * width_ratio)

        self.conv_reduce = nn.Conv2d(in_channels, D, kernel_size = (1, 1), stride = (1, 1), padding = 0, bias = False)
        self.bn_reduce = nn.BatchNorm2d(D)
        self.conv_conv = nn.Conv2d(D, D, kernel_size = (3, 3), stride = stride, padding = 1, groups = cardinality, bias = False)
        self.bn = nn.BatchNorm2d(D)
        self.conv_expand = nn.Conv2d(D, out_channels, kernel_size = (1, 1), stride = (1, 1), padding = 0, bias = False)
        self.bn_expand = nn.BatchNorm2d(out_channels)

        self.shortcut = nn.Sequential()

        if in_channels != out_channels:
            self.shortcut.add_module('shortcut_conv', 
                nn.Conv2d(in_channels, out_channels, kernel_size = (1, 1), stride = stride, padding = 0, bias = False))
            self.shortcut.add_module('shortcut_bn', nn.BatchNorm2d(out_channels))

    def forward(self, x):
        bottleneck = self.conv_reduce(x)
        bottleneck = F.relu(self.bn_reduce(bottleneck), inplace = True)
        bottleneck = self.conv_conv(bottleneck)
        bottleneck = F.relu(self.bn(bottleneck), inplace = True)
        bottleneck = self.conv_expand(bottleneck)
        bottleneck = self.bn_expand(bottleneck)
        
        residual = self.shortcut(x)

        return F.relu(residual + bottleneck, inplace = True)

'''

class GeneratorJohnson(nn.Module):
    """
    The Generator architecture in < Perceptual Losses for Real-Time Style Transfer and Super-Resolution >
    by Justin Johnson, et al.
    """

    def __init__(self, in_channels=3, out_channels=3, do_norm=True, norm='batch', bias=True):
        super(GeneratorJohnson, self).__init__()
        model = []
        model += [Conv_Norm_ReLU(in_channels, 32, (7, 7), padding=3, stride=1, bias=bias, do_norm=do_norm, norm=norm),
                  # c7s1-32
                  Conv_Norm_ReLU(32, 64, (3, 3), padding=1, stride=2, bias=bias, do_norm=do_norm, norm=norm),  # d64
                  Conv_Norm_ReLU(64, 128, (3, 3), padding=1, stride=2, bias=bias, do_norm=do_norm, norm=norm)]  # d128
        for i in range(6):
            model += [ResidualLayer(128, (3, 3), final_relu=False, bias=bias)]  # R128
        model += [
            Deconv_Norm_ReLU(128, 64, (3, 3), padding=1, output_padding=1, stride=2, bias=bias, do_norm=do_norm, norm=norm),
            # u64
            Deconv_Norm_ReLU(64, 32, (3, 3), padding=1, output_padding=1, stride=2, bias=bias, do_norm=do_norm, norm=norm),
            # u32
            nn.Conv2d(32, out_channels, (7, 7), padding=3, stride=1, bias=bias),  # c7s1-3
            nn.Tanh()]
        self.model = nn.Sequential(*model)

    def forward(self, input):
        """
        :param input: (N x channels x H x W)
        :return: output: (N x channels x H x W) with numbers of range [-1, 1] (since we use tanh())
        """
        return self.model(input)


#############################################################
# resnet9 with reflection padding
#############################################################

class ResidualBlock2(nn.Module):
    def __init__(self, in_features, norm_layer=nn.InstanceNorm2d):
        super(ResidualBlock2, self).__init__()

        conv_block = [nn.ReflectionPad2d(1),
                      nn.Conv2d(in_features, in_features, 3),
                      norm_layer(in_features),
                      nn.ReLU(inplace=True),
                      nn.ReflectionPad2d(1),
                      nn.Conv2d(in_features, in_features, 3),
                      norm_layer(in_features)]

        self.conv_block = nn.Sequential(*conv_block)

    def forward(self, x):
        return x + self.conv_block(x)


class GeneratorJohnson2(nn.Module):
    """
    Generator with 9 residual blocks and reflection padding.
    """

    def __init__(self, image_channel=3, norm='instancenorm', n_res_blocks=9):
        super(GeneratorJohnson2, self).__init__()
        if norm == 'batchnorm':
            norm_layer = nn.BatchNorm2d
        elif norm == 'instancenorm':
            norm_layer = nn.InstanceNorm2d
        else:
            raise Exception("Norm not specified!")

        # Downsample
        model = [nn.ReflectionPad2d(3),
                 nn.Conv2d(image_channel, 64, 7),
                 norm_layer(64),
                 nn.ReLU(inplace=True)]

        in_channels = 64
        out_channels = in_channels * 2
        # 256 -> 128
        for i in range(2):
            model += [nn.Conv2d(in_channels, out_channels, 3, stride=2, padding=1),
                      norm_layer(out_channels),
                      nn.ReLU(inplace=True)]
            in_channels = out_channels # 128, 256
            out_channels = in_channels * 2 # 256, 512

        # Residual blocks
        for i in range(n_res_blocks):
            model += [ResidualBlock2(in_channels, norm_layer=norm_layer)]

        # Upsample
        out_channels = in_channels // 2
        for i in range(2):
            model += [nn.ConvTranspose2d(in_channels, out_channels, 3, stride=2, padding=1, output_padding=1),
                      norm_layer(out_channels),
                      nn.ReLU(inplace=True)]
            in_channels = out_channels
            out_channels = in_channels // 2

        model += [nn.ReflectionPad2d(3),
                  nn.Conv2d(64, 3, 7),
                  nn.Tanh()]

        self.model = nn.Sequential(*model)


    def forward(self, input):
        return self.model(input)

'''
class GeneratorUResnet(nn.Module):
    def __init__(self, image_channel = 3, norm = 'instancenorm', n_res_blocks = 9):
        super(GeneratorUResnet, self).__init__()

        if norm == 'batchnorm':
            norm_layer = nn.BatchNorm2d
        elif norm == 'instancenorm':
            norm_layer = nn.InstanceNorm2d
        else:
            raise Exception('Unspecified norm')

        # downsampling
        model = [
                nn.ReflectionPad2d(3),
                nn.Conv2d(image_channel, 64, 7),
                norm_layer(64),
                nn.ReLU(inplace=True)
        ]

        in_channels = 64
        out_channels = in_channels * 2

        # 256 -> 128 -> 64
        for i in range(3):
            model += [nn.Conv2d(in_channels, out_channels, 3, stride = 2, padding = 1), 
                      norm_layer(out_channels), 
                      nn.ReLU(inplace = True)]

        # resnet blocks
        for i in range(n_res_blocks):
            model += [ResidualBlock2(in_channels, norm_layer = norm_layer)]

        # upsampling
        out_channels = in_channels // 2

        for i in range(3):
            model += [nn.ConvTranspose2d(in_channels, out_channels, 3, stride = 2, padding = 1, output_padding = 1), 
                      norm_layer(out_channels), 
                      nn.ReLU(inplace = True)]

            in_channels = out_channels
            out_channels = in_channels // 2

        model += [nn.ReflectionPad2d(3), 
                  nn.Conv2d(64, 3, 7), 
                  nn.Tanh()]

        self.model = nn.Sequential(*model)

    def forward(self, input):
        return self.model(input)

'''

#############################################################
# resnet50
#############################################################

class Resnet50(nn.Module):
    """
    Generator with 9 residual blocks and reflection padding.
    """

    def __init__(self, image_channel=3, norm='instancenorm'):
        super(Resnet50, self).__init__()
        if norm == 'batchnorm':
            norm_layer = nn.BatchNorm2d
        elif norm == 'instancenorm':
            norm_layer = nn.InstanceNorm2d
        else:
            raise Exception("Norm not specified!")

        model = []
        # Downsample, 256 -> 128 -> 64 -> 32 -> 16 -> 8, throw out last 4 layers from batch norm to FC
        res_original = models.resnet50(pretrained=False)
        model += list(res_original.children())[:-2]

        # Upsample
        in_channels = 2048
        out_channels = in_channels // 2
        for i in range(5):
            model += [nn.ConvTranspose2d(in_channels, out_channels, 3, stride=2, padding=1, output_padding=1),
                      norm_layer(out_channels),
                      nn.ReLU(inplace=True)]
            in_channels = out_channels
            out_channels = in_channels // 2

        model += [nn.ReflectionPad2d(3),
                  nn.Conv2d(64, image_channel, 7),
                  nn.Tanh()]

        self.model = nn.Sequential(*model)


    def forward(self, input):
        return self.model(input)

#############################################################
# resnet101
#############################################################

class Resnet101(nn.Module):
    """
    Generator with 9 residual blocks and reflection padding.
    """

    def __init__(self, image_channel=3, norm='batchnorm'):
        super(Resnet101, self).__init__()
        if norm == 'batchnorm':
            norm_layer = nn.BatchNorm2d
        elif norm == 'instancenorm':
            norm_layer = nn.InstanceNorm2d
        else:
            raise Exception("Norm not specified!")

        model = []
        # Downsample, 256 -> 128 -> 64 -> 32 -> 16 -> 8, throw out last 4 layers from batch norm to FC
        res_original = models.resnet101(pretrained=False)
        model += list(res_original.children())[:-2]

        # Upsample
        in_channels = 2048
        out_channels = in_channels // 2
        for i in range(5):
            model += [nn.ConvTranspose2d(in_channels, out_channels, 3, stride=2, padding=1, output_padding=1),
                      norm_layer(out_channels),
                      nn.ReLU(inplace=True)]
            in_channels = out_channels
            out_channels = in_channels // 2

        model += [nn.ReflectionPad2d(3),
                  nn.Conv2d(64, image_channel, 7),
                  nn.Tanh()]

        self.model = nn.Sequential(*model)


    def forward(self, input):
        return self.model(input)