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
        food = gameState.data.food.asList()
        for position in food:
            features[4].append(('food', position))
        return features

    def generateTuples(self, character=0):
        features_list = self.getNoveltyFeatures(character)
        atom_tuples = [set(),]*5
        for i in range(4):
            atom_tuples[i] = set(features_list[i])
        for i in range( 1, 2 ):
            atom_tuples[4] = atom_tuples[4] | set(itertools.combinations(features_list[4], i))
        return atom_tuples

    '''
    def computeNovelty(self, tuples_set, all_tuples_set):
        diff = tuples_set - all_tuples_set
        if len(diff) > 0:
            novelty = min([len(each) for each in diff])
            return novelty
        else:
            return 9999
    '''

