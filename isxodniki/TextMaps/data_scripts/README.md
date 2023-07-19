# Scripts used for downloading product pages

## Software needed

- phantomjs
- python

## Download product pages from eshop
Run following script:

```Shell
phantomjs download_shop.js [PREFIX]
#example: phantomjs download_shop.js www.grainger.com) 
```

## Semi-automatic labeling of DOM elements 
Run following script:

python labelling.py [prefix]

Script creates new directory "labeled_dom_trees" which contains copy of DOM trees with labeled elements.

## Review labeled results

We review labeled results by checking image patches of labeled elements. The process is divided into 3 steps - prepare labeled patches, review them, remove them.

### Step 1: Prepare patches
```Shell
python review.py prepare [prefix]
```

### Step 2: Review patches
```Shell
python review.py review [prefix]
```

You can select wrongly labeled patches, in order to remove page from dataset. If everything goes right, the script creates new file in "page_sets" directory,
which contains all pages that passed the review process.

### Step 3: Remove patches
```Shell
python review.py remove [prefix]
```

## Create boxes and text maps that enter neural net
```Shell
python create_net_inputs.py [prefix]
```
