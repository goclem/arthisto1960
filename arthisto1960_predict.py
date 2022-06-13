#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@description: Performs predictions for the Arthisto 1960 project
@author: Clement Gorin
@contact: gorinclem@gmail.com
@version: 2022.05.30
'''

#%% HEADER

# Modules
import gc
import numpy as np
import tensorflow

from arthisto1960_utilities import *
from keras import layers, models
from os import path

# Samples
training   = identifiers(search_data(paths['labels']), regex = True)
legend_1900='(0600_6895|0625_6895|0600_6870|0625_6870|0625_6845|0600_6845|0650_6895|0650_6870|0650_6845|0675_6895|0675_6870|0675_6845|0850_6545|0825_6545|0850_6520|0825_6520|0825_6495).tif$'
legend_N   ='(0400_6570|0425_6570|0400_6595|0425_6595|0425_6545|0400_6545|0425_6520|0400_6520|0425_6395|0425_6420|0400_6395|0400_6420|0425_6720|0450_6720|0425_6745|0450_6745|0450_6695|0425_6695|0425_6670|0450_6670|0450_6570|0450_6595|0450_6545|0450_6520|0450_6945|0450_6920|0475_6920|0475_6795|0500_6795|0475_6770|0500_6770|0500_6720|0475_6720|0475_6695|0500_6695|0475_6670|0450_6645|0475_6645|0500_6645|0525_6670|0500_6670|0525_6645|0500_6620|0525_6620|0475_6620|0550_6820|0525_6820|0550_6895|0575_6895|0550_6870|0575_6870|0575_6845|0550_6845|0550_6670|0575_6670|0550_6695|0575_6695|0575_6645|0550_6645|0475_6495|0450_6495|0475_6470|0450_6470|0450_6420|0450_6395|0475_6420|0475_6395|0475_6320|0500_6320|0525_6495|0500_6495|0500_6520|0525_6520|0525_6320|0525_6345|0500_6345|0600_6670|0600_6695|0600_6645|0625_6495|0650_6495|0650_6520|0625_6520|0725_6320|0700_6320|0725_6345|0700_6345|0775_6420|0750_6420|0725_6420|0775_6445|0750_6445|0725_6445|0775_6395|0725_6395|0750_6395|0775_6370|0800_6370|0775_6345|0800_6345|1150_6170|1150_6145|1150_6120|1175_6195|1150_6195|1175_6170|1175_6145|1175_6120|1175_6095|1150_6095|1200_6095|1175_6070|1200_6070|1200_6220|1200_6195|1175_6220|1200_6170|1200_6145|1225_6170|1225_6145|1200_6120|1225_6120|1225_6095|1250_6120|1250_6145).tif$'
cities     = dict(paris='0625_6870|0650_6870', marseille='0875_6245|0875_6270', lyon='0825_6520|0825_6545', toulouse='0550_6295|0575_6295')

# Sets tensorflow verbosity
tensorflow.compat.v1.logging.get_verbosity()
tensorflow.compat.v1.logging.set_verbosity(tensorflow.compat.v1.logging.ERROR)

# FUNCTIONS

def predict_tiles(model, files):
    '''Predicts image batch'''
    images  = np.array([read_raster(file) for file in files])
    images  = layers.Rescaling(1./255)(images)
    blocks1 = images_to_blocks(images, blocksize=(256, 256), shift=False)
    blocks2 = images_to_blocks(images, blocksize=(256, 256), shift=True)
    probas1 = model.predict(blocks1, verbose=1)
    probas2 = model.predict(blocks2, verbose=1)
    probas1 = blocks_to_images(probas1, imagesize=images.shape[:3] + (1,), shift=False)
    probas2 = blocks_to_images(probas2, imagesize=images.shape[:3] + (1,), shift=True)
    probas  = (probas1 + probas2) / 2
    gc.collect()
    return probas

#%% PREDICTS NEW TILES

# Loads model
model = models.load_model(path.join(paths['models'], 'unet64_220609.h5'))

# Lists batches
batch_size = 3
batches = search_data(paths['images'], pattern=training)
batches = search_data(paths['images'], pattern='(0875_6245|0875_6270)\\.tif$')
batches = filter_identifiers(batches, search_data(paths['predictions'], pattern='tif$'))
batches = [batches[i:i + batch_size] for i in range(0, len(batches), batch_size)]
del batch_size

# Computes predictions
for i, files in enumerate(batches):
    print('Batch {i:d}/{n:d}'.format(i=i + 1, n=len(batches)))
    probas   = predict_tiles(model=model, files=files)
    outfiles = [path.join(paths['predictions'], path.basename(file).replace('image', 'proba')) for file in files]
    for proba, file, outfile in zip(probas, files, outfiles):
        write_raster(array=proba, profile=file, destination=outfile, nodata=None, dtype='float32')
del i, files, file, probas, proba, outfiles, outfile
# %%
