from captureAgents import CaptureAgent
import random, time, util, itertools
from game import Directions, Actions
import game
import math
from util import nearestPoint
import copy
from collections import defaultdict


class ReplaceNode:
    def __init__( self, depth = -1 ):
        self.novel = False
        self.depth = depth

class BasicNode:
    def __init__( self , AlliesActions = None, OpponetActions = None ):
        pass
 
    def getScore( self ):
        if self.red:
            return self.GameState.getScore()
        else:
            return self.GameState.getScore() * -1

    '''
    def getNoveltyFeatures( self, character ):
        gameState = self.GameState
        features = [None,]*5
        for i in self.allies:
            features[i]=[gameState.getAgentState(i).getPosition()]
        if character != 0:
            #stateNode
            for i in self.enemies:
                features[i]=[gameState.getAgentState(i).getPosition()]
        else:
            for i in self.enemies:
                features[i] = []
        features[4] = []
        for j, position in enumerate(gameState.data.capsules):
            features[4].append(('capsule' + str(j), position))
        food = list(set(gameState.data.layout.food.asList())-set(gameState.data.food.asList()))
        for position in food:
            features[4].append(('eatfood', position))
        return features
    '''

    '''
    def getNoveltyFeatures(self, agent):
        gameState = self.GameState
        features = (None, ) * 4
        features[0] = gameState.getAgentState(agent).getPosition()
        features[1] = gameState.getAgentState(agent).numCarrying + gameState.getAgentState(agent).numReturned#food
        features[2] = gameState.getAgentState(agent).numCapsules#capsule
        features[3] = gameState.getAgentState(agent).eatEnemies #eatAgents ###### need to change
        #if features[1] != 0 or features[2] != 0 or features[3] != 0:
        #    print features
        return features
    '''

    def generateTuples(self, agent):
        #features_list = self.getNoveltyFeatures(agent)
        #atom_tuples = [set(),]*4
        #for i in range(4):
        #    atom_tuples[i] = set([features_list[i]])
        gameState = self.GameState
        features = list()
        features.append(gameState.getAgentState(agent).getPosition())
        features.append(gameState.getAgentState(agent).numCarrying)
        features.append(gameState.getAgentState(agent).numReturned)  # food
        features.append(gameState.getAgentState(agent).numCapsules)  # capsule
        features.append(gameState.getAgentState(agent).eatEnemies)  # eatAgents ###### need to change
        # if features[1] != 0 or features[2] != 0 or features[3] != 0:
        #    print features
        return tuple(features)

    '''
    def computeNovelty(self, tuples_set, all_tuples_set):
        diff = tuples_set - all_tuples_set
        if len(diff) > 0:
            novelty = min([len(each) for each in diff])
            return novelty
        else:
            return 9999
    '''

