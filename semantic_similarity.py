# -*- coding: utf-8 -*-
from pywsd import disambiguate
#from pywsd.similarity import max_similarity as maxsim
import numpy as np
from collections import defaultdict
alpha = 0.2
beta  = 0.45
benchmark_similarity = 0.8025
gamma = 1.8
"""
Semantic similarity based on the paper:
    Calculating the similarity between words and sentences using a lexical database and corpus statistics
TKDE, 2018
"""
          
def _synset_similarity(s1,s2):
    L1 =dict()
    L2 =defaultdict(list)
       
    for syn1 in s1:
        L1[syn1[0]] =list()
        for syn2 in s2:                                     
            
            subsumer = syn1[1].lowest_common_hypernyms(syn2[1], simulate_root=True)[0]
            h =subsumer.max_depth() + 1 # as done on NLTK wordnet        
            syn1_dist_subsumer = syn1[1].shortest_path_distance(subsumer,simulate_root =True)
            syn2_dist_subsumer = syn2[1].shortest_path_distance(subsumer,simulate_root =True)
            l  =syn1_dist_subsumer + syn2_dist_subsumer
            f1 = np.exp(-alpha*l)
            a  = np.exp(beta*h)
            b  = np.exp(-beta*h)
            f2 = (a-b) /(a+b)
            sim = f1*f2
            L1[syn1[0]].append(sim)          
            L2[syn2[0]].append(sim)
    return L1, L2       
    
def similarity(s1,s2):
    wsd = (
        [syn for syn in disambiguate(s) if syn[1]]
        for s in (s1, s2)
    )
    
    #vector_length = max(len(s1_wsd), len(s2_wsd))
    
    L = _synset_similarity(*wsd)
    V1, V2 = (
        np.array([max(e[key]) for key in e.keys()])
        for e in L
    )
    S  = np.linalg.norm(V1)*np.linalg.norm(V2)
    C1, C2 = (
        sum(V >= benchmark_similarity)
        for V in (V1, V2)
    )

    Xi = (C1+C2) / gamma

    if C1+C2 == 0:
        Xi = max(V1.size, V2.size) / 2
    return S/Xi
