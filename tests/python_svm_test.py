import unittest

from blb import BLB

from asp.avro_inter.py_avro_inter import *

class SVMPythonEmailVerifierBLB(BLB):
    def compute_estimate(btstrap_data):
        models = btstrap_data.models
        errors =0.0
        num_feature_vecs = 0
        num_models = len(models)
        for feature_vec in feature_vecs:
            weight = feature_vec.weight
            num_feature_vecs += weight
            tag = feature_vec.tag
            choice = 0
            max_match = -1.0
            for i in range(num_models):
                model = models[i]  
                total = custom_dot(model, feature_vec)
                if total > max_match:
                    choice = i + 1
                    max_match = total    
            if choice != tag:
                errors += weight                
        return errors / num_feature_vecs
    
    #calculates average error estimate
    def reduce_bootstraps(bootstraps):
        mean = 0.0
        for bootstrap in bootstraps:
            mean += bootstrap
        return mean / len(bootstraps)
    
    """
    #calculates stddev on error estimates
    def reduce_bootstraps(bootstraps):
        mean = 0.0
        for bootstrap in bootstraps:
            mean += bootstrap
        mean = mean / len(bootstraps)
        squared_dif =0.0
        for bootstrap in bootstraps:           
            squared_dif += (mean-bootstrap) * (mean-bootstrap)
        return (squared_dif  / (len(bootstraps)-1)) ** .5
    """
        
    def average(subsamples):
        mean = 0.0
        for subsample in subsamples:
            mean += subsample
        return mean/len(subsamples)

class SVMVerifierBLBTest(unittest.TestCase):

    def test(self): 
        test_blb = SVMPythonEmailVerifierBLB(25, 50, .7, with_scala=True)    
        result = test_blb.run('/root/test_examples/data/seq_test',\
                              '/root/test_examples/models/train_model.avro')
        print 'FINAL RESULT IS:', result  


if __name__ == '__main__':
    unittest.main()


