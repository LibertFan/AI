# -*- coding: utf-8 -*-
# __author__ = 'siyuan'
import math

#
class SingleTreeNode:

    def __init__(self, random, Id, opp_Id, no_players, NUM_ACTIONS, actions, rootState, parent=None, childIdx=-1):
        self.huge_nagetive = -10000000.0
        self.huge_positive = 10000000.0
        self.epsilon = 1e-6
        self.egreedyEpsilon = 0.05

        self.parent = parent
        self.children_list = []  #长度为NUM_ACTIONS[Id]

        self.totalVal = 0.0
        #self.nVisit =
        self.m_random = random
        self.bound = [float('inf'),float('-inf')]
        self.childIndex = childIdx

        self.MCTS_ITERATION = 100
        self.ROLLOUT_DEPTH = 10
        self.k = math.sqrt(2)
        self.REWARD_DISCOUNT = 1.00
        self.NUM_ACTIONS = NUM_ACTIONS#list
        self.actions = actions#二维数组

        self.Id = Id
        self.opp_Id = opp_Id
        self.no_players = no_players
        if parent is not None:
            self.m_depth = parent.m_depth + 1
        else:
            self.m_depth = 0
        self.rootState =

    #MCTS搜索算法
    def MCTS_Search(self):
        numIters = 0
        while numIters<self.MCTS_ITERATION:




