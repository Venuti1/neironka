import re
import numpy as np
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import HashingVectorizer

def preprocess_string(text):
    res = re.sub("[!.;?^*()_{}|]","", text) # remove special characters (we keep characters such as "$" and ",-" )
    res = re.sub("\d+", " ^number^ ", res)   # replace numbers wit special word and space
    return res

def my_tokenizer(s):
    return s.split()

def get_text_nodes(leaf_nodes, n_features):
    text_nodes = []
    vectorizer = HashingVectorizer(n_features=n_features, tokenizer=my_tokenizer, non_negative=True, preprocessor=preprocess_string, norm=None)

    for node in leaf_nodes:
        #-- process text nodes
        # if it is text node with value
        if node['type'] == 3 and 'value' in node:
            position = node['position']
            size = [(position[2]-position[0])*(position[3]-position[1])]
              
            # get text - remove whitespaces, lowercase
            text = node['value']
            text = ' '.join(text.lower().split())
            encoded_text = vectorizer.transform([text])

            if len(encoded_text.nonzero()[0]) > 0:
                text_nodes.append((position,encoded_text,size))

    # ORDER TEXT NODES BY SIZE
    text_nodes.sort(key=lambda x: x[2], reverse=True)  

    return text_nodes

def get_text_maps(text_nodes, n_features, spatial_shape, text_map_scale):
    # scale down spatial dimensions
    features = np.zeros((round((spatial_shape[0]*text_map_scale)),round((spatial_shape[1]*text_map_scale)), n_features), dtype=np.float)
    
    # for each node in text nodes
    for node in text_nodes:
        bb = node[0]
        bb_scaled = [int(round(x*text_map_scale)) for x in bb]
        encoded_text = node[1]
        encoded_text = normalize(encoded_text, axis=1, norm='l2')
        encoded_text = encoded_text*255   # we multiply by 255 in order to move to image scale
        vector = np.asarray(encoded_text.todense())[0]
        features[bb_scaled[1]:bb_scaled[3],bb_scaled[0]:bb_scaled[2],:] = vector
    return features
