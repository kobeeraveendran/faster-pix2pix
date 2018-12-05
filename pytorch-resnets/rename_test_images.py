# run with:
# python rename_test_images.py checkpoint/[checkpointID]/images/test

# purpose: renames all images in the generated test img directory to match
# the format of the cycleGAN dataset, allowing us to run the evaluation.py script
# correctly without re-training on differently-named files

import os
import sys

directory = sys.argv[1]

for filename in os.listdir(directory):
    ext = filename.split('.')
    pieces = ext[0].split('_')
    new_filename = pieces[1] + '_' + pieces[0] + '.' + ext[1]

    os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))