import os
import pickle
import random
import numpy as np
from scipy.ndimage.filters import gaussian_filter

# PATHS
split_directory = '../data_shops/page_sets/splits/'
test_results_directory = '../test_results/'
snapshots_directory = '../models/snapshots/'
boxes_directory = '../data_shops/input_boxes/'
priors_directory = '../data_shops/split_priors/'

# CONSTANTS
max_x = 1280
max_y = 1280

#####--- GET DATA PATHS

def get_train_data_path(split_name):
    return os.path.join(split_directory,'split_'+split_name+'_train.txt')
 
def get_test_data_path(split_name):
    return os.path.join(split_directory,'split_'+split_name+'_test.txt')

def get_result_path(experiment, split_name):
    results_dir = os.path.join(test_results_directory, experiment)
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)  

    return os.path.join(results_dir, split_name+'.txt')

def get_snapshot_name(experiment, split_name, iter):
    snapshots_dir = os.path.join(snapshots_directory, experiment)
    if not os.path.exists(snapshots_dir):
        os.makedirs(snapshots_dir)

    return os.path.join(snapshots_dir, 'snapshot_split_'+split_name+'_'+str(iter)+'.caffemodel')


####---  POSITION MAPS

def create_position_maps(train_data, split_name):
    print 'Creating and saving position maps'

    n_samples = 1000

    #--- GET TRAINING DATA
    with open(train_data) as f:
        train_pages = [line.strip() for line in f.readlines()]

    #--- GET RANDOM SUBSET
    sample_pages = random.sample(train_pages, n_samples)

    #--- FROM EACH RANDOM PAGE, USE POSITION OF GT ELEMENTS 
    final_maps = [np.ones((max_y,max_x),dtype=np.float32)]*4
    for page in sample_pages:
        # load boxes
        boxes_path = os.path.join(boxes_directory, page+'.pkl')
        with open(boxes_path,'rb') as f:
            boxes = pickle.load(f)
        gt_boxes = boxes['gt_boxes']

        # add to finals
        background_map = np.ones((max_y,max_x),dtype=np.float32) # we add one (we do not want zero probability)
        for i in range(1,4):
            bb = gt_boxes[i-1]
            background_map[bb[1]:bb[3],bb[0]:bb[2]] = 0
            type_map = np.zeros((max_y,max_x),dtype=np.float32)
            type_map[bb[1]:bb[3],bb[0]:bb[2]] = 1
            final_maps[i] = final_maps[i] + type_map

        final_maps[0] = final_maps[0] + background_map


    #--- normalize
    for i in range(0,4):
        final_maps[i] = final_maps[i]/(1+n_samples)

    #--- save
    for i in range(0,4):
        path = os.path.join(priors_directory,'split_'+split_name+'_'+str(i)+'.pkl')
        pickle.dump(final_maps[i], open(path,"wb"))

def load_position_map(file_name, sigma):
    map = pickle.load(open(file_name,'rb'))
    ### Gaussian convolution
    filtered_maps = []
    filtered =  gaussian_filter(map, sigma)
    return filtered

def load_position_maps(split_name, sigma):
    print 'Loading position maps smoothed with Gausian filter, sigma=',sigma

    maps = []
    for i in range(4):
        ### Load map
        path = os.path.join(priors_directory,'split_'+split_name+'_'+str(i)+'.pkl')
        filtered = load_position_map(path, sigma)
        maps.append(filtered)
    return maps
