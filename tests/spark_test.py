import unittest

from blb import BLB

from asp.avro_inter.py_avro_inter import *

class SVMVerifierBLB(BLB):
    def compute_estimate(btstrap_data):
        emails = btstrap_data.emails
        models = btstrap_data.models
        errors =0.0
        num_emails = 0
        num_models = len(models)
        for email in emails:
            weight = email.get_weight()
            num_emails += weight
            tag = email.get_tag()
            choice = 0
            max_match = -1.0
            for i in range(num_models):
                model = models[i]  
                total = custom_dot(model, email)
                if total > max_match:
                    choice = i + 1
                    max_match = total    
            if choice != tag:
                errors += weight                
        return errors / num_emails
    
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
            print 'squr dif is:', (mean-bootstrap) * (mean-bootstrap)
        return (squared_dif  / (len(bootstraps)-1)) ** .5
    """
        
    def average(subsamples):
        mean = 0.0
        for subsample in subsamples:
            mean += subsample
        return mean/len(subsamples)


class SVMVerifierBLBTest(unittest.TestCase):

    def test(self):
        test_blb = SVMVerifierBLB(25, 50, .6, with_scala=True)    
        result = test_blb.run('/root/enron_example/data/seq113ktest',\
                              '/root/enron_example/models/comp113kmodel.avro')
	#Note: Spark will likely hang after the completion of the calculation and the following line will not be reached
        print 'FINAL RESULT IS:', result  

if __name__ == '__main__':
    unittest.main()
