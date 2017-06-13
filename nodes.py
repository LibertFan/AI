from captureAgents import CaptureAgent
import random, time, util, itertools
from game import Directions, Actions
import game
import math
from util import nearestPoint
import copy
from collections import defaultdict
from pathos import multiprocessing as mp
import sys
import numpy as np
import multiprocessing 
from BasicNode import BasicNode, ReplaceNode

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
            self.index = allies[0]
            self.allies = allies
            self.enemies = enemies
            self.Bound = self.getBound()
            self.depth = 0
        elif GameState is None:
            self.allies = self.StateParent.allies
            self.enemies = self.StateParent.enemies
            self.index = self.allies[0]
            self.getDistancer = self.StateParent.getDistancer
            self.Bound = self.StateParent.Bound
            CurrentGameState = self.StateParent.GameState
            for index, action in self.LastActions.items():
		try:
                    CurrentGameState = CurrentGameState.generateSuccessor( index, action )
                except:
		    print index, action, StateParent.GameState.getAgentState( index ).getPosition()
                    CurrentStateNode = StateParent
                    while CurrentStateNode is not None:
                        print CurrentStateNode.IndexPositions[ index ], CurrentStateNode.GameState.getAgentState( index ).getPosition()
                        CurrentStateNode = CurrentStateNode.StateParent 
                    raise Exception 
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
                        if SuccStateNode.novel:
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
            flag = 0
            for SuccStateNode in self.SuccStateNodeDict.values():
                if SuccStateNode.novel and SuccStateNode.nVisit == 0:
                    flag = 1
                    break
            if flag == 1:
                self.FullExpand = False
            else:
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
        elif not self.novel:
            raise Exception( "The chosed state node is unnovel in function UCB1ChooseSuccNode")
        else:
            HighestScore = 0
            ChosedAction = None
            for AlliesAction in self.LegalAlliesActions:
                SuccAlliesActionsNode = self.AlliesSuccActionsNodeDict.get( AlliesAction )
                if SuccAlliesActionsNode.novel:
                    lowestEnemiesScore = 9999                    
                    flag = 0
                    ChosedEnemiesAction = None
                    for EnemiesAction in self.LegalEnemiesActions:
                        SuccEnemiesActionNode = self.EnemiesSuccActionsNodeDict.get( EnemiesAction )
                        if SuccEnemiesActionNode.novel:   
                            SuccStateNode = self.SuccStateNodeDict.get((AlliesAction,EnemiesAction))
                            if SuccStateNode.novel:
                                flag = 1
                                score = SuccStateNode.totalValue / float(SuccStateNode.nVisit) \
                                        + self.C1 * math.sqrt( math.log( self.nVisit ) / SuccStateNode.nVisit )
                                if score < lowestEnemiesScore:
                                    lowestEnemiesScore = score
                                    ChosedEnemiesAction = EnemiesAction
                                        
                    if flag == 0:
                        SuccAlliesActionsNode.novel = False
                        continue
                    elif lowestEnemiesScore > HighestScore:
                        HighestScore = lowestEnemiesScore
                        ChosedAction = ( AlliesAction, ChosedEnemiesAction )

            if ChosedAction is None:
                self.novel = False
                return None
            else:    
                SuccStateNode = self.SuccStateNodeDict.get( ChosedAction )
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
            print type(AlliesActions), type(EnemiesActions), type(self)
            SuccStateNode = StateNode( AlliesActions = AlliesActions, EnemiesActions = EnemiesActions,\
                            AlliesActionNodeParent = AlliesActionNode, EnemiesActionNodeParent = EnemiesActionNode, StateParent = self )
            self.SuccStateNodeDict[ ChosedActions ] = SuccStateNode
        else:
            SuccStateNode = self.SuccStateNodeDict.get( ChosedActions )    
        return SuccStateNode

    ### Expand the StateNode fully 
    ### Del those unnovel nodes( replace them with instances of ReplaceNode )
    ### return the list of NovelSuccStateNode 
    def FullExpandFunc( self ):
        if not self.novelTest:
            SuccStateNodeList = []
            for actions in self.LegalActions:
                SuccStateNdoe = self.ChooseSuccNode( actions )
            cacheMemory = [ self.NoveltyTestSuccessorsV1(0), self.NoveltyTestSuccessorsV1(1)]
            self.getSuccessorNovel( cacheMemory )                  

        NovelSuccActionStateNodeList = [] 
        for actions, SuccStateNode in self.SuccStateNodeDict.items():
            if not SuccStateNode.novel:
                rn = ReplaceNode( SuccStateNode.depth )
                self.SuccStateNodeDict[ actions ] = rn
                ### delete an instance of StateNode
                del SuccStateNode 
            else:
                NovelSuccActionStateNodeList.append( ( SuccStateNode, actions ) ) 

        return NovelSuccActionStateNodeList           
    
    def getNovelSuccStateNodeList( self ):
        NovelSuccActionStateNodeList = [] 
        for actions, SuccStateNode in self.SuccStateNodeDict.items():
            if SuccStateNode.novel:                 
                NovelSuccActionStateNodeList.append( ( SuccStateNode, actions ) )  
        return NovelSuccActionStateNodeList
    
    ### Return top K NovelSuccStateNode in score!
    ### If the number of NovelSuccStateNode is less than k, return them all and the 
    def getSortedSuccStateNodes( self, K, PreActions = [] ):
        if not self.novelTest:        
            raise Exception(" CurrentStateNode is not fully expanded") 

        ### the following list is None !
        NovelSuccActionStateNodeList = self.getNovelSuccStateNodeList()
        if NovelSuccActionStateNodeList == 0:
            raise Exception("No Successive Node is Novel in node.py's function getSortedSuccStateNodes ")           
 
        NovelScoreSuccStateNodeList = [] 
        for SuccStateNode, actions in NovelSuccActionStateNodeList:
            AlliesActions, EnemiesActions = actions
            AlliesActionNode = self.AlliesSuccActionsNodeDict[ AlliesActions ]
            EnemiesActionNode = self.EnemiesSuccActionsNodeDict[ EnemiesActions ]                  
            NovelScoreSuccStateNodeList.append( ( actions, SuccStateNode, AlliesActionNode.getLatentScore(), EnemiesActionNode.getLatentScore() ) )
        try:
            SortedNovelSuccStateNodeList = sorted( NovelScoreSuccStateNodeList, key = lambda x:( x[-2], x[-1] ) )[:K]    
        except:
            print NovelScoreSuccStateNodeList
            raise Exception
    
        NewNovelSuccActionStateNodeList = []     
        for actions, SuccStateNode, _, _ in NovelScoreSuccStateNodeList: 
            NewNovelSuccActionStateNodeList.append( ( SuccStateNode, PreActions + [ actions, ] ) )  
        return NewNovelSuccActionStateNodeList, K - len( NewNovelSuccActionStateNodeList )

    # The following method is used to compute the LatentScore the process of playout when the final score has no change with the original one! 
    # getBound is used to scale the features value to interval [ 0, 0.5 ], and we name the final score as LatentScore!
    # getFeatures is used to compute the features in 
    # getWeights returns a dictionary that record the different features and their corresponding weight
    # getLatentScore is used to

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
            features2['onDefense' + str( index )] = 2
            features2['distanceToFood' + str(index) ] = 0.3
            features2['invaderDistance' + str(index) ] = 50

        features2["numInvaders"] = 2

        #return [features2 * weights, features1 * weights]
        return [ features2 * weights, 0]

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
            weights['distanceToFood' + str( index )] = -2
            weights['invaderDistance' + str( index )] = 0

        return weights
    
    def getFood( self, gameState ):
        if self.red:
            foodLeft = gameState.getBlueFood()
        else:
            foodLeft = gameState.getRedFood()
        return foodLeft

    def getFeatures( self ):
        features = util.Counter()

        walls = self.GameState.getWalls()
        FoodList = self.getFood( self.GameState ).asList()
        for index in self.allies:
            myMinDist = min([self.getDistancer( self.IndexPositions[ index ], food) for food in FoodList])
            features["distanceToFood" + str(index)] = float(myMinDist) / (walls.width * walls.height)

        return features
    
    ### The following functions are used to compute the novelty of an StateNode
    ### the cacheMemory of the successive ActionNode should be set in the following function !
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

