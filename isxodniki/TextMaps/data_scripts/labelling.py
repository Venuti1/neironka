import os
import cv2
import sys
import json
import copy
import pickle
import random
from custom_layers.dom_tree import DOMTree
import matplotlib.pyplot as plt

FIGURE_WIDTH = 14
FIGURE_HEIGHT = 10
MAX_LABELED = 500

DOWNLOADED_PAGES_LIST_PATH = '../data_shops/downloaded_pages/'
LABELED_DOM_PATH =  '../data_shops/labeled_dom_trees/'
IMAGES_PATH = '../data_shops/images/'
DOM_PATH = '../data_shops/dom_trees/'
PATHS_PATH = '../data_shops/element_paths/'

#----- CLASS FOR SELECTING A NODE
class ElementSelector:

    selected_patch = None

    def __init__(self, image_path, dom_tree):
        self.image_path = image_path
        self.dom_tree = dom_tree

    def onPick(self, event):
        # change back old selected page
        if self.selected_patch:
            self.selected_patch.set_linewidth(1)

        # new selected patch
        self.selected_patch = event.artist

        # draw
        self.selected_patch.set_linewidth(4)
        self.selected_patch.figure.canvas.draw()

    def keyPress(self, event):
        if event.key == 'enter':
            plt.close()

    def selectElement(self):
        ## CROP IMAGE
        crop_top = 900
        self.fig = plt.figure(figsize=(FIGURE_WIDTH,FIGURE_HEIGHT))
        im = cv2.imread(self.image_path)
        im = im[:crop_top,:,:]

        plt.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        patches = []


        # for each leaf node
        for leafNode in self.dom_tree.getPositionedLeafNodes():
            position = leafNode['position']

            # text nodes have different color (just for sanity checks)
            if leafNode['type']==3:
                patch = plt.Rectangle((position[0], position[1]), position[2]-position[0],position[3]-position[1], fill=False, edgecolor='g', linewidth=1, picker=5)
            else:    
                patch = plt.Rectangle((position[0], position[1]), position[2]-position[0],position[3]-position[1], fill=False, edgecolor='b', linewidth=1, picker=5)
            
            patch.node = leafNode
            
            # compute size
            size = (position[2]-position[0])*(position[3]-position[1])
            # add to patch list
            patches.append((patch,size))

        patches.sort(key=lambda tup: tup[1], reverse=True)  # sorts in place
        for (patch,size) in patches:
            plt.gca().add_patch(patch)

        self.fig.canvas.mpl_connect('pick_event', self.onPick)
        self.fig.canvas.mpl_connect('key_press_event', self.keyPress)
        plt.show()

        if self.selected_patch:
            return self.selected_patch.node
        else:
            return None

def findAndLabel(page, main_image_paths, name_paths, price_paths):
    # get dom
    dom = getPageDOM(page)

    # find elements
    image_element = dom.getElementByOneOfPaths(main_image_paths)
    name_element = dom.getElementByOneOfPaths(name_paths)
    price_element = dom.getElementByOneOfPaths(price_paths)

    # if we have all elements
    if image_element and name_element and price_element:
        image_element['label'] = 'main_image'
        name_element['label'] = 'name'
        price_element['label'] = 'price'

        dom.saveTree(os.path.join(LABELED_DOM_PATH, page+'.json'))
        return True

    # if we do not have all
    else:
        return False

def loadPaths(prefix):
    print 'Loading paths'
    price_paths = []
    main_image_paths = []
    name_paths = []
    path_to_saved_path = os.path.join(PATHS_PATH, prefix+'.pkl')
    if os.path.exists(path_to_saved_path):
        paths = pickle.load(open(path_to_saved_path,'rb'))
        price_paths = paths['price']
        main_image_paths = paths['main_image']
        name_paths = paths['name']

    return price_paths, main_image_paths, name_paths

def savePaths(prefix, main_image_paths, name_paths, price_paths):
    paths = {}
    paths['price'] = price_paths
    paths['main_image'] = main_image_paths
    paths['name'] = name_paths
     
    path_to_saved_path = os.path.join(PATHS_PATH, prefix+'.pkl')
    pickle.dump(paths, open(path_to_saved_path,'wb+'))


