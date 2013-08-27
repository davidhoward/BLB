import unittest
from blb import BLB
from asp.avro_inter.py_avro_inter import *
import os

class SVMMultimediaVerifierBLB(BLB):
    TYPE_DECS = (['compute_estimate', [('array', ('array', ('array','double')))], ('array', 'double')],
         ['reduce_bootstraps', [('array', ('array', 'double'))], ('array','double')],
         ['average', [('array', ('array','double'))], ('array', 'double')],
         ['run', [('array', ('array','double'))], ('list','double')])

    #computes EER from scores 
    def compute_estimate(self,scores):
        num_classes = len(scores)

        thresholds = [0.0] * num_classes
        correct_under_thresh = [0] * num_classes
        incorrect_under_thresh = [0] * num_classes
        num_correct = [0] * num_classes
        num_incorrect = [0] * num_classes
        FA = [0.0] * num_classes
        MD = [0.0] * num_classes

        for i in range(num_classes):
            scores[i].sort()
            # begin with threshold at lowest score for each class
            thresholds[i] = scores[i][0]

            #assuming here that if on threshold, classified as positive
            if thresholds[i][1] == 1:
                correct_under_thresh[i] += 1
            else:
                incorrect_under_thresh[i] += 1

            for score in scores[i]:
                if score[1] == 1:
                    num_correct[i] += 1
                else:
                    num_incorrect[i] += 1                    
            MD[i] = correct_under_thresh[i]  * 1.0 / num_correct[i]
            FA[i] = (num_incorrect[i]-incorrect_under_thresh[i]) *1.0 / num_incorrect[i]

        EERs =[0.0] * num_classes
        for i in range(num_classes):
            count = 0
            while FA[i] > MD[i]:
                if thresholds[i][1] == 1:
                    correct_under_thresh[i] += 1
                else:
                    incorrect_under_thresh[i] += 1
                FA[i] = (num_incorrect[i]-incorrect_under_thresh[i]) * 1.0 / num_incorrect[i]
                MD[i] =correct_under_thresh[i] * 1.0 / num_correct[i]
                thresholds[i] = scores[i][count]
                count += 1

            EERs[i] = (FA[i] + MD[i])/2.0
        return EERs

    def std_dev(self, arr):
        from numpy import std
        return std(arr)

    def mean(self, arr):
        from numpy import mean
        return mean(arr) 

    #computes std dev
    def reduce_bootstraps(self,bootstraps):
        class_md_ratios = [0.0] * len(bootstraps)
        std_dev_md_ratios = [0.0] * len(bootstraps[0])
        for i in range(len(bootstraps[0])):
            count = 0
            for md_ratios in bootstraps:
                class_md_ratios[count] = md_ratios[i] 
                count += 1 
            #std_dev_md_ratios[i] = scala_lib.std_dev(class_md_ratios)
            std_dev_md_ratios[i] = self.mean(class_md_ratios)
        return std_dev_md_ratios


    def average(self,subsamples):
        class_std_dev_md_ratios = [0.0] * len(subsamples)
        avg_std_dev_md_ratios = [0.0] * len(subsamples[0])
        for i in range(len(subsamples[0])):
            count = 0
            for md_ratios in subsamples:
                class_std_dev_md_ratios[count] = md_ratios[i] 
                count += 1 
            #avg_std_dev_md_ratios[i] = scala_lib.mean(class_std_dev_md_ratios)
            avg_std_dev_md_ratios[i] = self.mean(class_std_dev_md_ratios)
        return avg_std_dev_md_ratios

class MultimediaClassifierVerificationBLBTest(unittest.TestCase):
    def test_multimedia_classifier(self): 
        test_blb = SVMMultimediaVerifierBLB(30, 100, .9, pure_python=True)  
        SCORES_DIR='/home/eecs/peterbir/blb/test_data/150k/'  
        event_scores = self.read_event_scores(SCORES_DIR)
        result = test_blb.run(event_scores)
        print 'FINAL RESULT IS:', result  

    def read_event_scores(self, scores_dir):
        file_list = os.listdir(scores_dir)
        event_scores = [0.0] * len(file_list)
        event_count=0
        for f in file_list:
            lines = open(scores_dir+f).readlines()
            event_scores[event_count] = [0.0] * len(lines)
            score_count = 0
            for score in lines:
                score = score.strip().split(' ')
                if int(score[0]) == 0:
                    event_scores[event_count][score_count] = [float(score[1]), 0]
                else:
                    event_scores[event_count][score_count] = [float(score[1]), 1]
                score_count += 1

            event_count += 1
        return event_scores

if __name__ == '__main__':
    spark_test_suite = unittest.TestSuite()
    spark_test_suite.addTest(MultimediaClassifierVerificationBLBTest('test_multimedia_classifier'))
    unittest.TextTestRunner().run(spark_test_suite)


