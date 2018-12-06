# faster-pix2pix

## Baseline code and acknowledgements

Code for the pytorch version is mainly adapted from https://github.com/yuzhoucw/230pix2pix which tackles a similar problem as ours, and 
includes their own proposed method. I used this as a baseline since it had many of the auxiliary functions (plotting, model selection with 
multiple models, etc.) and had many models to benchmark our own models on. Among the many models in gan_model and model_modules is 
UResNet, which is my own model that takes inspiration from their approach of using ResNets as an intermediary bottleneck layer.

Code for the keras version (mostly untouched) is adapted from https://github.com/tdeboissiere/DeepLearningImplementations/tree/master/pix2pix.
This version was only used to test the effect of scaling patches with image size, which obviously improved training time if the number of "sections"
chosen resulted in patches of size greater than 70 pixels. Interestingly, although the authors insisted that patch sizes of 70 were best, 
the model trained faster and just as well with an effective patch size of 128 (number of sections was 4, and 256 / 2 = 128). In the end, we decided not to go forward with this approach since it seemed trivial, though it could likely still be experimented with in combination with the models in `pytorch-resnets`.
