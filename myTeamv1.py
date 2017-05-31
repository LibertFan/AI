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


from captureAgents import CaptureAgent
import random, time, util, itertools
from game import Directions
import game
import math
from util import nearestPoint
from collections import defaultdict
import copy
import multiprocessing as mp

#################
# Team creation #
#################

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
        features = []
        for i in self.allies:
            features.append(('agent'+str(i), gameState.getAgentState(i).getPosition()))
        if character != 0:
            #stateNode
            for i in self.enemies:
                features.append(('agent'+str(i), gameState.getAgentState(i).getPosition()))
        for j, position in enumerate(gameState.data.capsules):
            features.append(('capsule' + str(j), position))
        food = gameState.data.food.asList()
        for position in food:
            features.append(('food', position))
        return features

    def generateTuples(self, character=0):
        features_list = self.getNoveltyFeatures(character)
        atoms_tuples = set()
        for i in range( 1, 2 ):
            atoms_tuples = atoms_tuples | set(itertools.combinations(features_list, i))
        return atoms_tuples

    def computeNovelty(self, tuples_set, all_tuples_set):
        diff = tuples_set - all_tuples_set
        if len(diff) > 0:
            novelty = min([len(each) for each in diff])
            return novelty
        else:
            return 9999

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
        elif GameState is None:
            self.GameState = GameState
            self.allies = self.StateParent.allies
            self.enemies = self.StateParent.enemies
            self.getDistancer = self.StateParent.getDistancer
            self.Bound = self.StateParent.Bound
            CurrentGameState = copy.deepcopy(self.StateParent.GameState )
            for index, action in self.LastActions.items():
                CurrentGameState = CurrentGameState.generateSuccessor( index, action )
            self.GameState = CurrentGameState
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
    
    ### How to set the best action ?
    ###
    def getBestActions( self ):
        HighestScore = 0
        BestAlliesAction = None
        for AlliesAction in self.LegalAlliesActions:
            SuccAlliesActionsNode = self.AlliesSuccActionsNodeDict.get( AlliesAction )
            if SuccAlliesActionsNode.novel:
                nVisit = 0.0
                totalValue = 0.0
                for EnemiesAction in self.LegalEnemiesActions:
                    SuccEnemiesActionNode = self.EnemiesSuccActionsNodeDict.get( EnemiesAction )
                    if SuccEnemiesActionNode.novel:    
                        SuccStateNode = self.SuccStateNodeDict.get((AlliesAction,EnemiesAction))
                        nVisit += SuccStateNode.nVisit
                        totalValue += SuccStateNode.totalValue
                score = totalValue / float( nVisit )
                SuccAlliesActionsNode.PScore = score
                if score > HighestScore:
                    HighestScore = score
                    BestAlliesAction = AlliesAction
        if BestAlliesAction is None:
            raise Exception( "Error in getBestAction, check the \
                    attribution of 'novel' " )
        
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
                    print self.EnemiesSuccActionsNodeDict
                    print self.LegalEnemiesActions
                    print self.LegalAlliesActions
                    print self.SuccStateNodeDict
                    print len(self.SuccStateNodeDict)
                    raise Exception
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
        for eachStateSucc in self.SuccStateNodeDict.values():
            eachStateSucc.cacheMemory = cacheMemory
            eachStateSucc.isNovel()
                
    def NoveltyTestSuccessors(self, character):
        ###character : allies or enemies
        # 0 is allies
        # 1 is enemies
        ########
        threshold = 1
        if not self.isFullExpand():
            raise Exception("this node is not fully expanded that is not support Novelty computation!")
        else:
            all_atoms_tuples = set()
            this_atoms_tuples = self.generateTuples(character)
            all_atoms_tuples = all_atoms_tuples | this_atoms_tuples

            ### cacheMemory is a list consist of set
            if self.StateParent is None and self.cacheMemory[ character ] is None:
                self.cacheMemory[ character ] = this_atoms_tuples

            if character == 0:
                ChildrenNone = self.AlliesSuccActionsNodeDict
            else:
                ChildrenNone = self.EnemiesSuccActionsNodeDict


            sorted_childNones = []
            for succ in ChildrenNone.values():
                succ_atoms_tuples = succ.generateTuples()
                diff = len(succ_atoms_tuples - all_atoms_tuples)
                sorted_childNones.append((succ, diff, succ_atoms_tuples))
            sorted_childNones = sorted(sorted_childNones, lambda x, y: -cmp(x[1], y[1]))


            for each_pair in sorted_childNones:
                each_succ = each_pair[0]
                succ_atoms_tuples = each_pair[2]
                novelty = self.computeNovelty(succ_atoms_tuples, all_atoms_tuples)
                if novelty > threshold:
                    each_succ.novel = False
                else:
                    p = each_succ.StateParent
                    while p is not None:
                        parent_atoms_tuples = p.cacheMemory[character]
                        if parent_atoms_tuples is None:
                            raise Exception("parent_atom_tuple is None, which goes wrong!")
                        novelty = self.computeNovelty(succ_atoms_tuples, parent_atoms_tuples)
                        if novelty > threshold:
                            each_succ.novel = False
                            break
                        p = p.StateParent
                all_atoms_tuples = all_atoms_tuples | succ_atoms_tuples
            

            ### The original iteration used to modify the succ.novel has been deleted
            """
            for succ in ChildrenNone.values():
                if succ.getScore() > self.getScore():
                    succ.novel = True
            """
            ### saved in succStateNode
            """
            for succ in ChildrenNone.values():
                succ.cacheMemory = all_atoms_tuples
            """    
            return all_atoms_tuples

