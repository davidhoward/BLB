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
    def compute_estimate(scores):
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
            if num_incorrect[i] > 0:
                MD[i] = correct_under_thresh[i]  * 1.0 / num_incorrect[i]
            else:
                 MD[i] = 0.0
            FA[i] = (num_incorrect[i] - incorrect_under_thresh[i]) *1.0 / num_incorrect[i]

        EERs =[0.0] * num_classes
        for i in range(num_classes):
            count = 0
            while FA[i] > MD[i]:
                if thresholds[i][1] == 1:
                    correct_under_thresh[i] += 1
                else:
                    incorrect_under_thresh[i] += 1
                FA[i] = (num_incorrect[i]-incorrect_under_thresh[i]) * 1.0 / num_incorrect[i]

                if num_correct[i] > 0:
                    MD[i] = correct_under_thresh[i] * 1.0 / num_correct[i]
                else:
                    MD[i] = 0.0

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
    def reduce_bootstraps(bootstraps):
        class_md_ratios = [0.0] * len(bootstraps)
        std_dev_md_ratios = [0.0] * len(bootstraps[0])
        for i in range(len(bootstraps[0])):
            count = 0
            for md_ratios in bootstraps:
                class_md_ratios[count] = md_ratios[i] 
                count += 1 
            std_dev_md_ratios[i] = scala_lib.std_dev(class_md_ratios)
            # std_dev_md_ratios[i] = self.std_dev(class_md_ratios)
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
            # avg_std_dev_md_ratios[i] = self.mean(class_std_dev_md_ratios)
        return avg_std_dev_md_ratios

