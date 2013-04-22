import unittest

from blb import BLB
from Queue import PriorityQueue
from asp.avro_inter.py_avro_inter import *

class SVMEmailVerifierBLB(BLB):

    TYPE_DECS = (['compute_estimate', ['BootstrapData'], 'double'],
         ['reduce_bootstraps', [('list', 'double')], 'double'],
         ['average', [('array', 'double')], 'double'])

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
                total = helperFuncs.custom_dot(model, feature_vec)
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

    TYPE_DECS = (['compute_estimate', ['BootstrapData'], ('array', 'double')],
         ['reduce_bootstraps', [('array', ('array', 'double'))], ('array','double')],
         ['average', [('array', ('array','double'))], ('array', 'double')],
         ['run', [('array', ('array','double'))], ('list','double')])

    #calculates missed detection percentage for all classes 
    def compute_estimate(btstrap_data):
        models = btstrap_data.models
        num_models = len(models)
        class_occurrences = [0] * num_models
        missed_detections= [0] * num_models
        class_thresholds = [0.0] * num_models
        class_scores = [0.0] * num_models
        for feature_vec in btstrap_data.data:
            tag = feature_vec.tag
            if tag > 0:
                weight = feature_vec.weight
                class_occurrences[tag-1] += weight
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
                            class_scores[i] += HelperFuncs.custom_dot_uncompressed(sub_model, feature_vec)
                    if (class_scores[i] < class_thresholds[i] and tag == i+1):
                        missed_detections[tag-1] += weight
        for i in range(len(class_occurrences)):
            if class_occurrences[i] == 0:
                class_occurrences[i] = 1
        return [md_count_occurrences_tup[0] *1.0 / md_count_occurrences_tup[1] for md_count_occurrences_tup in zip(missed_detections, class_occurrences)]

    # TYPE_DECS = (['compute_estimate', ['BootstrapData'], ('array', ('array', 'double'))],

    #      ['reduce_bootstraps', [('array', ('array', 'double'))], ('array','double')],
    #      ['average', [('array', ('array','double'))], ('array', 'double')],
    #      ['run', [('array', ('array','double'))], ('list','double')])

    #calculates missed detection AND false alarm percentage for all classes 
    # def compute_estimate(btstrap_data):
    #     models = btstrap_data.models
    #     num_models = len(models)
    #     class_occurrences = [0] * num_models
    #     missed_detections= [0] * num_models
    #     false_alarms= [0] * num_models
    #     class_thresholds = [0.0] * num_models
    #     class_scores = [0.0] * num_models
    #     total_files = 0.0
    #     for feature_vec in btstrap_data.data:
    #         tag = feature_vec.tag
    #         if tag < 16:
    #             class_occurrences[tag-1] += weight
    #         total_files += weight
    #         weight = feature_vec.weight
    #         choice = 0
    #         max_match = -1.0
    #         for i in range(num_models):
    #             model = models[i]  
    #             first = True
    #             class_scores[i] = 0.0
    #             for sub_model in model:
    #                 if first: 
    #                     class_thresholds[i] = sub_model[0]
    #                     first = False
    #                 else:
    #                     class_scores[i] += HelperFuncs.custom_dot_uncompressed(sub_model, feature_vec)
    #             if (class_scores[i] < class_thresholds[i] and tag == i+1):
    #                 missed_detections[tag-1] += weight
    #             elif (score >= thresholds[predicted_class-1] and tag != i+1):
    #                 false_alarms[tag-1] += weight

    #     md_rates = [md_count_occurrences_tup[0] *1.0 / md_count_occurrences_tup[1] for md_count_occurrences_tup in zip(missed_detections, class_occurrences)]
    #     fa_rates = [fa_count_occurrences_tup[0] *1.0 / (total_files - md_count_occurrences_tup[1]) for fa_count_occurrences_tup in zip(false_alarms, class_occurrences)]
    # might be better if i do tuples ?
    #     return zip(md_rates, fa_rates)


    #computes mean md_ratio
    # def reduce_bootstraps(bootstraps):
    #     md_percent_sums = [0.0] * len(bootstraps[0])
    #     for bootstrap in bootstraps:
    #         for i in range(len(bootstrap)):
    #             md_percent_sums[i] += bootstrap[i]
    #     return [md_percent_sum *1.0 / len(bootstraps) for md_percent_sum in md_percent_sums]

    #computes std dev

    def reduce_bootstraps(bootstraps):
        class_md_ratios = [0.0] * len(bootstraps)
        std_dev_md_ratios = [0.0] * len(bootstraps[0])
        for i in range(len(bootstraps[0])):
            count = 0
            for md_ratios in bootstraps:
                class_md_ratios[count] = md_ratios[i] 
                count += 1 
            std_dev_md_ratios[i] = scala_lib.std_dev(class_md_ratios)
        return std_dev_md_ratios

    def average(subsamples):
        md_percent_sums = [0.0] * len(subsamples[0])
        for subsample in subsamples:
            for i in range(len(subsample)):
                md_percent_sums[i] += subsample[i]
        return [md_percent_sum *1.0 / len(subsamples) for md_percent_sum in md_percent_sums]

