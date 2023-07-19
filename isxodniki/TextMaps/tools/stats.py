import utils
import argparse
import numpy as np
import collections

#----- MAIN PART
if __name__ == "__main__":

    #--- Get params
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment', type=str, default=None, help='name of experiment', required=True)
    args = parser.parse_args()

    #-- Load params
    experiment = args.experiment


    results = {}
    n_splits = 10

    for i_split in range(1,n_splits+1):
        # path
        path = utils.get_result_path(experiment, str(i_split))
        with open(path,'r') as f:
            lines = [line.strip() for line in f.readlines()]

        for line in lines:
            # parse line
            parts = line.split(': ')
            if len(parts)==3:
                settings = parts[0]
                element = parts[1]
                value = float(parts[2])

                # if key does not exist add array
                key = settings+':'+element
                if key not in results:
                    results[key] = []

                # add value to array
                results[key].append(value)



    results = collections.OrderedDict(sorted(results.items()))

    for stats, values in results.iteritems():        
        print stats
        print np.mean(values), '+-', np.std(values)