class SVMMultimediaComputeScoresBLB(BLB):
    TYPE_DECS = (['compute_estimate', [('array', 'FeatureVec'), ('array', ('array', ('array','float')))], ('array', 'float')],
         ['reduce_bootstraps', [('array', ('array', 'float'))], ('array','float')],
         ['average', [('array', ('array','float'))], ('array', 'float')],
         ['run', [('array', ('array','float'))], ('list','float')])

    def dot(self, x,y):
        sum = 0.0
        for i in range(len(x)):
            sum += x[i] * y[i]
        return sum

    def compute_estimate(self, feature_vecs, models, feature_vec_weights):
        num_classes = len(models)
        # this doesn't work in real python because will just copy reference to same array ...
        # CHANGE TO THIS IN SPARK VERSION 
        # file_scores = [[0.0] * len(feature_vecs)] * num_classes
        # use this in actual Python; unsure if this works in conversion 
        file_scores = [[0.0 for x in range(len(feature_vecs))] for x in range(num_classes)] 
        
        file_tags = [0] * len(feature_vecs)
        file_index = 0
        tag = 0

        #compute score for each file
        for feature_vec in feature_vecs:
            # CHANGE TO THIS IN SPARK VERSION 
            # tag = feature_vec.tag
            tag = feature_vec[0]
            file_tags[file_index] = tag 

            for i in range(num_classes):
                # CHANGE TO THIS IN SPARK VERSION 
                # if feature_vec.weight > 0:
                if feature_vec_weights[file_index] > 0:
                    model = models[i]
                    class_score = 0.0
                    for sub_model in model:
                        class_score += self.dot(sub_model, feature_vec)
                    file_scores[i][file_index] = class_score
            file_index += 1

        ######### now compute EERS from scores
        print 'scores 0 0 is:', file_scores[0][0]
        scores = self.convert_scores(file_scores, file_tags)
        return self.compute_EERs(scores)

    def convert_scores( self, file_scores, file_tags ):
        """
        in format:
        [ [xxx...] , [xxx...] , [xxx...] .. ]

        out format:
        [ [[0,x], [0,x], [1,x],..], [[0,x], [0,x], [1,x],..], [[0,x], [0,x], [1,x],..], .. ]
        """
        num_classes = len(file_scores)
        num_files = len(file_tags)
        scores = [[[0,0.0] for x in range(num_files)] for x in range(num_classes)] 
        for i in range(num_files):
            tag = file_tags[i]
            class_count = 0
            for j in range(6,16)+range(21,31):
                if tag == j:
                    scores[class_count][i] = [1, file_scores[class_count][i]]
                else:
                    scores[class_count][i] = [0, file_scores[class_count][i]]
                class_count += 1
        return scores 

    def compute_EERs(self, scores ):
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

            if num_incorrect[i] > 0:
                MD[i] = correct_under_thresh[i]  * 1.0 / num_incorrect[i]
            else:
                 MD[i] = 0.0

            FA[i] = (num_incorrect[i]-incorrect_under_thresh[i]) *1.0 / num_incorrect[i]

        EERs =[0.0] * num_classes
        for i in range(num_classes):
            count = 0
            while FA[i] > MD[i]:
                # print 'one iter in while'
                if thresholds[i][1] == 1:
                    correct_under_thresh[i] += 1
                else:
                    incorrect_under_thresh[i] += 1
                FA[i] = (num_incorrect[i]-incorrect_under_thresh[i]) * 1.0 / num_incorrect[i]
                if num_correct[i] > 0:
                    MD[i] = correct_under_thresh[i] * 1.0 / num_correct[i]
                else:
                    MD[i] = 0.0                
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
    def test_short_multimedia_classifier(self): 
        test_blb = SVMMultimediaVerifierBLB(1, 1, .9, with_scala=True)  
        # SCORES_DIR='/Users/pbirsinger/Research/blb/data/test_icsi/kindred/blb_full/'
        # SCORES_DIR='/Users/pbirsinger/Research/blb/data/test_icsi/med/blb_full/'
        SCORES_DIR='/mnt/test_examples/data/med_scores/'
        event_scores = self.read_event_scores(SCORES_DIR)
        result = test_blb.run(*event_scores)
        print 'FINAL RESULT IS:', result  
        print 'scores dir is:', SCORES_DIR

    def test_long_multimedia_classifier(self): 
        test_blb = SVMMultimediaComputeScoresBLB(1, 1, .9, with_scala=True)  
        feature_vec_filename='/Users/pbirsinger/Research/blb/data/test_icsi/med/test_med.svmdat'
        models_dir='/Users/pbirsinger/Research/blb/data/test_icsi/med/models/'
        models = self.read_models(models_dir)
        test_feature_vecs = self.read_feature_vecs(feature_vec_filename)
        result = test_blb.run(test_feature_vecs, models)

        print 'FINAL RESULT IS:', result  
        print 'scores dir is:', SCORES_DIR

    def read_feature_vecs(self, filename):
        lines = open(filename).readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].strip().split(' ')
            lines[i][0] = int(lines[i][0])
            for j in range(1, len(lines[i])):
                lines[i][j] = float(lines[i][j].split(':')[1])
        return lines 

    def read_models(self, dir):
        models = [ 0.0 ] * 20
        file_count = 0
        for i in range(6,16)+range(21,31):
            models[file_count] = []
            line_count = 1
            for line in open(dir+'model'+str(i)):
                if line_count > 11:  
                    support_vec = line.strip().split(' ')[0:-1]
                    support_vec[0] = float(support_vec[0])
                    for j in range(1, len(support_vec)):
                        support_vec[j] = float(support_vec[j].split(':')[1])
                    models[file_count].append(support_vec)
                line_count += 1
            file_count += 1
        return models
            
    def read_event_scores(self, scores_dir):
        file_list = os.listdir(scores_dir)
        event_scores = [0.0] * len(file_list)
        event_count=0
        for i in range(6,16)+range(21,31):
            lines = open(scores_dir+'out'+str(i)).readlines()
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
    spark_test_suite.addTest(MultimediaClassifierVerificationBLBTest('test_short_multimedia_classifier'))
    # spark_test_suite.addTest(MultimediaClassifierVerificationBLBTest('test_long_multimedia_classifier'))
    unittest.TextTestRunner().run(spark_test_suite)


