# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 11:26:36 2016

@author: lenovo
"""
from gensim.models import word2vec
model_org = word2vec.Word2Vec.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
print(model_org["father"])
print(model_org["'s"])