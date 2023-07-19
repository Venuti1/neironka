import os
import cv2
import sys
import caffe
import utils
import argparse
import tempfile
import subprocess
import numpy as np
import _init_paths
import matplotlib.pyplot as plt
from utils import load_position_map
from test import  get_probabilities_with_position
from custom_layers.dom_tree import DOMTree
import custom_layers.web_data_utils as data_utils

#----------------
# PREPARE PHANTOMJS DOWNLOAD PAGE (URL, TMPFILENAME) -> IMAGE.JPEG, DOM-TREE.JSON
# CALL PHANTOMJS WITH FILENAME
#-----------------

# NETWORK SETTINGS
N_FEATURES = 128
Y_SIZE = 1280
X_SIZE = 1280
SPATIAL_SHAPE = (Y_SIZE, X_SIZE)
TEXT_MAP_SCALE = 0.125
GAUSS_VAR = 80

def download_page(url):
    print "Downloading:",url
    temp_dir = tempfile.mkdtemp()
    result = subprocess.check_output(["phantomjs", "download_page.js",url,temp_dir])
    return temp_dir

def load_position_maps(position_map_path):
     #--- LOAD SMOTHED POSITION MAPS
    position_maps = []
    for i in range(4):
        path = os.path.join(position_map_path,str(i)+'.pkl')
        position_maps.append(load_position_map(path,sigma=80))
    return position_maps

def load_image_blob(image_path):
    # load image
    im = cv2.imread(image_path)
    size_x = min(im.shape[1],X_SIZE)
    size_y = min(im.shape[0],Y_SIZE)

    # Crop
    im_croped = np.zeros((Y_SIZE,X_SIZE,3),dtype=np.uint8)
    im_croped[:size_y,:size_x,:] = im[:size_y,:size_x,:] 

    # TODO - this part is tensor_list_to_blob -> move to CUSTOM LAYER utils
    n_channels = im.shape[2]
    im_blob = np.zeros((1, Y_SIZE, X_SIZE, n_channels), dtype=np.float32)
    im_blob[0, 0:im_croped.shape[0], 0:im_croped.shape[1], :] = im_croped
    im_blob = im_blob.transpose((0, 3, 1, 2))
    return im_blob

def load_text_blob(leaf_nodes):
    # get text nodes
    text_nodes = data_utils.get_text_nodes(leaf_nodes,N_FEATURES)

    # get text maps
    text_maps = data_utils.get_text_maps(text_nodes, N_FEATURES, SPATIAL_SHAPE, TEXT_MAP_SCALE)

    # TODO - this part is tensor_list_to_blob -> move to CUSTOM LAYER utils
    n_channels = text_maps.shape[2]
    text_blob = np.zeros((1, text_maps.shape[0], text_maps.shape[1], n_channels), dtype=np.float32)
    text_blob[0, 0:text_maps.shape[0], 0:text_maps.shape[1], :] = text_maps
    text_blob = text_blob.transpose((0, 3, 1, 2))
    return text_blob

def load_boxes_blob(leaf_nodes, max_x, max_y):
    # get input boxes
    boxes = np.array([leaf['position'] for leaf in leaf_nodes],dtype = np.float32)
    # remove boxes outside the considered area
    keep_indices = np.logical_and.reduce(((boxes[:,0]>=0), (boxes[:,1]>=0),(boxes[:,2]<=max_x), (boxes[:,3]<=max_y)))
    boxes = boxes[keep_indices,:]
    boxes_this_image = np.hstack((np.zeros((boxes.shape[0], 1)), boxes))
    return boxes_this_image

def net_forward(model, weights, im_blob, text_blob, boxes_blob):
    #LOAD NET
    net = caffe.Net(model, weights, caffe.TEST)

    # SET DATA
    net.blobs['im_data'].reshape(*(im_blob.shape))
    net.blobs['txt_data'].reshape(*(text_blob.shape))
    net.blobs['boxes'].reshape(*(boxes_blob.shape))

    # NET FORWARD
    net.forward(im_data=im_blob.astype(np.float32, copy=False),txt_data=text_blob.astype(np.float32, copy=False),
                            boxes=boxes_blob.astype(np.float32, copy=False))
    return net

def show(net, position_maps):
    
    # colors for particular classes
    colors = ['r','g','b']

    # get image
    image = net.blobs['im_data'].data
    image = np.squeeze(image[0,:,:,:])
    image = image/255.0
    image = np.transpose(image, (1,2,0))
    image = image[:,:,(2,1,0)]
    plt.imshow(image)

    # get predictions with boxes
    predicted = net.blobs['prob'].data[:,0:4,0,0]
    boxes = net.blobs['boxes'].data[:,1:5] 

    # get probabilities with position likelihoods
    probs = get_probabilities_with_position(boxes, predicted, position_maps)

    # compute maximum
    box_class = np.argmax(probs,axis=1)
    max_boxes = np.argmax(probs,axis=0)

    # draw result
    for cls in range(1,4):
        ind = max_boxes[cls]
        print probs[ind]
    
        pred_box = boxes[ind,:]
        rect = plt.Rectangle((pred_box[0], pred_box[1]), pred_box[2] - pred_box[0],
            pred_box[3] - pred_box[1], fill=True, alpha=0.5,facecolor=colors[cls-1],
            edgecolor=colors[cls-1], linewidth=3)
        plt.gca().add_patch(rect)

    plt.show()

if __name__ == "__main__":
    #--- Get params
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, help='URL to classify', required=True)
    parser.add_argument('--model', type=str, default='../models/inference.prototxt', help='Model definition in prototxt')
    parser.add_argument('--weights',  type=str, default='../models/weights/snapshot_split_1_10000.caffemodel', help='Initialize with pretrained model weights')
    parser.add_argument('--position_maps_dir', type=str, default='../models/likelihoods/', help='Number of iterations for training')
    args = parser.parse_args()
    
    #-- Load params
    url = args.url
    model = args.model
    weights = args.weights
    position_map_path = args.position_maps_dir


    # DOWNLOAD PAGE
    try:
        download_dir = download_page(url)
    except subprocess.CalledProcessError:
        print "Download was not succesfull"
        sys.exit(1)

    screenshot_path = os.path.join(download_dir,"screenshot.jpeg")
    dom_path = os.path.join(download_dir,"dom.json")

    # LOAD POSITION LIKELIHOODS
    position_maps = load_position_maps(position_map_path)

    # LOAD IMAGE BLOB
    im_blob = load_image_blob(screenshot_path)
    
    # LOAD TEXT BLOB AND BOXES BLOB
    dom = DOMTree(dom_path)
    leaf_nodes = dom.getPositionedLeafNodes()
    text_blob = load_text_blob(leaf_nodes)
    boxes_blob = load_boxes_blob(leaf_nodes,im_blob.shape[3],im_blob.shape[2])

    # NET FORWARD
    net = net_forward(model, weights, im_blob, text_blob, boxes_blob)
    show(net, position_maps)