def getUnlabeledPages(pages):
    print 'Getting unlabed pages'

    unlabeled = []
    labeled_count=0
    for page in pages:
        path = os.path.join(LABELED_DOM_PATH,page+'.json')
        if os.path.exists(path):
            labeled_count+=1
        else:
            unlabeled.append(page)
            
    print 'Unlabeled count:', len(unlabeled)
    print 'Labeled count:', labeled_count
    return unlabeled

def getPageDOM(page):
    dom_path = os.path.join(DOM_PATH,page+'.json')
    return DOMTree(dom_path)

def selectNewPaths(image_path, dom):
    selector = ElementSelector(image_path,dom)
    element = selector.selectElement()
    if element:
        return dom.getPaths(element)
    else:
        return []


def getNewPaths(pages, im_paths, name_paths, price_paths):
    updatedPath = False

    # untile we have no upadted path
    while not updatedPath:
        random_page = random.choice(pages)
        dom = getPageDOM(random_page)
        page_image_path = os.path.join(IMAGES_PATH,random_page+'.jpeg')
        displayQuestion=True

        new_price_paths = []
        new_name_paths = []
        new_image_paths = []

        # try to get price
        price_element = dom.getElementByOneOfPaths(price_paths)
        if price_element is None and displayQuestion:
            print 'Help me to find price:'
            new_price_paths = selectNewPaths(page_image_path, dom)
            if len(new_price_paths)>0:
                updatedPath=True
            else:
                displayQuestion=False

        # try to get name
        name_element = dom.getElementByOneOfPaths(name_paths)
        if name_element is None and displayQuestion:
            print 'Help me to find name:'
            new_name_paths = selectNewPaths(page_image_path, dom)
            if len(new_name_paths)>0:
                updatedPath=True
            else:
                displayQuestion=False

        # try to get image
        image_element = dom.getElementByOneOfPaths(im_paths)
        if image_element is None and displayQuestion:
            print 'Help me to find image:'
            new_image_paths = selectNewPaths(page_image_path, dom)
            if len(new_image_paths)>0:
                updatedPath=True
            else:
                displayQuestion=False

    return new_price_paths, new_image_paths, new_name_paths

#----- MAIN PART
if __name__ == "__main__":

    # read params
    if len(sys.argv) != 2:
        print 'BAD PARAMS. USAGE [prefix]'
        sys.exit(1)
    
    prefix = sys.argv[1]

    # prepare output path
    if not os.path.exists(LABELED_DOM_PATH):
        os.makedirs(LABELED_DOM_PATH)
    if not os.path.exists(PATHS_PATH):
        os.makedirs(PATHS_PATH)

    # load pages
    pages_path = os.path.join(DOWNLOADED_PAGES_LIST_PATH, prefix+'.txt')
    with open(pages_path,'r') as f:
        pages = [line.split('\t')[0] for line in f.readlines()]

    # try to load paths to elements
    price_paths, main_image_paths, name_paths = loadPaths(prefix)
    
    # split pages to already labeled or unlabeled
    unlabeled_pages = getUnlabeledPages(pages)

    total_labeled_count = len(pages)-len(unlabeled_pages)
    # until there are some unlabeled_pages
    while len(unlabeled_pages)>0:

        # get new paths
        print 'Get new paths'
        new_price_paths, new_image_paths, new_name_paths  \
            = getNewPaths(unlabeled_pages, main_image_paths, name_paths, price_paths)

        # update existing paths
        print 'Updating paths'
        price_paths.extend(new_price_paths)
        main_image_paths.extend(new_image_paths)
        name_paths.extend(new_name_paths)

        # save new updated paths
        print 'Saving new paths'
        savePaths(prefix,  main_image_paths, name_paths, price_paths)

        # try to annotate page
        print 'Annotating other pages'

        #succeded_count = 0
        new_unlabeled_pages = []
        for page in unlabeled_pages:
            success = findAndLabel(page, main_image_paths, name_paths, price_paths)
            if success:
                print total_labeled_count, page
                total_labeled_count += 1
            else:
                new_unlabeled_pages.append(page)

            if total_labeled_count>=MAX_LABELED:
                break

        # print result
        print "Successfully labeled", total_labeled_count, 'pages.'
        print "Unlabeled pages", len(new_unlabeled_pages), 'pages.'
   
        unlabeled_pages = new_unlabeled_pages
        
        # check maximum threshold
        if total_labeled_count>=MAX_LABELED:
            print "Maximum number of labeled examples achieved"
            break
