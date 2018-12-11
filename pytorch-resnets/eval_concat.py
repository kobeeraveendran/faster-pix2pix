import PIL
from PIL import Image
import sys
import os

start_idx = int(input("start image id: "))
end_idx = int(input("end image id: "))
pix2pix_folder = input("unet(pix2pix) folder name: ")
uresnet9_folder = input("uresnet9 folder name: ")

gt_dir = 'datasets/maps/testB'
pix2pix_dir = 'checkpoints/' + pix2pix_folder + '/images/test'
uresnet9_dir = 'checkpoints/' + uresnet9_folder + '/images/test'
target_path = 'img_comparison'

if target_path not in os.listdir():
    os.mkdir(target_path)

#gt_dir = os.listdir(gt_dir)
#pix2pix_dir = os.listdir(pix2pix_dir)
#uresnet9_dir = os.listdir(uresnet9_dir)

for i in range(start_idx - 1, end_idx):
    gt_file = gt_dir + '/' + str(i + 1) + '_B.jpg'
    p2p_file = pix2pix_dir + '/' + str(i + 1) + '_test.png'
    uresnet9_file = uresnet9_dir + '/' + str(i + 1) + '_test.png'

    gt = Image.open(gt_file)
    p2p = Image.open(p2p_file)
    uresnet9 = Image.open(uresnet9_file)

    # resize dataset's image to match
    gt = gt.resize((p2p.size[1], p2p.size[0]))

    # concatenate images in format groundtruth | pix2pix | uresnet9
    total_width = sum([gt.size[0], p2p.size[0], uresnet9.size[0]])
    height = max(gt.size[1], p2p.size[1], uresnet9.size[1])

    new_image = Image.new('RGB', (total_width, height))

    x_start = 0
    for im in [gt, p2p, uresnet9]:
        new_image.paste(im, (x_start, 0))
        x_start += im.size[0]

    new_file = target_path + '/set_' + str(i + 1) + '.jpg'
    new_image.save(new_file)