class ActionNode( BasicNode, ):

    def __init__(self, allies, enemies, Actions, StateParent):
        self.StateParent = StateParent
        self.allies = allies
        self.enemies = enemies
        self.LastActions = Actions
        CurrentGameState = copy.deepcopy( StateParent.GameState )
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
        self.GameState = copy.deepcopy( GameState )
        self.getDistancer = getDistancer
        self.getDistanceDict = getDistanceDict
        self.startPosition = self.GameState.getAgentPosition( self.index )
        self.isPacman = self.GameState.getAgentState( self.index ).isPacman
        self.red = self.GameState.isOnRedTeam( self.index )

    def chooseAction(self, GameState):
        """
        Picks among the actions with the highest Q(s,a).
        """
        gameState = copy.deepcopy( GameState )
        actions = gameState.getLegalActions( self.index )    

        values = [self.evaluate(gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
        foodLeft = len( gameState.data.food.asList() )
     
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

class Distancer:
    def __init__( self ):
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
		self.cores = multiprocessing.cpu_count() - 2
		self.pool = multiprocessing.Pool( processes = self.cores )

    def chooseAction( self, GameState ):
        """ 
        we return the best action for current GameState. 
        we hope to return the best two action for two pacman! 
        """
        start = time.time()
        self.rootNode = StateNode(self.allies, self.enemies, GameState,  getDistancer = self.getMazeDistance)
        iters = 0
        running_time = 0.0
        while( running_time < 30 and iters < self.MCTS_ITERATION ):
            node = self.Select()
            if node is None:
                continue
            EndNode = self.PlayOut( node )
            self.BackPropagate( EndNode )
            end = time.time()
            running_time = end - start
            iters += 1

        print iters
        for actions, succNode in self.rootNode.AlliesSuccActionsNodeDict.items():
            print actions, succNode.novel, succNode.nVisit
            print "-"*50
        print len(self.rootNode.AlliesSuccActionsNodeDict), len(self.rootNode.EnemiesSuccActionsNodeDict)
        print len(self.rootNode.SuccStateNodeDict)
        bestActions = self.rootNode.getBestActions()
        print self.allies, bestActions 
        print "="* 50   
        bestAction = bestActions[0]
        rev = Directions.REVERSE[GameState.getAgentState(self.index).configuration.direction]
        import Queue
        if rev == bestActions:
            CandidateStates = Queue.Queue()
            root = self.rootNode
            CandidateStates.put((root,i))

            while not CandidateStates.empty():
                current, layer = CandidateStates.get()
                if current.novel and layer < 5:
                    if current.ParentState is not None:
                        print "ParentPosition",currentParentState.IndexPositions
                        print 'currentPosition',current.IndexPositions
                        print 'visit times',current.nVisit,'score',current.totalValue / float(self.nVisit)
                    else:
                        print "ParentPosition",None
                        print 'currentPosition',current.IndexPositions
                        print 'visit times',current.nVisit,'score',current.totalValue / float(self.nVisit)
                   

                for successor in current.SuccStateNodeDict.values():
                        CandidateStates.put((successor,i))

        print "&" * 50
        return bestActions[0]

    def Select(self):
        currentNode = self.rootNode
        #time = 1
        while True:
            #print time
            #time += 1
            if not currentNode.isFullExpand():
                #print 'random'
                return currentNode.RandChooseLeftActions()
            else:
                if not currentNode.novelTest:
                    cacheMemory = [currentNode.NoveltyTestSuccessors(0), currentNode.NoveltyTestSuccessors(1)]
                    currentNode.getSuccessorNovel(cacheMemory)
                currentNode = currentNode.UCB1ChooseSuccNode()
                if currentNode is None:
                    raise Exception( "No StateNode in tree is novel!")
                    return None

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
            currentNode = currentNode.StateParent
            









