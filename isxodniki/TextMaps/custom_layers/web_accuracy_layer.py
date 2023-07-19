import caffe
import numpy as np
from random import randint

class WebAccuracyLayer(caffe.Layer):

    def setup(self, bottom, top):

        #print '== setup =='        
        #print 'bottom 0 shape', bottom[0].data.shape
        #print 'bottom 1 shape', bottom[1].data.shape
        #print 'bottom 2 shape', bottom[2].data.shape

        #self.batch_size = bottom[0].data.shape[0]
        #if self.batch_size != 1:
        #    raise Exception('Batch size in TEST should be 1') 
        
        #print 'batch size', self.batch_size
        for i in range(0,3):
            top[i].reshape(1)


    def reshape(self, bottom, top):
        #top[0].reshape(*bottom[0].data.shape)

        #print '== reshape =='
        #print 'bottom 0 shape', bottom[0].data.shape
        #print 'bottom 1 shape', bottom[1].data.shape
        #print 'bottom 2 shape', bottom[2].data.shape

        #self.batch_size = bottom[0].data.shape[0]
        #if self.batch_size != 1:
        #    raise Exception('Batch size in TEST should be 1')

        #print 'batch size', self.batch_size
        #top[0].reshape(self.batch_size, 1)
        for i in range(0,3):
            top[i].reshape(1)

    def forward(self, bottom, top):
        
        #scale = 1.0/16
        results = np.zeros((1,3),dtype = np.float32)

        ### get results and boxes
        predicted = bottom[0].data[:,1:4]
        max_inds = np.argmax(predicted,axis=0)

        for cls in range(0,3):
           if max_inds[cls] == cls:
               top[cls].data[0] = 1
           else:
               top[cls].data[0] = 0

    def backward(self, top, propagate_down, bottom):
        #bottom[0].diff[...] = 10 * top[0].diff
        pass
