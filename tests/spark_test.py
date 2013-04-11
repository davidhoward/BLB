import unittest

from blb import BLB
from Queue import PriorityQueue
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
    #calculates number of missed detections for all classes 
    def compute_estimate(btstrap_data):
        models = btstrap_data.models
        num_models = len(models)
        class_occurrences = [0] * num_models
        missed_detections= [0] * num_models
        class_thresholds = [0] * num_models
        class_scores = [0.0] * num_models
        for feature_vec in btstrap_data.data:
            tag = feature_vec.tag
            weight = feature_vec.weight
            class_occurrences[tag] += weight
            choice = 0
            max_match = -1.0
            for i in range(num_models):
                model = models[i]  
                first = True
                class_scores[i] = 0.0
                for sub_model in model:
                    if first: 
                        class_thresholds[i] = sub_model[0]
                        first = False
                    else:
                        class_scores[i] += custom_dot_uncompressed(sub_model, feature_vec)
                if (class_scores[i] < thresholds[i] and tag == i):
                    missed_detections[tag] += weight

        return [md_count *1.0 / occurrences for md_count, occurrences in zip(missed_detections, class_occurrences)]

    #should change this to take standard deviation 
    def reduce_bootstraps(bootstraps):
        md_percent_sums = [0.0] * len(bootstraps[0])
        for bootstrap in bootstraps:
            for i in range(len(bootstrap)):
                md_percent_sums[i] += bootstrap[i]
        return [md_percent_sum *1.0 / len(bootstraps) for md_percent_sum in md_percent_sums]
        
    def average(subsamples):
        md_percent_sums = [0.0] * len(bootstraps[0])
        for bootstrap in bootstraps:
            for i in range(len(bootstrap)):
                md_percent_sums[i] += bootstrap[i]
        return [md_percent_sum *1.0 / len(bootstraps) for md_percent_sum in md_percent_sums]

class NGramRatiosBLB(BLB):
    def compute_estimate(btstrap_data):
        """
        get total occurrences per decade 
        calculate top 50 ratios

        assume btstrap_data contains rows 
        should i make each sample contain all of an NGram
            or just allow parts of it (year ?)
        should probably make all of an ngram part of it
            because otherwise will hardly be able to compare 
            any words 
        thus each row will be of the format
        ngram\tyear occurrences\tyear occurrences\tyear occurrences ...
        """
        #should take out dependency on 11 and 12 to var at beginning 
        #obtain total number of occurrences per decade 
        BEGINNING_DECADE = 1890
        TOTAL_DECADES = (2010-BEGINNING_DECADE)/10
        NUM_TOP_RATIOS = 50

        ngram_tab_split = []
        year_split = []
        ngram = ""
        decade_total_occurrences  = [0.0] * TOTAL_DECADES
        decadeIndex = 0
        for ngram_row in btstrap_data:
            ngram_tab_split = ngram_row.split("\t")
            ngram = ngram_tab_split[0]
            for year_count in ngram_tab_split[1:]
                year_split = year_count.split(' ')
                year = int(year_split[0])
                occurrences = int(year_split[1])
                if year >= BEGINNING_DECADE:
                    decadeIndex = int((year/ 100.0 - BEGINNING_DECADE/10.0) * 10.0)
                    decade_total_occurrences[decadeIndex] += occurrences

        #now get top ratios 
        #don't need to put (word, ratio) in queue, just ratio 
        MIN_FREQUENCY_THRESH = 0.000001
        top_n_ratios_per_decade = [] 
        for i in range(TOTAL_DECADES-1):
            top_n_ratios_per_decade.append(PriorityQueue())
        decade_ratio_mins = [0.0] * (TOTAL_DECADES-1)
        ngram_decade_frequency = [0.0] * TOTAL_DECADES
        ngram_decade_occurrences = [0] * TOTAL_DECADES
        decade_count =0
        ratio = 0.0

        for ngram_row in btstrap_data:
            ngram_tab_split = ngram_row.split("\t")
            for year_count in ngram_tab_split[1:]
                year_split = year_count.split(' ')
                year = int(year_split[0])
                occurrences = int(year_split[1])
                if year >= BEGINNING_DECADE:
                    decadeIndex = int((year/ 100.0 - BEGINNING_DECADE/10.0) * 10.0)
                    ngram_decade_occurrences[decadeIndex] += occurrences 

            for decadeIndex in range(1,len(decade_total_occurrences)):
                if (decade_total_occurrences[decadeIndex] > 0 and decade_total_occurrences[decadeIndex-1] > 0 and ngram_decade_occurrences[decadeIndex] > 0 and ngram_decade_occurrences[decadeIndex] / ngram_decade_occurrences[decadeIndex] > MIN_FREQUENCY_THRESH):
                    ratio = (ngram_decade_occurrences[decadeIndex] / decade_total_occurrences[decadeIndex]) / (ngram_decade_occurrences[decadeIndex-1] / decade_total_occurrences[decadeIndex-1]) 
                    
                    if ratio > decade_ratio_mins(decadeIndex-1) or top_n_ratios_per_decade[decadeIndex-1].qsize() < NUM_TOP_RATIOS:
                        PriorityQueue.put(top_n_ratios_per_decade[decadeIndex-1], ratio)

                        if (top_n_ratios_per_decade[decadeIndex-1].qsize() >= NUM_TOP_RATIOS):
                            PriorityQueue.get(top_n_ratios_per_decade[decadeIndex-1])
                        lowest_ratio = PriorityQueue.get(top_n_ratios_per_decade[decadeIndex-1])
                        decade_ratio_mins[decadeIndex-1] = lowest_ratio
                        PriorityQueue.put(top_n_ratios_per_decade[decadeIndex-1], lowest_ratio)

            ngram_decade_occurrences = [0.0] * TOTAL_DECADES

        #will need to convert priority queue to array here  
        return top_n_ratios_per_decade

    def reduce_bootstraps(bootstraps):
        #find median ratio ?
        pass

    def average(subsamples):
        pass

class SVMVerifierBLBTest(unittest.TestCase):
    def test_feature_vec_classifier(self): 
        test_blb = SVMEmailVerifierBLB(25, 50, .7, with_scala=True)    
        result = test_blb.run('/root/test_examples/data/seq_test',\
                              '/root/test_examples/models/train_model.avro')
        print 'FINAL RESULT IS:', result  

    def test_multimedia_classifier(self): 
        test_blb = SVMMultimediaVerifierBLB(25, 50, .7, with_scala=True)    
        result = test_blb.run('/root/test_examples/data/e1-15seq',\
                              '/root/test_examples/models/e1-15.model.java')
        print 'FINAL RESULT IS:', result  

    def test_ngram_ratio_calculator(self):
        test_blb = SVMMultimediaVerifierBLB(25, 50, .7, with_scala=True)
        result = test_blb.run()
        print 'FINAL RESULT IS:', result  


if __name__ == '__main__':
    spark_test_suite = unittest.TestSuite()
    #spark_test_suite.addTest(SVMVerifierBLBTest('test_feature_vec_classifier))
    spark_test_suite.addTest(SVMVerifierBLBTest('test_multimedia_classifier'))
    unittest.TextTestRunner().run(spark_test_suite)