class ActionNode( BasicNode ):

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
        self.LatentScore = None
	
    def getLatentScore( self ):
        if self.LatentScore is not None:
            return self.LatentScore
        else:
	    LatentScore = 0
       
	    for index, action in zip( self.allies, list(self.LastActions) ):
		LatentScore += self.getIndexFeatures( self.StateParent.GameState, action, index ) * self.getWeights()	
	    self.LatentScore = LatentScore
            return self.LatentScore  

    def getWeights( self ):
        return {'eats-invader': 5, 'invaders-1-step-away': 0, 'teammateDist': 1.5, 'closest-food': -1,
                'eats-capsules': 10.0, '#-of-dangerous-ghosts-1-step-away': -20, 'eats-ghost': 1.0,
                '#-of-harmless-ghosts-1-step-away': 0.1, 'stopped': -5, 'eats-food': 1}

    def getFood( self, gameState ):
        if self.red:
            foodLeft = gameState.getBlueFood()
        else:
            foodLeft = gameState.getRedFood()
        return foodLeft
	
    def getIndexFeatures(self, state, action, index):
        state = self.StateParent.GameState
        food = self.getFood( state ) 
        foodList = food.asList()
        walls = state.getWalls()
        isPacman = self.GameState.getAgentState(index).isPacman

        # Zone of the board agent is primarily responsible for
        zone = (index - index % 2) / 2

        teammates = [state.getAgentState(i).getPosition() for i in self.allies]
        opponents = [state.getAgentState(i) for i in self.enemies]
        # chasers = [a for a in opponents if not (a.isPacman) and a.getPosition() != None]
        # prey = [a for a in opponents if a.isPacman and a.getPosition() != None]
        chasers = [a for a in opponents if not a.isPacman]
        prey = [a for a in opponents if a.isPacman ]

        features = util.Counter()
        if action == Directions.STOP:
            features["stopped"] = 1.0
        # compute the location of pacman after he takes the action
        x, y = state.getAgentState(index).getPosition()
        dx, dy = Actions.directionToVector(action)
        next_x, next_y = int(x + dx), int(y + dy)

        # count the number of ghosts 1-step away
        for g in chasers:
            if (next_x, next_y) == g.getPosition():
                if g.scaredTimer > 0:
                    features["eats-ghost"] += 1
                    features["eats-food"] += 2
                else:
                    features["#-of-dangerous-ghosts-1-step-away"] = 1
                    features["#-of-harmless-ghosts-1-step-away"] = 0
            elif (next_x, next_y) in Actions.getLegalNeighbors(g.getPosition(), walls):
                if g.scaredTimer > 0:
                    features["#-of-harmless-ghosts-1-step-away"] += 1
                elif isPacman:
                    features["#-of-dangerous-ghosts-1-step-away"] += 1
                    features["#-of-harmless-ghosts-1-step-away"] = 0
        if state.getAgentState(index).scaredTimer == 0:
            for g in prey:
                if (next_x, next_y) == g.getPosition:
                    features["eats-invader"] = 1
                elif (next_x, next_y) in Actions.getLegalNeighbors(g.getPosition(), walls):
                    features["invaders-1-step-away"] += 1
        else:
            for g in opponents:
                if g.getPosition() != None:
                    if (next_x, next_y) == g.getPosition:
                        features["eats-invader"] = -10
                    elif (next_x, next_y) in Actions.getLegalNeighbors(g.getPosition(), walls):
                        features["invaders-1-step-away"] += -10

        for capsule_x, capsule_y in state.getCapsules():
            if next_x == capsule_x and next_y == capsule_y and isPacman:
                features["eats-capsules"] = 1.0
        if not features["#-of-dangerous-ghosts-1-step-away"]:
            if food[next_x][next_y]:
                features["eats-food"] = 1.0
            if len(foodList) > 0:  # This should always be True,  but better safe than sorry
                myFood = []
                for food in foodList:
                    food_x, food_y = food
                    if (food_y > zone * walls.height / 3 and food_y < (zone + 1) * walls.height / 3):
                        myFood.append(food)
                if len(myFood) == 0:
                    myFood = foodList
                myMinDist = min([self.getDistancer((next_x, next_y), food) for food in myFood])
                if myMinDist is not None:
                    features["closest-food"] = float(myMinDist) / (walls.width * walls.height)

        features.divideAll(10.0)

        return features

















 