class NGramRatiosBLB(BLB):

    TYPE_DECS = (['compute_estimate', [('list', 'NGramRow')], ('array', 'double')],
         ['reduce_bootstraps', [('array', ('array', 'double'))], ('array', 'double')],
         ['average', [('array', ('array','double'))], ('list','double')])


    def compute_estimate(btstrap_data):
        BEGINNING_DECADE = 1890
        TOTAL_DECADES = (2010-BEGINNING_DECADE)/10
        NUM_TOP_RATIOS = 50
        MIN_FREQUENCY_THRESH = 0.000001

        #obtain total number of occurrences per decade 
        ngram_tab_split=['']
        year_split=['']
        occurrences = 0.0
        year = 0

        decade_total_occurrences  = [0.0] * TOTAL_DECADES
        decadeIndex = 0
        for ngram_row in btstrap_data:
            ngram_tab_split = ngram_row.year_counts.split("\t")
            ngram = ngram_tab_split[0]
            for year_count in ngram_tab_split[1:len(ngram_tab_split)]:
                year_split = year_count.split(' ')
                year = int(year_split[0])
                occurrences = int(year_split[1]) * ngram_row.weight
                if year >= BEGINNING_DECADE:
                    decadeIndex = int((year/ 100.0 - BEGINNING_DECADE/100.0) * 10.0)
                    decade_total_occurrences[decadeIndex] += occurrences

        #obtain word frequency ratios between decades 
        top_n_ratios_per_decade = [PriorityQueue() for i in range(TOTAL_DECADES -1)]

        decade_ratio_mins = [0.0] * (TOTAL_DECADES-1)
        ngram_decade_frequency = [0.0] * TOTAL_DECADES
        ngram_decade_occurrences = [0.0] * TOTAL_DECADES

        for ngram_row in btstrap_data:
            ngram_tab_split = ngram_row.year_counts.split("\t")
            for year_count in ngram_tab_split[1:len(ngram_tab_split)]:
                year_split = year_count.split(' ')
                year = int(year_split[0])
                occurrences = int(year_split[1]) * ngram_row.weight
                if year >= BEGINNING_DECADE:
                    decadeIndex = int((year/ 100.0 - BEGINNING_DECADE/100.0) * 10.0)
                    ngram_decade_occurrences[decadeIndex] += occurrences 

            for decadeIndex in range(1,len(decade_total_occurrences)):
                if (decade_total_occurrences[decadeIndex] > 0 and decade_total_occurrences[decadeIndex-1] > 0 and ngram_decade_occurrences[decadeIndex-1] > 0 and ngram_decade_occurrences[decadeIndex] / decade_total_occurrences[decadeIndex] > MIN_FREQUENCY_THRESH):
                    ratio = (ngram_decade_occurrences[decadeIndex] / decade_total_occurrences[decadeIndex]) / (ngram_decade_occurrences[decadeIndex-1] / decade_total_occurrences[decadeIndex-1]) 
                    
                    if ratio > decade_ratio_mins[decadeIndex-1]:
                        while top_n_ratios_per_decade[decadeIndex-1].qsize() < NUM_TOP_RATIOS and ngram_row.weight > 0:
                            PriorityQueue.put(top_n_ratios_per_decade[decadeIndex-1], ratio)

                            if (top_n_ratios_per_decade[decadeIndex-1].qsize() >= NUM_TOP_RATIOS):
                                PriorityQueue.get(top_n_ratios_per_decade[decadeIndex-1])
                            lowest_ratio = PriorityQueue.get(top_n_ratios_per_decade[decadeIndex-1])
                            decade_ratio_mins[decadeIndex-1] = lowest_ratio
                            PriorityQueue.put(top_n_ratios_per_decade[decadeIndex-1], lowest_ratio)
                            ngram_row.weight -= 1

            ngram_decade_occurrences = [0.0] * TOTAL_DECADES
    
        decade_ratios_arr = [0.0] * (TOTAL_DECADES-1)
        count = 0
        for queue in top_n_ratios_per_decade:
            ratios_summed = 0.0
            for i in range(NUM_TOP_RATIOS): 
                if top_n_ratios_per_decade[count].qsize() > 0:
                    ratios_summed += PriorityQueue.get(top_n_ratios_per_decade[count])

            decade_ratios_arr[count] = ratios_summed / NUM_TOP_RATIOS
            count += 1
        return decade_ratios_arr

    def reduce_bootstraps(bootstraps):
        decade_ratios = [0.0] * len(bootstraps)
        std_dev_ratios = [0.0] * len(bootstraps[0])
        for i in range(len(bootstraps[0])):
            count = 0
            for cross_decades in bootstraps:
                decade_ratios[count] = cross_decades[i] 
                count += 1 
            std_dev_ratios[i] = scala_lib.std_dev(decade_ratios)
        return std_dev_ratios

    # def reduce_bootstraps(subsamples):
    #     decade_std_devs = [0.0] * len(subsamples)
    #     avg_std_dev_ratios = [0.0] * len(subsamples[0])
    #     for i in range(len(subsamples[0])):
    #         count = 0
    #         for cross_decades in subsamples:
    #             decade_std_devs[count] = cross_decades[i] 
    #             count += 1 
    #         avg_std_dev_ratios[i] = scala_lib.mean(decade_std_devs)
    #     return avg_std_dev_ratios     

    def average(subsamples):
        decade_std_devs = [0.0] * len(subsamples)
        avg_std_dev_ratios = [0.0] * len(subsamples[0])
        for i in range(len(subsamples[0])):
            count = 0
            for cross_decades in subsamples:
                decade_std_devs[count] = cross_decades[i] 
                count += 1 
            avg_std_dev_ratios[i] = scala_lib.mean(decade_std_devs)
        return avg_std_dev_ratios     

