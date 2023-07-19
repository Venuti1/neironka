import os
import sys
from sklearn.cross_validation import KFold

RESULT_PATH = '../data_shops/page_sets/splits/'
PAGE_SETS_PATH = '../data_shops/page_sets/'
SHOP_LIST_PATH = '../data_shops/shop_list.txt'

def getPagesForShops(shops):
    pages = []
    for shop in shops:
        page_set_path = os.path.join(PAGE_SETS_PATH,shop)
        with open(page_set_path, 'r') as f:
            shop_pages = [l.strip() for l in f.readlines()]
            pages.extend(shop_pages)

    return pages


def createListFile(filename, pages):
    # for each page
    lines = []
    for page in pages:
        line=page
        lines.append(line)

    with open(os.path.join(RESULT_PATH, filename),'w') as f:
        for line in lines:
            f.write(line+'\n')

#----- MAIN PART
if __name__ == "__main__":
    # read shop list
    with open(SHOP_LIST_PATH, 'r') as f:
        shops = [l.strip() for l in f.readlines()]
    

    kf = KFold(len(shops), n_folds=10)
    
    split_num=1
    for train_index, test_index in kf:
        train_shops = [shops[i] for i in train_index]
        test_shops = [shops[i] for i in test_index]

        # get pages
        train_pages = getPagesForShops(train_shops)
        test_pages = getPagesForShops(test_shops)
  
        createListFile('split_'+str(split_num)+'_train.txt',train_pages)
        createListFile('split_'+str(split_num)+'_test.txt',test_pages)
        split_num+=1

