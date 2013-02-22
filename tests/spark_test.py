import unittest

from blb import BLB

from asp.avro_inter.py_avro_inter import *

class SVMEmailVerifierBLB(BLB):
    def compute_estimate(btstrap_data):
        feature_vecs = btstrap_data.data
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

class SVMMultimediaVerifierBLB(BLB):
    def compute_estimate(btstrap_data):
        models = btstrap_data.models
        errors =0.0
        num_feature_vecs = 0
        num_models = len(models)
        for feature_vec in btstrap_data.data:
            weight = feature_vec.weight
            num_feature_vecs += weight
            tag = feature_vec.tag
            choice = 0
            max_match = -1.0
            for i in range(num_models):
                model = models[i]  
                total = 0.0
                for sub_model in model:
                    total += custom_dot_uncompressed(sub_model, feature_vec)
                if total > max_match:
                    choice = i + 1
                    max_match = total
            #check to see if max_match < threshold ?
            # if so put in class 16    
            if choice != tag:
                errors += weight                
        return errors / num_feature_vecs
    #could instead calculate false positive to false negative rate for each model
    #calculates average error estimate
    # this should be that roc curve 
    def reduce_bootstraps(bootstraps):
        mean = 0.0
        for bootstrap in bootstraps:
            mean += bootstrap
        return mean / len(bootstraps)
        
    def average(subsamples):
        mean = 0.0
        for subsample in subsamples:
            mean += subsample
        return mean/len(subsamples)

class SVMVerifierBLBTest(unittest.TestCase):

    def test_feature_vec_classifier(self): 
        test_blb = SVMfeature_vecVerifierBLB(25, 50, .7, with_scala=True)    
        result = test_blb.run('/root/enron_example/data/seq_test',\
                              '/root/enron_example/models/train_model.avro')
        print 'FINAL RESULT IS:', result  

    def test_multimedia_classifier(self): 
        test_blb = SVMMultimediaVerifierBLB(25, 50, .7, with_scala=True)    
        result = test_blb.run('/root/enron_example/data/e1-15seq',\
                              '/root/enron_example/models/e1-15double.model.java')
        print 'FINAL RESULT IS:', result  

if __name__ == '__main__':
    spark_test_suite = unittest.TestSuite()
    #spark_test_suite.addTest(SVMVerifierBLBTest('test_feature_vec_classifier))
    spark_test_suite.addTest(SVMVerifierBLBTest('test_multimedia_classifier'))
    unittest.TextTestRunner().run(spark_test_suite)