class SVMVerifierBLBTest(unittest.TestCase):
    def test_feature_vec_classifier(self): 
        test_blb = SVMEmailVerifierBLB(25, 50, .7, with_scala=True)    
        result = test_blb.run('/root/test_examples/data/seq_test',\
                              '/root/test_examples/models/train_model.avro')
        print 'FINAL RESULT IS:', result  

    def test_multimedia_classifier(self): 
        test_blb = SVMMultimediaVerifierBLB(25, 50, .7, with_scala=True)    
        result = test_blb.run('/mnt/test_examples/data/20percentE1-15.seq',\
                              '/mnt/test_examples/models/e1-15double.model.java')
        print 'FINAL RESULT IS:', result  

    def test_ngram_ratio_calculator(self):
        test_blb = NGramRatiosBLB(25, 50, .7, with_scala=True)
        result = test_blb.run('/mnt/test_examples/data/10_percent_cleaned_blb.seq')
        print 'FINAL RESULT IS:', result  

if __name__ == '__main__':
    spark_test_suite = unittest.TestSuite()
    #spark_test_suite.addTest(SVMVerifierBLBTest('test_feature_vec_classifier))
    spark_test_suite.addTest(SVMVerifierBLBTest('test_multimedia_classifier'))
    #spark_test_suite.addTest(SVMVerifierBLBTest('test_ngram_ratio_calculator'))
    unittest.TextTestRunner().run(spark_test_suite)

