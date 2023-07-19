import os
import sys
import caffe
import pickle
import utils
import test
import random
import argparse
import numpy as np
import google.protobuf as pb2
from caffe.proto import caffe_pb2
from sklearn.preprocessing import normalize


def snapshot(net, snapshot_path):
    net.save(snapshot_path)

#----- MAIN PART
if __name__ == "__main__":

    #--- Get params
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', type=int, help='Split number', required=True)
    parser.add_argument('--solver', type=str, default=None, help='solver prototxt', required=True)
    parser.add_argument('--test_model', type=str, default=None, help='test net prototxt', required=True)
    parser.add_argument('--weights', help='initialize with pretrained model weights',
                        default='/storage/plzen1/home/gogartom/DOM-Extraction/data/imagenet_models/CaffeNet.v2.caffemodel', type=str)
    parser.add_argument('--train_iters', type=int, default=10000, help='Number of iterations for training')
    parser.add_argument('--test_iters', type=int, default=100, help='Number of iterations for testing')
    parser.add_argument('--experiment', type=str, default=None, help='name of experiment', required=True)    
    args = parser.parse_args()
    
    #-- Load params
    split_name = str(args.split)
    train_iters = args.train_iters
    final_test_iters = args.test_iters
    solver_path = args.solver
    test_model = args.test_model
    pretrained_weights = args.weights    
    experiment = args.experiment

    #--- GET DATA PATHS
    train_data = utils.get_train_data_path(split_name)
    test_data = utils.get_test_data_path(split_name)

    #--- LOAD SMOTHED POSITION MAPS
    position_maps = utils.load_position_maps(split_name, 80)    

    #--- GET TEST RESULTS PATH
    test_res_path = utils.get_result_path(experiment, split_name)

    ###--- LOAD SOLVER PARAMS
    solver_param = caffe_pb2.SolverParameter()
    with open(solver_path, 'rt') as f:
        pb2.text_format.Merge(f.read(), solver_param)

    ###--- LOAD SOLVER
    caffe.set_mode_gpu()
    solver = caffe.SGDSolver(solver_path)

    ###--- TRAIN
    #-- set input data and pretrained model
    train_net = solver.net
    train_net.copy_from(pretrained_weights)
    train_net.layers[0].set_data(train_data)

    #-- make steps
    num_steps = 20
    test_every_n_iters = 200
    val_iters = 100
    for i in range(train_iters/num_steps):
        #-- update
        solver.step(num_steps)
        iteration=(i+1)*num_steps

        #-- print loss
        print '----------------------'
        print 'Iteration:',str(iteration)
        print 'Loss:',train_net.blobs['loss'].data
        sys.stdout.flush()

        #-- create snapshot and test
        if iteration%test_every_n_iters==0:
            print 'Snapshoting and Testing'
            sys.stdout.flush()

            #-- snapshot
            snapshot_path = utils.get_snapshot_name(experiment, split_name, iteration)
            snapshot(train_net, snapshot_path)

            #-- test
            net_results, position_results = test.test_net(test_model, snapshot_path, test_data, val_iters, position_maps)
           
            im_acc, price_acc, name_acc = net_results
            print 'NET: image accuracy:', im_acc
            print 'NET: price accuracy:', price_acc
            print 'NET: name accuracy:', name_acc
           
            p_im_acc, p_price_acc, p_name_acc = position_results
            print 'NET+POSITION: image accuracy:', p_im_acc
            print 'NET+POSITION: price accuracy:', p_price_acc
            print 'NET+POSITION: name accuracy:', p_name_acc
            
            sys.stdout.flush()

    ###--- FINAL SNAPSHOT
    snapshot_path = utils.get_snapshot_name(experiment, split_name,train_iters)
    train_net.save(snapshot_path)

    ###--- FINAL TEST
    print 'Final testing'
    sys.stdout.flush()

    net_results, position_results = test.test_net(test_model, snapshot_path, test_data, final_test_iters, position_maps)

    im_acc, price_acc, name_acc = net_results
    print 'NET: image accuracy:', im_acc
    print 'NET: price accuracy:', price_acc
    print 'NET: name accuracy:', name_acc

    p_im_acc, p_price_acc, p_name_acc = position_results
    print 'NET+POSITION: image accuracy:', p_im_acc
    print 'NET+POSITION: price accuracy:', p_price_acc
    print 'NET+POSITION: name accuracy:', p_name_acc
    sys.stdout.flush()

    ###--- save results
    with open(test_res_path, 'w+') as f:
        f.write('NET: image accuracy: '+str(im_acc)+"\n")
        f.write('NET: price accuracy: '+str(price_acc)+"\n")
        f.write('NET: name accuracy: '+str(name_acc)+"\n")
        f.write('\n')
        f.write('NET+POSITION: image accuracy: '+str(p_im_acc)+"\n")
        f.write('NET+POSITION: price accuracy: '+str(p_price_acc)+"\n")
        f.write('NET+POSITION: name accuracy: '+str(p_name_acc)+"\n")
