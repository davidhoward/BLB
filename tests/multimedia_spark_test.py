import unittest
from blb import BLB
from asp.avro_inter.py_avro_inter import *
import os

class SVMMultimediaVerifierBLB(BLB):
    TYPE_DECS = (['compute_estimate', [('array', 'FeatureVec'), ('array', ('array', ('array','double')))], ('array', 'double')],
         ['reduce_bootstraps', [('array', ('array', 'double'))], ('array','double')],
         ['average', [('array', ('array','double'))], ('array', 'double')],
         ['run', [('array', ('array','double'))], ('list','double')])

    def compute_estimate(feature_vecs, models):
        num_classes = len(models)
        file_scores = [[0.0] * len(feature_vecs)] * num_classes
        file_tags = [0] * len(feature_vecs)
        file_index = 0
        tag = 0

        #compute score for each file 
        for feature_vec in feature_vecs:
            tag = feature_vec.tag
            file_tags[file_index] = tag 
            for i in range(num_classes):
                if feature_vec.weight > 0:
                    model = models[i]
                    class_score = 0.0
                    for sub_model in model:
                        class_score  += HelperFuncs.dot(sub_model, feature_vec)
                    file_scores[i][file_index] = class_score
            file_index += 1

        #compute threshold for each class s.t. FA <= 5% for each class
        TARGET_FA_RATE = .05
        file_index = 0
        class_index = 0
        class_thresholds = [0.0] * num_classes
        num_negative = 0
        for class_scores in file_scores:
            negative_scores = [[0.0, 0.0]] * len(feature_vecs)
            file_index = 0
            negative_index = 0
            total_negative = 0.0
            for score in class_scores:
                tag = file_tags[file_index]
                if tag != class_index+1:
                    weight = feature_vecs[file_index].weight
                    negative_scores[negative_index] = [score, weight]
                    negative_index += 1
                    total_negative += weight
                file_index += 1 
            
            negative_scores = negative_scores[0:negative_index]
            negative_scores.sort()
            summed = 0.0
            negative_index = 0
            neg_score_pair = [0.0, 0.0]
            while (summed/ total_negative < (1.0 -TARGET_FA_RATE)):
                neg_score_pair = negative_scores[negative_index]
                summed += neg_score_pair[1]
                negative_index +=1
            class_thresholds[class_index] = neg_score_pair[0]

            class_index += 1

        #compute MD % for each class
        md_ratios = [0.0] * num_classes
        class_index = 0
        for class_scores in file_scores:
            md_total = 0
            class_occurrences = 0
            file_index = 0

            for score in class_scores:
                tag = file_tags[file_index]
                if tag == class_index+1:
                    class_occurrences += feature_vecs[file_index].weight
                    if score < class_thresholds[class_index]:
                        md_total += feature_vecs[file_index].weight
                file_index +=1
            if class_occurrences != 0:
                md_ratios[class_index] = md_total *1.0 / class_occurrences
            class_index += 1

        return md_ratios

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
        class_std_dev_md_ratios = [0.0] * len(subsamples)
        avg_std_dev_md_ratios = [0.0] * len(subsamples[0])
        for i in range(len(subsamples[0])):
            count = 0
            for md_ratios in subsamples:
                class_std_dev_md_ratios[count] = md_ratios[i] 
                count += 1 
            avg_std_dev_md_ratios[i] = scala_lib.mean(class_std_dev_md_ratios)
        return avg_std_dev_md_ratios

class MultimediaClassifierVerificationBLBTest(unittest.TestCase):
    def test_multimedia_classifier(self): 
        test_blb = SVMMultimediaVerifierBLB(4, 3, .85, with_scala=True)    
        result = test_blb.run(os.environ['HDFS_URL']+'/test_examples/data/full_test.svmdat',\
                              '/mnt/test_examples/models/med_supervec_model.double.java')
        print 'FINAL RESULT IS:', result  

if __name__ == '__main__':
    spark_test_suite = unittest.TestSuite()
    spark_test_suite.addTest(SVMVerifierBLBTest('test_multimedia_classifier'))
    unittest.TextTestRunner().run(spark_test_suite)

