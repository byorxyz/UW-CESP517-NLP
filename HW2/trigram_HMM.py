import re
import json
from collections import defaultdict
import os
import time
import math
import pandas as pd
from math import log
import numpy as np
from sklearn.metrics import confusion_matrix
from utils import *


def viterbi_tri(vocab, vocab_tag, words, tags, t_trigram_count, t_bigram_count, t_unigram_count, e_bigram_count, e_unigram_count, ADD_K):
	vocab_size = len(vocab)
	V = [{}]
	# Prob of very first word. 
	for t in vocab_tag:
		prob = np.log2(float(e_bigram_count.get((words[0],t),0)+ADD_K))-np.log2(float(e_unigram_count[t]+vocab_size*ADD_K))
		# trigram V[0][0]
		V[0][t] = {"prob": prob, "prev": None, "prev_prev": None} # None because it's the first word. 
	
	for i in range(1,len(words)):
		V.append({})
		#initialize
		for t in vocab_tag:
			V[i][t] =  {"prob": np.log2(0), "prev": None, "prev_prev": None}
		for t in vocab_tag:
			max_trans_prob = np.log2(0); # initialize max_trans_prob
			for prev_tag in vocab_tag:
				for penult_tag in vocab_tag:
					#transition probabilty for TAGS (not words!)
					trans_prob = np.log2(float(t_trigram_count.get((t, prev_tag, penult_tag),0)+ADD_K))-np.log2(float(t_bigram_count.get((prev_tag,penult_tag),0)+ADD_K*vocab_size))

					if V[i-1][prev_tag]["prob"]+trans_prob > max_trans_prob: ###!!!
						
						max_trans_prob = V[i-1][prev_tag]["prob"]+trans_prob 
						
						max_prob = max_trans_prob+np.log2(e_bigram_count.get((words[i],t),0)+ADD_K)-np.log2(float(e_unigram_count[t]+vocab_size*ADD_K))
						
						max_prob = max_trans_prob+np.log2(e_bigram_count.get((words[i],t),0)+ADD_K)-np.log2(float(e_unigram_count[t]+vocab_size*ADD_K))
						
						V[i][t] = {"prob": max_prob, "prev": prev_tag, "penult_tag": penult_tag}

	opt = []
	previous = None	
	max_prob = max(value["prob"] for value in V[-1].values())

	# BACKTRACKING!!! Get the most probable state
	for state, data in V[-1].items():
		if data["prob"] == max_prob:
			opt.append(state)
			previous = state
			break

	for t in range(len(V) - 2, -1, -1): #[3,2,1,0]
		opt.insert(0, V[t + 1][previous]["prev"])
		previous = V[t][previous]["prev"]
	return opt


def compute_accu(predict, ground):
	num = len(ground)
	correct = 0
	total = 0
	for i in range(0,num):
		total = total + 1
		if predict[i]==ground[i]:
			correct = correct + 1

	return (correct,total)


def trigram_inference(vocab, vocab_tag, dataset, t_trigram_count, t_bigram_count, t_unigram_count, e_bigram_count, e_unigram_count, ADD_K):
	conf_matrix = defaultdict(set)
	total = 0
	hit = 0
	tweet_counter = 0
	for tweet in dataset:
		#print tweet
		tweet_counter +=1
		words = [w[0] for w in tweet]
		tags = [t[1] for t in tweet]
		predict = viterbi_tri(vocab, vocab_tag, words, tags, t_trigram_count, t_bigram_count, t_unigram_count, e_bigram_count, e_unigram_count, ADD_K)
		num = len(tags) 
		for i in range(0,num):		
			conf_matrix[tags[i], predict[i]] = conf_matrix.get((tags[i], predict[i]),0) + 1

		(correct,count) = compute_accu(predict,tags)
		hit = hit + correct
		total = total + count
	print ('(add-k k=%d) Trigram hmm accuracy = %f (%d/%d)' % (ADD_K,hit/(float)(total),hit,total))
	print ("#####################################")
	print ("######### confusion matrix###########")
	print ("#####################################")
	print_confusion_matrix(conf_matrix,vocab_tag)



def prob1_add_k():
	train_corpus = read_dataset(TRAIN_SET_PATH)
	test_corpus = read_dataset(DEV_SET_PATH)
	(train_data, vocab, tags) = preprocessing(train_corpus) #final_corpus,words_unk_counts,tags_unk_counts
	test_data = preproc_test(test_corpus,vocab)
	#K_set = [100, 10, 1, 0.1, 0.01]
	K_set = [0]
	t_trigram_count, t_bigram_count, t_unigram_count, e_trigram_count, e_bigram_count, e_unigram_count = learning(train_data)
	for ADD_K in K_set:
		trigram_inference(vocab, tags, test_data, t_trigram_count, t_bigram_count, t_unigram_count, e_bigram_count, e_unigram_count, ADD_K)


def main():

	train_corpus = read_dataset(TRAIN_SET_PATH)
	test_corpus = read_dataset(DEV_SET_PATH)
	for oov_thres in [1,5,10]:
		(train_data, vocab, tags) = preprocessing(train_corpus, oov_thres) #final_corpus,words_unk_counts,tags_unk_counts
		test_data = preproc_test(test_corpus,vocab)
		K_set = [1, 0.01, 0.0001, 0.000001]
		t_trigram_count, t_bigram_count, t_unigram_count, e_trigram_count, e_bigram_count, e_unigram_count = learning(train_data)
		for ADD_K in K_set:
			print('oov thres: ', oov_thres)
			bigram_inference(vocab, tags, test_data, t_bigram_count, t_unigram_count, e_bigram_count, e_unigram_count, ADD_K)



if __name__ == "__main__":
	main() 
