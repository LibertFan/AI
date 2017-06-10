#myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).
import copy_reg
import types


def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)


'''
def _pickle_method(method):
  func_name = method.im_func.__name__
  obj = method.im_self
  cls = method.im_class
  if func_name.startswith('__') and not func_name.endswith('__'):
    cls_name = cls.__name__.lstrip('_')
  if cls_name: 
    func_name = '_' + cls_name + func_name
  return _unpickle_method, (func_name, obj, cls)
'''


def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
        return func.__get__(obj, cls)


import copy_reg
import types

copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)

from captureAgents import CaptureAgent
import random, time, util, itertools
from game import Directions
import game
import math
from util import nearestPoint
import copy
from collections import defaultdict
from pathos import multiprocessing as mp
import sys
#import multiprocessing as mp
#################
# Team creation #
#################
"""
def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    if func_name.startswith('__') and not func_name.endswith('__'):
        cls_name = cls.__name__.lstrip('_')
    if cls_name: 
        func_name = '_' + cls_name + func_name

def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
        return func.__get__(obj, cls)

import copy_reg
import types
copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)
"""
def createTeam(firstIndex, secondIndex, isRed,
               first = 'MCTSCaptureAgent', second = 'MCTSCaptureAgent'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.
  
    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """

    # The following line is an example only; feel free to change it.
    #return [eval(first)(firstIndex), eval(second)(secondIndex)]
    return [eval(first)( firstIndex ), eval(second)( secondIndex ) ]

##########
# Agents #
##########


class BasicNode:
    def __init__( self , AlliesActions = None, OpponetActions = None ):
        return None 
 
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

class StateNode( BasicNode ):

    def __init__( self, allies = None, enemies = None, GameState = None, AlliesActions = dict(),\
                      EnemiesActions = dict(), AlliesActionNodeParent = None, EnemiesActionNodeParent = None,\
                      StateParent = None, getDistancer = None, getDistanceDict = None ):      	        
        # check the format of input data!
        if StateParent is None and GameState is None:
            raise Exception( "GameState and StateParent can not be 'None' at the same time!" )
        elif StateParent is not None and GameState is not None:
            raise Exception( "GameState and StateParent can not have value at the same time!" )
        """
          Generate attributions:
          ```
          Attention:
          1. The format of Actions is dictionary
          2. The function getDistancer can inherent from StateParent or get from __init__( )
          3. 
          ```
        """
        try:
            self.LastActions = dict( AlliesActions, **EnemiesActions )
        except:
            raise Exception( " the format of AlliesActions and OpponentsAction go wrong!" )

        self.StateParent = StateParent
        self.AlliesActionParent = AlliesActionNodeParent
        self.EnemiesActionParent = EnemiesActionNodeParent
        if StateParent is None:     
            if getDistancer is None or allies is None or enemies is None:
                raise Exception( "the function of getDistancer or allies or enemies missing!")
            self.GameState = copy.deepcopy( GameState )
            self.getDistancer = getDistancer
            self.allies = allies
            self.enemies = enemies
            self.Bound = self.getBound()
            self.depth = 0
        elif GameState is None:
            self.GameState = GameState
            self.allies = self.StateParent.allies
            self.enemies = self.StateParent.enemies
            self.getDistancer = self.StateParent.getDistancer
            self.Bound = self.StateParent.Bound
            CurrentGameState = self.StateParent.GameState
            for index, action in self.LastActions.items():
                CurrentGameState = CurrentGameState.generateSuccessor( index, action )
            self.GameState = CurrentGameState
            self.depth = self.StateParent.depth + 1 
        # self.LegalIndexActions is an auxiliary variables that store a dict which key is the agent index 
        # and the value is its corresponding legal actions  
        self.LegalIndexActions = dict()
        self.IndexStates = dict()
        self.IndexPositions = dict()
        for index in self.allies + self.enemies:
            self.LegalIndexActions[ index ] = self.GameState.getLegalActions( index )
            self.IndexStates[ index ] = self.GameState.getAgentState( index )
            self.IndexPositions[ index ] = self.IndexStates[ index ].getPosition()
        # combine different actions for different indexes
        self.LegalAlliesActions = tuple( itertools.product( self.LegalIndexActions.get(self.allies[0]), self.LegalIndexActions.get(self.allies[1]) ) )    
        self.LegalEnemiesActions = tuple( itertools.product( self.LegalIndexActions.get(self.enemies[0]), self.LegalIndexActions.get(self.enemies[1]) ) ) 
        self.LegalActions = tuple( itertools.product( self.LegalAlliesActions, self.LegalEnemiesActions ) )
        if len( self.LegalActions ) != len( self.LegalAlliesActions ) * len( self.LegalEnemiesActions ):
            raise Exception( "The pair action of allies and enemies are unappropriate" )

        # self.LegalActions = self.LegalAlliesActions + self.LegalEnemiesActions
        # the following attributes 
        self.AlliesSuccActionsNodeDict = dict()
        self.EnemiesSuccActionsNodeDict = dict()
        self.SuccStateNodeDict = dict()
        self.nVisit = 0.0
        self.totalValue = 0.0
        self.C1 = math.sqrt( 2 ) / 10
        self.red = self.GameState.isOnRedTeam( self.allies[0] )
        self.novel = True
        self.cacheMemory = [ None, ] * 2
        self.novelTest = False
        self.InProcess = False
    
    def update( self, ActionSeries ):
        CurrentStateNode = self
        for Action in ActionSeries:
            CurrentStateNode = CurrentStateNode.ChooseSuccNode( Action )
        return CurrentStateNode    
            
    ### How to set the best action ?
    ###
    def getBestActions( self ):
        HighestScore = 0
        BestAlliesAction = None
        print len(self.LegalAlliesActions), len( self.AlliesSuccActionsNodeDict)
        print len( self.LegalEnemiesActions), len(self.EnemiesSuccActionsNodeDict)
        print len(self.LegalActions), len(self.SuccStateNodeDict)
        for AlliesAction in self.LegalAlliesActions:
            SuccAlliesActionsNode = self.AlliesSuccActionsNodeDict.get( AlliesAction )
            lowestEnemiesScore = 9999
            if SuccAlliesActionsNode.novel:
                for EnemiesAction in self.LegalEnemiesActions:
                    SuccEnemiesActionNode = self.EnemiesSuccActionsNodeDict.get( EnemiesAction )
                    if SuccEnemiesActionNode.novel:   
                        SuccStateNode = self.SuccStateNodeDict.get((AlliesAction,EnemiesAction))
                        score = SuccStateNode.totalValue/float(SuccStateNode.nVisit)
                        if score < lowestEnemiesScore:
                            lowestEnemiesScore = score
                if lowestEnemiesScore > HighestScore:
                    HighestScore = lowestEnemiesScore
                    BestAlliesAction = AlliesAction

        if BestAlliesAction is None:
            raise Exception( "Error in getBestAction, check the attribution of 'novel' " )
        
        return BestAlliesAction

    """
    isPrune is related to the self.AlliesActionParent and self.OpponentsActionParent, 
    the return value is True or False.
    """
    def isNovel( self ):
        if self.AlliesActionParent.novel is False or self.EnemiesActionParent.novel is False:
            self.novel = False
        else:
            self.novel = True
        return self.novel	       

    def isFullExpand( self ):
        if len( self.SuccStateNodeDict.keys() ) != len( self.LegalActions ):
            self.FullExpand = False
        else:
            if len( self.LegalAlliesActions ) != len( self.AlliesSuccActionsNodeDict.keys() ) \
            or len( self.LegalEnemiesActions ) != len( self.EnemiesSuccActionsNodeDict.keys() ):
                raise Exception( " This StateNode should not be determined as 'FullExpand' " )
            self.FullExpand = True
        return self.FullExpand

    ### RandChooseLeftActions is applied in MCTS select
    def RandChooseLeftActions( self ):
        if self.isFullExpand():
            raise Exception( "This Node has been full Expanded, you should choose UCB1ChooseActions!" )
        else:
            # Choose the action that has not been taken
            PreparedActions =  []
            for Action in self.LegalActions:
                if self.SuccStateNodeDict.get( Action ) is None:
                    PreparedActions.append( Action )
            ChosedActions = random.choice( PreparedActions )
            # Get the corresponding AlliesActionNode and EnemiesActionNode
            ChosedAlliesAction, ChosedEnemiesAction = ChosedActions
            AlliesActionNode = self.AlliesSuccActionsNodeDict.get( ChosedAlliesAction )
            if AlliesActionNode is None:
                AlliesActionNode = ActionNode( self.allies, self.enemies, ChosedAlliesAction, self )
                self.AlliesSuccActionsNodeDict[ ChosedAlliesAction ] = AlliesActionNode
            EnemiesActionNode = self.EnemiesSuccActionsNodeDict.get( ChosedEnemiesAction )
            if EnemiesActionNode is None:
                EnemiesActionNode = ActionNode( self.enemies, self.allies, ChosedEnemiesAction, self )
                self.EnemiesSuccActionsNodeDict[ ChosedEnemiesAction ] = EnemiesActionNode
            ###  The format of AlliesActionNode and EnenmiesAcrionNode should be dict instead of list!
            AlliesActions = dict( zip( self.allies, ChosedAlliesAction ) )
            EnemiesActions = dict( zip( self.enemies, ChosedEnemiesAction ) )
            SuccStateNode = StateNode( AlliesActions = AlliesActions, EnemiesActions = EnemiesActions,\
                            AlliesActionNodeParent = AlliesActionNode, EnemiesActionNodeParent = EnemiesActionNode, StateParent = self )
            self.SuccStateNodeDict[ ChosedActions ] = SuccStateNode
            return SuccStateNode     
        
    ### UCB1ChooseSuccNode is applied in MCTS select
    ### Do ActionNode call on here need add 1 to their nVisit ?
    def UCB1ChooseSuccNode( self ):
        if not self.isFullExpand():
            raise Exception( "This Node has not been full expanded, you should choose RandChooseLeftActions!")
        else:
            HighestScore = 0
            ChosedAlliesAction = None
            un_novel_num = 0
            for AlliesAction in self.LegalAlliesActions:
                AlliesSuccActionNode = self.AlliesSuccActionsNodeDict.get( AlliesAction )
                if AlliesSuccActionNode.novel:
                    score = AlliesSuccActionNode.totalValue / float( AlliesSuccActionNode.nVisit ) + \
                            self.C1 * math.sqrt( math.log( self.nVisit ) / AlliesSuccActionNode.nVisit )
                    if score >= HighestScore:
                        HighestScore = score
                        ChosedAlliesAction = AlliesAction
                else:
                    un_novel_num += 1
            if un_novel_num == len(self.LegalAlliesActions):
                self.novel = False
                return None
           
            HighestScore = -9999
            ChosedEnemiesAction = None
            EnemiesUnnovelNum = 0
            for EnemiesAction in self.LegalEnemiesActions:
                EnemiesSuccActionNode = self.EnemiesSuccActionsNodeDict.get( EnemiesAction )
                try:
                    a = EnemiesSuccActionNode.novel
                except:
                    # print self.EnemiesSuccActionsNodeDict
                    # print self.LegalEnemiesActions
                    # print self.LegalAlliesActions
                    # print self.SuccStateNodeDict
                    # print len(self.SuccStateNodeDict)
                    raise Exception("No EnemiesSuccActionNode is novel!")
                if EnemiesSuccActionNode.novel:
                    score = - EnemiesSuccActionNode.totalValue / float( EnemiesSuccActionNode.nVisit ) + \
                            self.C1 * math.sqrt( math.log( self.nVisit) / EnemiesSuccActionNode.nVisit )
                    if score >= HighestScore:
                        HighestScore = score
                        ChosedEnemiesAction = EnemiesAction
                else:
                    EnemiesUnnovelNum += 1
            if EnemiesUnnovelNum == len(self.LegalEnemiesActions):
                self.novel = False
                return None
            else:
                ChosedAction = ( ChosedAlliesAction, ChosedEnemiesAction )
                SuccStateNode = self.SuccStateNodeDict[ ChosedAction ]
                return SuccStateNode
    
    ### RandChooseSuccNode is used in the course of MCTS's playout      
    def ChooseSuccNode( self, actions = None ):
        if actions is None:
            ChosedActions = random.choice( self.LegalActions )
            print "Random Choose"
        else:
            ChosedActions = actions
        # Get the corresponding AlliesActionNode and EnemiesActionNode
        if self.SuccStateNodeDict.get( ChosedActions ) is None:
            ChosedAlliesAction, ChosedEnemiesAction = ChosedActions
            if ChosedAlliesAction is None or ChosedEnemiesAction is None:
                print ChosedAlliesAction, ChosedEnemiesAction 
            AlliesActionNode = self.AlliesSuccActionsNodeDict.get( ChosedAlliesAction )            
            if AlliesActionNode is None:
                AlliesActionNode = ActionNode( self.allies, self.enemies, ChosedAlliesAction, self )
                self.AlliesSuccActionsNodeDict[ ChosedAlliesAction ] = AlliesActionNode
            EnemiesActionNode = self.EnemiesSuccActionsNodeDict.get( ChosedEnemiesAction )
            if EnemiesActionNode is None:
                EnemiesActionNode = ActionNode( self.enemies, self.allies, ChosedEnemiesAction, self )
                self.EnemiesSuccActionsNodeDict[ ChosedEnemiesAction ] = EnemiesActionNode 
            ### The format of AlliesActionNode and EnenmiesAcrionNode should be dict instead of list!
            AlliesActions = dict( zip( self.allies, ChosedAlliesAction ) )
            EnemiesActions = dict( zip( self.enemies, ChosedEnemiesAction ) )
            SuccStateNode = StateNode( AlliesActions = AlliesActions, EnemiesActions = EnemiesActions,\
                            AlliesActionNodeParent = AlliesActionNode, EnemiesActionNodeParent = EnemiesActionNode, StateParent = self )
            self.SuccStateNodeDict[ ChosedActions ] = SuccStateNode
        else:
            SuccStateNode = self.SuccStateNodeDict.get( ChosedActions )    
        return SuccStateNode

    """ 
    The following method is used to compute the LatentScore the process of playout when the final score has no change with the original one!
 
    getBound is used to scale the features value to interval [ 0, 0.5 ], and we name the final score as LatentScore!
    getFeatures is used to compute the features in 
    getWeights returns a dictionary that record the different features and their corresponding weight
    getLatentScore is used to

    """

    def getLatentScore( self ):
        weights = self.getWeights()
        features = self.getFeatures()
        return ( features * weights - self.Bound[0] ) * 0.5 / ( self.Bound[1] - self.Bound[0] )

    def getBound( self ):
        weights = self.getWeights()
        features1 = util.Counter()
        for index in self.allies:
            features1['onDefense' + str(index)] = 1 
         
        features2 = util.Counter()
        red = self.GameState.isOnRedTeam(self.allies[0])
        if red:
            foodList = self.GameState.getBlueFood().asList()
        else:
            foodList = self.GameState.getRedFood().asList()
            features2['successorScore'] = len(foodList)

        for index in self.allies:
            features2['onDefens' + str( index )] = 2
            features2['distanceToFood' + str(index) ] = 20
            features2['invaderDistance' + str(index) ] = 50

        features2["numInvaders"] = 2

        return [features2 * weights, features1 * weights]

    def getWeights( self ):
        """
        Features we used here are:
        1. successorScore
        2. distanceToFood1 and distanceToFood2
        3. onDefense1 and onDefense2
        4. numInvaders
        5. invaderDistance1 and invaderDistance2 ( minimum distance to invaders )
        the score to invaderDistance should be positive.abs           
        Only when the pacmac is in their own field, they can compute this score.
        6. When the pacman in the opposite field, there is no effective computation 
        method to measure its behavior.
        
        The weights for various feature should be reset!
        """
        weights = {'successorScore': 0, 'numInvaders': 0 }

        for index in self.allies:
            weights['onDefense' + str( index )] = 0
            weights['distanceToFood' + str( index )] = -100
            weights['invaderDistance' + str( index )] = 0

        return weights

    def getFeatures( self ):
        features = util.Counter()

        if self.red:
            foodList = self.GameState.getBlueFood().asList()
        else:
            foodList = self.GameState.getRedFood().asList()
        features['successorScore'] = len(foodList)

        if len(foodList) > 0: # This should always be True,  but better safe than sorry
            for index in self.allies:
                myPos = self.IndexPositions[ index ]

            minDistance = min([ self.getDistancer(myPos, food) for food in foodList] )
            features['distanceToFood' + str(index)] = minDistance

        enemiesStates = [ self.IndexStates.get( index ) for index in self.enemies ]
        invaders = [ index for a, index in zip( enemiesStates, self.enemies ) if a.isPacman ]
        features['numInvaders'] = len( invaders )

        for index in self.allies:
            myState = self.IndexStates.get( index )
            myPos = self.IndexPositions.get( index )
            if myState.isPacman:
                features['onDefense'+ str(index)] = 1
            if len(invaders) > 0:
                invaders_positions = [ self.IndexPositions.get( a ) for a in invaders ]
                mindist = min([self.getDistancer(myPos, a) for a in invaders_positions])
                features['invaderDistance' + str(index)] = mindist

        self.features = features
        return features
    """
    The following functions are used to compute the novelty of an StateNode
    """
    ### the cachyMemory of the successive ActionNode should be set in the following function !
    ### And also update the novel of the SuccStateNodes
    def getSuccessorNovel(self,cacheMemory):
        self.novelTest = True
        for eachStateSucc in self.SuccStateNodeDict.values():
            eachStateSucc.cacheMemory = cacheMemory
            eachStateSucc.isNovel()

    def updateCacheMemory(self, allMemory, addMemory):
        for component in range(len(addMemory)):
            allMemory[component] = allMemory[component] | addMemory[component]
        return allMemory

    def NoveltyTestSuccessorsV1(self, character):
        ###character : allies or enemies
        # 0 is allies
        # 1 is enemies
        ########
        this_atoms_tuples = self.generateTuples(character)

        ### cacheMemory is a list consist of set
        # print self.StateParent
        # print self.cacheMemory[character]
        # print '*'*80
        if self.StateParent is None and self.cacheMemory[character] is None:
            # print 'hello'
            self.cacheMemory[character] = this_atoms_tuples

        if character == 0:
            ChildrenNone = self.AlliesSuccActionsNodeDict
            parent_allies = self.allies
        else:
            ChildrenNone = self.EnemiesSuccActionsNodeDict
            parent_allies = self.enemies

        # print parent_allies
        all_memory = [set(),]*5
        p = self
        parent_atoms_tuples = p.cacheMemory[character]
        self.updateCacheMemory(all_memory, parent_atoms_tuples)
        for succ in ChildrenNone.values():
            # print succ.allies
            succ_atoms_tuples = succ.generateTuples()
            '''
            print succ_atoms_tuples[succ.allies[0]]
            print succ_atoms_tuples[succ.allies[1]]
            print '.....'*20
            '''
            self.updateCacheMemory(all_memory,succ_atoms_tuples)
            if len(succ_atoms_tuples[4]) - len(parent_atoms_tuples[4]) == 0:
                if len(succ_atoms_tuples[succ.allies[0]] - parent_atoms_tuples[parent_allies[0]]) == 0:
                    succ.novel = False
                    #print 1
                    continue
                else:
                    if len(succ_atoms_tuples[succ.allies[0]] - parent_atoms_tuples[parent_allies[1]]) == 0:
                        if len(succ_atoms_tuples[succ.allies[1]] - parent_atoms_tuples[parent_allies[0]]) == 0 or \
                                        len(succ_atoms_tuples[succ.allies[1]] - parent_atoms_tuples[parent_allies[1]]) == 0:
                            succ.novel = False
                            #print 2
                            continue
                    else:
                        if len(succ_atoms_tuples[succ.allies[1]] - parent_atoms_tuples[parent_allies[1]]) == 0:
                            succ.novel = False
                            #print 3
                            continue

        return all_memory

class ActionNode( BasicNode, ):

    def __init__(self, allies, enemies, Actions, StateParent):
        self.StateParent = StateParent
        self.allies = allies
        self.enemies = enemies
        self.LastActions = Actions
        CurrentGameState = StateParent.GameState
        for index, action in zip(self.allies, self.LastActions):
            CurrentGameState = CurrentGameState.generateSuccessor(index, action)
        self.GameState = CurrentGameState
        self.getDistancer = self.StateParent.getDistancer
        self.novel = True
        self.cacheMemory = None
        self.red = self.GameState.isOnRedTeam(self.allies[0])
        self.nVisit = 0
        self.totalValue = 0.0

class SimulateAgent:
    """
    In BaselineTeam, the agents are divided into Defensive Agent and Offensive Agent, there we shoul allocate an "Defensive" or "Offensive" 
    state for our agent here
    For simplification, here if the Agent in its own field, then we consider it as Defensive state, else we consider it as Offensive State.
    Obviouly, this method is quite bad! 
    We should reset the their State !
    """
    def __init__(self, index, allies, enemies, GameState, getDistancer, getDistanceDict = None ):
        self.index = index
        self.allies = allies
        self.enemies = enemies
        #########这里的deepcopy有意义吗
        self.GameState = copy.deepcopy( GameState )
        self.getDistancer = getDistancer
        self.getDistanceDict = getDistanceDict
        self.startPosition = self.GameState.getAgentPosition( self.index )
        self.isPacman = self.GameState.getAgentState( self.index ).isPacman
        self.red = self.GameState.isOnRedTeam( self.index )

    def chooseAction(self, GameState, nums=None):
        """
        Picks among the actions with the highest Q(s,a).
        """
        gameState = copy.deepcopy( GameState )
        actions = gameState.getLegalActions( self.index )    

        values = [self.evaluate(gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
        
        if self.red:
            foodLeft = self.GameState.getBlueFood().asList()
        else:
            foodLeft = self.GameState.getRedFood().asList()
     
        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getDistancer(self.startPosition,pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction
      
        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor( self.index, action)
        pos = successor.getAgentState( self.index ).getPosition()
        if pos != nearestPoint(pos):
           # Only half a grid position was covered
            return successor.generateSuccessor( self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        if self.isPacman:
            features = self.getDefensiveFeatures( gameState, action )
        else:
            features = self.getOffensiveFeatures( gameState, action )
        weights = self.getWeights( )
        return features * weights

    def getOffensiveFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
      
        if self.red:
            foodList = self.GameState.getBlueFood().asList()
        else:
            foodList = self.GameState.getRedFood().asList()
        features['successorScore'] = -len(foodList)

        # Compute distance to the nearest food

        if len(foodList) > 0: # This should always be True,  but better safe than sorry
            myPos = successor.getAgentState( self.index ).getPosition()
        minDistance = min([self.getDistancer(myPos, food) for food in foodList])
        features['distanceToFood'] = minDistance

        return features

    def getDefensiveFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)

        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        # Computes whether we're on defense (1) or offense (0)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0

        # Computes distance to invaders we can see
        enemies = [successor.getAgentState(i) for i in self.enemies]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            invader_positions = [ a.getPosition() for a in invaders ]
            mindist = self.getDistancer( myPos, invader_positions )
            features['invaderDistance'] = mindist

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features
   
    def getWeights( self ):
        """
        Normally, weights do not depend on the gamestate.  They can be either
        a counter or a dictionary.
        """
        return {'successorScore': 100, 'distanceToFood': -1, 'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}

class SimulateAgentV1( SimulateAgent ):
    ## return the i-th score action!
    def chooseAction(self, GameState, nums=None):
        gameState = copy.deepcopy(GameState)
        actions = gameState.getLegalActions(self.index )

        values = [self.evaluate(gameState, a) for a in actions]
        ActionValues = list( zip( actions, values ) )
        sorted(ActionValues, lambda x, y: -cmp(x[1], y[1]))
        SortActionValues = sorted( ActionValues, lambda x, y: -cmp( x[1], y[1] ) )
        TopAction = []
        for i in range(nums):
            try:
                TopAction.append( SortActionValues[i][0] )
            except:
                break

        if self.red:
            foodLeft = self.GameState.getBlueFood().asList()
        else:
            foodLeft = self.GameState.getRedFood().asList()

        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition( self.index )
                dist = self.getDistancer(self.startPosition,pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction

        return TopAction


class Distancer:

    def __init__( self, layout ):
        """
        Attention: the coodinate begins from 1 instead of 0
        """
        self.height = layout.height - 2
        self.width = layout.width - 2
        self.positions_dict = dict()
        self.layout = layout
        self.construct_dict()

    def adj( self ):
        for w in range( 1, self.width + 1 ):
            for h in range( 1, self.height + 1 ):
                position = ( w, h )
                if not self.layout.isWall( position ):
                    """
                    how to set the following collection.default()?
                    """
                    self.positions_dict[ position ] = defaultdict(int)
                    self.positions_dict[ position ][ position ] = 0
                    for ix, iy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        new_position = ( position[0] + ix, position[1] +iy )
                        if not self.layout.isWall( new_position ):
                            self.positions_dict[ position ][ new_position ] = 1

        self.positions = self.positions_dict.keys()
        self.inf = 99999  
        for key1, key2 in tuple( itertools.product( self.positions, repeat=2 ) ):
            if self.positions_dict[key1].get(key2) is None:
                self.positions_dict[key1][key2] = self.inf        
    
    def construct_dict( self ):
        self.adj()  
        for position2 in self.positions:
            for position1 in self.positions:
                for position3 in self.positions:
                    self.positions_dict[ position1 ][ position3 ]\
                    = min( self.positions_dict[ position1][position3],\
                    self.positions_dict[ position1 ][ position2 ] +\
                    self.positions_dict[ position2 ][ position3 ] )

    def getDistancer( self, pos1 ,pos2 ):
        return self.positions_dict[pos1][pos2]

    def min_position_distance( self, start_position, target_list ):
        distances = self.positions_dict[ start_position ]
        min_distance = 9999
        for target in target_list:
            distance = distances[ target ]  
            if min_distance > distance:
                min_distance = distance
        return min_distance    
    
    def max_position_distance( self, layout, start_position ):
        return 0

#need to change
class MCTSCaptureAgent(CaptureAgent):

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.allies = self.getTeam( gameState )
        if self.allies[0] != self.index:
            self.allies = self.allies[::-1]
        self.enemies = self.getOpponents( gameState )
        print self.allies, self.enemies
        self.MCTS_ITERATION = 10000
        self.ROLLOUT_DEPTH = 10
        self.LastRootNode = None
        self.cores = mp.cpu_count() - 2
        print self.cores
        self.count = 0
        #self.pool = mp.ProcessingPool( processes = self.cores )
        self.getMazeDistance = Distancer( gameState.data.layout ).getDistancer
       
    """ 
    we return the best action for current GameState. 
    we hope to return the best two action for two pacman! 
    """

    def TreeReuse( self, GameState):
        print "TreeReuse is used"
        if self.LastRootNode is None:
            print "LastRootNode is None"
            self.leaf = None
            self.novelleaf = None
            return None
        else:
            IndexPositions = dict()
            for index in self.allies + self.enemies:
                IndexPositions[ index ] = GameState.getAgentState( index ).getPosition()
            for Action in self.LastRootNode.LegalActions: 
                SuccStateNode = self.LastRootNode.SuccStateNodeDict.get( Action )
                if SuccStateNode is not None and SuccStateNode.novel and SuccStateNode.IndexPositions == IndexPositions:
                    self.rootNode = SuccStateNode
                    self.rootNode.AlliesActionParent = None
                    self.rootNode.EnemiesActionParent = None
                    self.rootNode.StateParent = None

                    import Queue
                    CandidateStates = Queue.Queue()
                    root = self.rootNode
                    CandidateStates.put( ( root ) )
                    num = 0
                    novelnum = 0 
                    while not CandidateStates.empty():              
                        CurrentState = CandidateStates.get()
                        CurrentState.depth = CurrentState.depth - 1 
                        num += 1
                        if CurrentState.novel:
                            novelnum += 1
                        for successor in CurrentState.SuccStateNodeDict.values():
                            CandidateStates.put( successor ) 
                    print num, novelnum
                    self.leaf = num
                    self.novelleaf = novelnum
                    return self.rootNode
                    
            return None   

    def chooseAction( self, GameState ):
        print "="* 25, "new process", "="*25
        self.count =+ 1
        print self.count
        start = time.time()
        self.rootNode = self.TreeReuse( GameState )
        if self.rootNode is None:
            self.rootNode = StateNode(self.allies, self.enemies, GameState,  getDistancer = self.getMazeDistance)
        print "="*50
        print "Start Position",self.rootNode.IndexPositions
        print "="*50  

        iters = 0
        running_time = 0.0
        if self.novelleaf is None or self.novelleaf < 500:             
            while( iters < 2 and running_time < 10 ):        
                node = self.Select()
                if node is None:
                    print "Invalid Selections"
                    print iters
                    iters += 1
                    if node == self.rootNode or id(node) == id(self.rootNode):
                        raise Exception("MCTS/chooseAction: No Node in the tree is novel")
                    continue
                print "iters",iters, "select node position:", node.IndexPositions               
                self.ParallelGenerateSuccNode( node )
                end = time.time()
                running_time = end - start
                iters += 1
             
        print "iters", iters  
        self.LastRootNode = self.rootNode
        bestActions = self.rootNode.getBestActions()
        bestAction = bestActions[0]
        print "="*50
        print "="*50
        print "Positions:", self.rootNode.IndexPositions
        print "index:", self.index, "beseAction:", bestAction
        print "=" * 50
        print "="*50
        return bestAction

    def Select( self ):
        currentNode = self.rootNode
        while True:
            if not currentNode.novelTest:
                if currentNode.isFullExpand():
                    raise Exception("This node should be FullExpand!")
                return currentNode
            else:
                currentNode = currentNode.UCB1ChooseSuccNode()
                if currentNode is None:
                    #raise Exception( "No StateNode in tree is novel!")
                    return None 

    def ParallelGenerateSuccNode(self, CurrentStateNode):

        def PlayOut3( CurrentStateInfo ):
            t1 = time.time()
            GameState, InitialAction = CurrentStateInfo
            print InitialAction, "playout begin!"      

            n1 = SimulateAgentV1( self.allies[0], self.allies, self.enemies, GameState,
                                  self.getMazeDistance )
            a1s = n1.chooseAction( GameState, 2 )

            n2 = SimulateAgentV1( self.allies[1], self.allies, self.enemies, GameState,
                                  self.getMazeDistance )
            a2s = n2.chooseAction( GameState, 2 )

            a12s = list( itertools.product( a1s , a2s ) )
            if len( a12s ) > 3:
                a12s = a12s[:3]

            m1 = SimulateAgentV1( self.enemies[0], self.enemies, self.allies, GameState,
                                  self.getMazeDistance )
            b1s = m1.chooseAction( GameState, 2 )
            m2 = SimulateAgentV1( self.enemies[1], self.enemies, self.allies, GameState,
                                  self.getMazeDistance )
            b2s = m2.chooseAction( GameState, 2 )

            b12s = list( itertools.product( b1s, b2s ) )
            if len(b12s) > 3:
                b12s = b12s[:3]

            ActionList = tuple( itertools.product( a12s, b12s ) )

            ActionSeriesList = [ None, ] * len( ActionList )
            for index in range( len( ActionList ) ):
                ActionSeriesList[ index ] = [ InitialAction, ] 

            for index, Actions in enumerate(ActionList):
                ActionSeriesList[ index ].append( Actions )
                iters = 0
                CurrentGameState = copy.deepcopy( GameState )
                for Agent, Action in zip( self.allies + self.enemies, Actions[0] + Actions[1] ):
                    CurrentGameState = CurrentGameState.generateSuccessor( Agent, Action )
              
                while iters < ( self.ROLLOUT_DEPTH - 1 ):
                    ###########为什么每次都要new SimulateAgent

                    n1 = SimulateAgent( self.allies[0], self.allies, self.enemies, CurrentGameState,
                                        self.getMazeDistance )
                    a1 = n1.chooseAction( CurrentGameState )

                    n2 = SimulateAgent( self.allies[1], self.allies, self.enemies, CurrentGameState,
                                        self.getMazeDistance )
                    a2 = n2.chooseAction( CurrentGameState )

                    m1 = SimulateAgent( self.enemies[0], self.enemies, self.allies, CurrentGameState,
                                        self.getMazeDistance )
                    b1 = m1.chooseAction( CurrentGameState )

                    m2 = SimulateAgent( self.enemies[1], self.enemies, self.allies, CurrentGameState,
                                        self.getMazeDistance )
                    b2 = m2.chooseAction( CurrentGameState )

                    Actions = ( a1, a2, b1, b2 )
                    for Agent, Action in zip( self.allies + self.enemies, Actions):
                        CurrentGameState = CurrentGameState.generateSuccessor( Agent, Action )
                        
                    iters += 1
                    ActionSeriesList[ index ].append( ( ( a1, a2 ) , ( b1, b2 ) ) )     

            t2 = time.time()
            print InitialAction, t2 - t1

            return ActionSeriesList

        def PlayOut2( CurrentStateInfo ): 

            CurrentStateNode, Action = CurrentStateInfo
            time1 = time.time()
            print Action, "playout begin!"       
            n1 = SimulateAgentV1(self.allies[0], self.allies, self.enemies, CurrentStateNode.GameState,
                                 self.getMazeDistance)
            a1s = n1.chooseAction(CurrentStateNode.GameState, 2)
            n2 = SimulateAgentV1(self.allies[1], self.allies, self.enemies, CurrentStateNode.GameState,
                                 self.getMazeDistance)
            a2s = n2.chooseAction(CurrentStateNode.GameState, 2)
            a12s = list(itertools.product(a1s, a2s))
            if len(a12s) > 3:
                a12s = a12s[:3]
            m1 = SimulateAgentV1(self.enemies[0], self.enemies, self.allies, CurrentStateNode.GameState,
                                 self.getMazeDistance)
            b1s = m1.chooseAction(CurrentStateNode.GameState, 2)
            m2 = SimulateAgentV1(self.enemies[1], self.enemies, self.allies, CurrentStateNode.GameState,
                                 self.getMazeDistance)
            b2s = m2.chooseAction(CurrentStateNode.GameState, 2)
            b12s = list(itertools.product(b1s, b2s))
            if len(b12s) > 3:
                b12s = b12s[:3]
            actions = tuple(itertools.product(a12s, b12s))
            # print actions
            # print "actions:",len(actions)
            # if CurrentStateNode.StateParent == self.rootNode or id(CurrentStateNode.StateParent) == id(self.rootNode):
            #     print "Play out CurrentNode == rootNode"
            CurrentNodeList = []
            for i in range(len(actions)):
                iters = 0
                #print CurrentStateNode.LegalActions
                #print actions[i]
                CopyCurrentStateNode = CurrentStateNode.ChooseSuccNode(actions[i])
                while iters < (self.ROLLOUT_DEPTH - 1):
                    n1 = SimulateAgent(self.allies[0], self.allies, self.enemies,CopyCurrentStateNode.GameState,
                                       self.getMazeDistance)
                    a1 = n1.chooseAction(CopyCurrentStateNode.GameState)
                    n2 = SimulateAgent(self.allies[1], self.allies, self.enemies, CopyCurrentStateNode.GameState,
                                       self.getMazeDistance)
                    a2 = n2.chooseAction(CopyCurrentStateNode.GameState)

                    m1 = SimulateAgent(self.enemies[0], self.enemies, self.allies,CopyCurrentStateNode.GameState,
                                       self.getMazeDistance)
                    b1 = m1.chooseAction(CopyCurrentStateNode.GameState)
                    m2 = SimulateAgent(self.enemies[1], self.enemies, self.allies, CopyCurrentStateNode.GameState,
                                       self.getMazeDistance)
                    b2 = m2.chooseAction(CopyCurrentStateNode.GameState)
                    CopyCurrentStateNode = CopyCurrentStateNode.ChooseSuccNode(((a1, a2), (b1, b2)))
                    iters += 1
                CurrentNodeList.append(CopyCurrentStateNode)
            time2 = time.time()
            print Action, time2 - time1
            # print "CurrentNodeList:",len(CurrentNodeList)    
            return Action, CurrentStateNode, CurrentNodeList

        if not CurrentStateNode.novelTest:
            print "ParallelGenerateSuccNdoe novelTest"
            # f = CurrentStateNode.ChooseSuccNode()
            # SuccStateNodes = self.pool.map(CurrentStateNode.ChooseSuccNode, CurrentStateNode.LegalActions)
            ######################################## 可以删掉吗
            SuccStateNodes = []
            for actions in CurrentStateNode.LegalActions:
                SuccStateNode = CurrentStateNode.ChooseSuccNode( actions )
                SuccStateNodes.append( SuccStateNode )
            if len(SuccStateNodes) != len(CurrentStateNode.LegalActions) or\
               len(CurrentStateNode.AlliesSuccActionsNodeDict) != len(CurrentStateNode.LegalAlliesActions) or\
               len(CurrentStateNode.EnemiesSuccActionsNodeDict) != len(CurrentStateNode.LegalEnemiesActions):
                raise Exception("Parallel goes wrong!")
            cacheMemory = [CurrentStateNode.NoveltyTestSuccessorsV1(0), CurrentStateNode.NoveltyTestSuccessorsV1(1)]
            CurrentStateNode.getSuccessorNovel(cacheMemory)
           # for each in CurrentStateNode.AlliesSuccActionsNodeDict.items():
           #     print each[0],each[1].novel
           # print 'x'*80
           # for each in CurrentStateNode.EnemiesSuccActionsNodeDict.items():
           #     print each[0],each[1].novel
        else:
            raise Exception("The novelTest of this node should be False!")

        #CurrentCopyInfo = []
        CurrentInfo = []
        for Actions, SuccStateNode in CurrentStateNode.SuccStateNodeDict.items():
            if SuccStateNode.novel:
                CurrentInfo.append( ( SuccStateNode, Actions ) )
                #CopySuccStateNode = copy.deepcopy( SuccStateNode )
                #CopySuccStateNode.AlliesActionParent = None
                #CopySuccStateNode.EnemiesActionParent = None
                #CopySuccStateNode.StateParent = None 
                #CurrentCopyInfo.append( ( CopySuccStateNode, Actions ) ) 

        if len( CurrentInfo ) == 0:
            CurrentStateNode.novel = False
            return

        print "The number of branch is:", len(CurrentInfo)

        if len(CurrentInfo) > 2:

            p = mp.ProcessPool( 3 )
            t1 = time.time()

            GameStateList = [ ( copy.deepcopy( CurrentState.GameState ), Action ) for CurrentState, Action in CurrentInfo ]
            print "Parallel Begin"
            #ActionSeriesLists = p.map( PlayOut3, GameStateList )
            #HelpList = []
            #for each in CurrentCopyInfo:
            #    HelpList.append( p.apply_async( PlayOut2, args=(each,) ) )

            ##################不需要random就直接playout吗
            results = p.amap( PlayOut3, GameStateList )
            while not results.ready():
                time.sleep(0.1)
            ActionSeriesLists = results.get()
            #p.close()
            #p.join()
            #EndStateNodeLists = []  
            #for each in HelpList:
            #    EndStateNodeLists.append( each.get() ) 
            t2 = time.time()
            print "Parallel Finish!", t2 - t1

            for ActionSeriesList in ActionSeriesLists:
                for ActionSeries in ActionSeriesList:
                    EndStateNode = CurrentStateNode.update( ActionSeries )
                    self.BackPropagate(EndStateNode)
            t3 = time.time()        
            print "BackPropagate Finish!", t3 - t1      
        else:
            for info in CurrentInfo:
                _, _, EndStateNodeList = PlayOut2( info )
                for EndStateNode in EndStateNodeList: 
                    self.BackPropagate( EndStateNode )

    def PlayOut( self, CurrentNode ):
        iters = 0
        while iters < self.ROLLOUT_DEPTH:
            n1 = SimulateAgent( self.allies[0], self.allies, self.enemies, CurrentNode.GameState, self.getMazeDistance )
            a1 = n1.chooseAction( CurrentNode.GameState )
            n2 = SimulateAgent( self.allies[1], self.allies, self.enemies, CurrentNode.GameState, self.getMazeDistance )
            a2 = n2.chooseAction( CurrentNode.GameState )

            m1 = SimulateAgent( self.enemies[0], self.enemies, self.allies, CurrentNode.GameState, self.getMazeDistance )
            b1 = m1.chooseAction( CurrentNode.GameState )
            m2 = SimulateAgent( self.enemies[1], self.enemies, self.allies, CurrentNode.GameState, self.getMazeDistance )
            b2 = m2.chooseAction( CurrentNode.GameState )
            CurrentNode = CurrentNode.ChooseSuccNode( ((a1,a2),(b1,b2)) )
            iters += 1
        return CurrentNode

    def PlayOut1( self, CurrentNode ):
        iters = 0
        while iters < self.ROLLOUT_DEPTH:
            CurrentNode = CurrentNode.ChooseSuccNode()
            iters += 1
        return CurrentNode

    def BackPropagate( self, endNode):
        #print "backPropagate"
        """
        In ExploreNode.getSupScore, self.distance_layout is used!
        """
        score = self.getScore( endNode.GameState )
        if score == self.getScore( self.rootNode.GameState ):
            LatentScore = endNode.getLatentScore()
            score += LatentScore
        else:
            print "Oh My God", score
        currentNode = endNode
        while currentNode is not None:
            if currentNode.AlliesActionParent is not None:
                currentNode.AlliesActionParent.totalValue += score            
                currentNode.AlliesActionParent.nVisit += 1
                currentNode.EnemiesActionParent.totalValue += score 
                currentNode.EnemiesActionParent.nVisit += 1
            currentNode.totalValue += score
            currentNode.nVisit += 1
            """
            if currentNode.StateParent is None:
                print currentNode.IndexPositions
                print id(currentNode)
                print id(self.rootNode)
            if currentNode == self.rootNode or id(currentNode) == id(self.rootNode):
                print "rootNode"
                print currentNode.IndexPositions
                print currentNode.nVisit
                print currentNode.totalValue
            """    
            currentNode = currentNode.StateParent



