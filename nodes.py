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
import capture

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
            #self.index = allies[0]
            self.allies = allies
            self.enemies = enemies
            self.Bound = self.getBound()
            self.depth = 0
        elif GameState is None:
            self.allies = self.StateParent.allies
            self.enemies = self.StateParent.enemies
            #self.index = self.allies[0]
            self.getDistancer = self.StateParent.getDistancer
            self.Bound = self.StateParent.Bound

            CurrentGameState = self.StateParent.GameState

            agentMoveInfo = []
            for agentIndex, action in self.LastActions.items():
                isAgentPacman = CurrentGameState.getAgentState( agentIndex ).isPacman
                agentMoveInfo.append( ( isAgentPacman, agentIndex, action ) ) 
            agentMoveOrder = sorted( agentMoveInfo, key=lambda x:( x[0], x[1] ) ) 

            self.deadAgentList = []
            for index, ( isAgentPacman, agentIndex, action ) in enumerate( agentMoveOrder ):
                if agentIndex in self.deadAgentList:
                    CurrentGameState, deadAgents = CurrentGameState.generateSuccessor( agentIndex, "Stop", True )
                    self.deadAgentList.extend( deadAgents )
                else:    
                    CurrentGameState, deadAgents = CurrentGameState.generateSuccessor( agentIndex, action, True )
                    self.deadAgentList.extend( deadAgents )

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
        self.cacheMemory = defaultdict(set)
        self.novelTest = False
        #self.InProcess = False
        #self.DeathNum = [ None, ] * 4


    def update( self, ActionSeries ):
        CurrentStateNode = self
        for Action in ActionSeries:
            CurrentStateNode = CurrentStateNode.ChooseSuccNode( Action )
        return CurrentStateNode    
            
    ### How to set the best action ?
    ###
    def getBestActions( self ):
        HighestScore = -9999
        BestAlliesAction = None
        for AlliesAction in self.LegalAlliesActions:
            SuccAlliesActionsNode = self.AlliesSuccActionsNodeDict.get( AlliesAction )
            lowestEnemiesScore = 9999
            if SuccAlliesActionsNode.novel:
                for EnemiesAction in self.LegalEnemiesActions:
                    SuccEnemiesActionNode = self.EnemiesSuccActionsNodeDict.get( EnemiesAction )
                    if SuccEnemiesActionNode.novel:
                        print 'novel action', (AlliesAction,EnemiesAction)
                        SuccStateNode = self.SuccStateNodeDict.get((AlliesAction,EnemiesAction))
                        if SuccStateNode.novel:
                            score = SuccStateNode.totalValue/float(SuccStateNode.nVisit)
                            if score < lowestEnemiesScore:
                                lowestEnemiesScore = score

                if lowestEnemiesScore != 9999 and lowestEnemiesScore > HighestScore:
                    HighestScore = lowestEnemiesScore
                    BestAlliesAction = AlliesAction

        if BestAlliesAction is None:
            raise Exception( "Error in getBestAction, check the attribution of 'novel' " )

        print "BestAction",BestAlliesAction
        return BestAlliesAction

    """
    isPrune is related to the self.AlliesActionParent and self.OpponentsActionParent, 
    the return value is True or False.
    """

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
            if len( self.SuccStateNodeDict.keys() ) == 0 or flag == 1:
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
            ### judge which part of action is unnovel!
            if self.StateParent is None:
                #print self.cacheMemory
                #for action, SuccActionNode in self.AlliesSuccActionsNodeDict.items():
                #   print action, SuccActionN

                for actions, SuccStateNode in self.SuccStateNodeDict.items():
                    print actions, SuccStateNode.IndexPositions

                AgentFaultList = self.WhichAgentFault()
                print "UCB1, AgentFaultList", AgentFaultList
                for agent in AgentFaultList:
                    self.cacheMemory[agent] = set()
                print "UCB1, refresh cacheMemory", self.cacheMemory
                self.NovelTest = False
                self.novel = True
                self.AlliesSuccActionsNodeDict = dict()
                self.EnemiesSuccActionsNodeDict = dict()
                self.SuccStateNodeDict = dict()

                return self

            raise Exception( "The chosed state node is unnovel in function UCB1ChooseSuccNode")
        else:
            HighestScore = -9999
            ChosedAction = None
            for AlliesAction in self.LegalAlliesActions:
                SuccAlliesActionsNode = self.AlliesSuccActionsNodeDict.get( AlliesAction )
                if SuccAlliesActionsNode.novel:
                    lowestEnemiesScore = 9999                    
                    #flag = 0
                    ChosedEnemiesAction = None
                    for EnemiesAction in self.LegalEnemiesActions:
                        SuccEnemiesActionNode = self.EnemiesSuccActionsNodeDict.get( EnemiesAction )
                        if SuccEnemiesActionNode.novel:   
                            SuccStateNode = self.SuccStateNodeDict.get((AlliesAction,EnemiesAction))
                            if SuccStateNode.novel:
                                #flag = 1
                                score = SuccStateNode.totalValue / float(SuccStateNode.nVisit) \
                                        + self.C1 * math.sqrt( math.log( self.nVisit ) / SuccStateNode.nVisit )
                                if score < lowestEnemiesScore:
                                    lowestEnemiesScore = score
                                    ChosedEnemiesAction = EnemiesAction
                            else:
                                print self.IndexPositions 
                                print SuccAlliesActionsNode.LastActions, SuccEnemiesActionNode.LastActions

                                raise Exception( "Two novel actions produce an unnovel StateNode!" )
                                    
                    if lowestEnemiesScore != 9999 and lowestEnemiesScore > HighestScore:
                        HighestScore = lowestEnemiesScore
                        ChosedAction = ( AlliesAction, ChosedEnemiesAction )

            if ChosedAction is None:
                #self = ReplaceNode(self.depth)
                #if self.StateParent is None:
                #    print "This StateNode is RootNode"
                raise Exception("UCB1 return None!") 
                self.novel = False
                return None
            else:    
                SuccStateNode = self.SuccStateNodeDict.get( ChosedAction )
                if SuccStateNode is None:
                    print "all legal actions",self.LegalIndexActions
                    print "all succ state nodes",self.SuccStateNodeDict
                    print "chosed action",ChosedAction
                    currentStateNode = self
                    while currentStateNode.StateParent is not None:
                        print currentStateNode.IndexPositions 

                    raise Exception ("UCB1 Chosed StateNode is None")

                return SuccStateNode
 
    def WhichAgentFault( self ):
        WhichActionNodeDictList = []
        WhichTeamList = []

        alliesUnnovelNum = 0
        for actionNode in self.AlliesSuccActionsNodeDict.values():
            if not actionNode.novel:
                alliesUnnovelNum += 1 
        if alliesUnnovelNum == len( self.AlliesSuccActionsNodeDict ):
            WhichActionNodeDictList.append( self.AlliesSuccActionsNodeDict )
            WhichTeamList.append( 0 )  # allies

        enemiesUnnovelNum = 0
        for actionNode in self.EnemiesSuccActionsNodeDict.values():
            if not actionNode.novel:
                enemiesUnnovelNum += 1
        if enemiesUnnovelNum == len( self.EnemiesSuccActionsNodeDict ):
            WhichActionNodeDictList.append( self.EnemiesSuccActionsNodeDict )
            WhichTeamList.append( 1 )  # allies

        '''Observe that all unnovel owing to which agent'''
        #print "whichTeam",WhichTeam
        AgentFaultList = []
        for WhichTeam, WhichActionNodeDict in zip( WhichTeamList, WhichActionNodeDictList ):

            cause = set([0, 1])
            for actionkey,eachActionNode in WhichActionNodeDict.items():
                #print actionkey,eachActionNode.unnovelCause
                cause = cause & set(eachActionNode.unnovelCause)

            if WhichTeam == 0:
                if len(cause) == 0:
                    AgentFaultList.extend( self.allies )
                else:
                    for agentIndex in cause:
                        AgentFaultList.append( self.allies[agentIndex] )
            else:
                if len(cause) == 0:
                    AgentFaultList.extend( self.enemies )
                else:
                    for agentIndex in cause:
                        AgentFaultList.append( self.enemies[agentIndex] )

        return AgentFaultList
  
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
                raise Exception( "The ChosedAction for generate successive StateNode is None( AlliesAction or EnemiesAction)  " )
            AlliesActionNode = self.AlliesSuccActionsNodeDict.get( ChosedAlliesAction )            
            if AlliesActionNode is None:
                AlliesActionNode = ActionNode( self.allies, self.enemies, ChosedAlliesAction, self )
                self.AlliesSuccActionsNodeDict[ ChosedAlliesAction ] = AlliesActionNode
            EnemiesActionNode = self.EnemiesSuccActionsNodeDict.get( ChosedEnemiesAction )
            if EnemiesActionNode is None:
                EnemiesActionNode = ActionNode( self.enemies, self.allies, ChosedEnemiesAction, self )
                self.EnemiesSuccActionsNodeDict[ ChosedEnemiesAction ] = EnemiesActionNode 
            ### The format of AlliesActionNode and EnemiesAcrionNode should be dict instead of list!
            ### What if the same EnemiesActionNode ?  
            AlliesActions = dict( zip( self.allies, ChosedAlliesAction ) )
            EnemiesActions = dict( zip( self.enemies, ChosedEnemiesAction ) )
            SuccStateNode = StateNode( AlliesActions = AlliesActions, EnemiesActions = EnemiesActions,\
                            AlliesActionNodeParent = AlliesActionNode, EnemiesActionNodeParent = EnemiesActionNode, StateParent = self )
            self.SuccStateNodeDict[ ChosedActions ] = SuccStateNode
        else:
            SuccStateNode = self.SuccStateNodeDict.get( ChosedActions )   
            
        return SuccStateNode

    ### Judge whether near to each other
    def nearToEnemies(self):
        nearPairs = []
        nearAllies = set()
        nearEnemies = set()
        for i in self.allies:
            for j in self.enemies:
                dis = self.getDistancer(self.IndexPositions[i],self.IndexPositions[j])
                if dis <= 2:
                    nearPairs.append((i,j))
                    nearAllies.add(i)
                    nearEnemies.add(j)
        return (nearPairs,nearAllies,nearEnemies)

    ### Expand the StateNode fully 
    ### Del those unnovel nodes( replace them with instances of ReplaceNode )
    ### return the list of NovelSuccStateNode 
    def FullExpandFunc( self ):
        if not self.isFullExpand():
            for actions in self.LegalActions:
                self.ChooseSuccNode( actions )

        #if not self.novelTest:
            nearResult = self.nearToEnemies()
            if len(nearResult[1]) == 2 and len(nearResult[2]) == 2:
                cacheMemory = self.StateParent.cacheMemory
            elif len(nearResult[1]) == 0 and len(nearResult[2]) == 0:
                allMemory1 = self.NoveltyTestSuccessorsV1(0)
                allMemory2 = self.NoveltyTestSuccessorsV1(1)
                allMemory1.update(allMemory2)
                cacheMemory = allMemory1
            elif len(nearResult[1]) == 1 and len(nearResult[2]) == 1:
                allMemory1 = self.NoveltyTestSuccessorsV1(0, nearResult[0][0][0])
                allMemory2 = self.NoveltyTestSuccessorsV1(1, nearResult[0][0][1])
                allMemory1.update(allMemory2)
                cacheMemory = allMemory1
            elif len(nearResult[1]) == 1 and len(nearResult[2]) == 2:
                allMemory1 = self.NoveltyTestSuccessorsV1(0, nearResult[0][0][0])
                allMemory1.update({self.enemies[0]:self.StateParent.cacheMemory[self.enemies[0]], self.enemies[1]:self.StateParent.cacheMemory[self.enemies[1]]})
                cacheMemory = allMemory1
            elif len(nearResult[1]) == 2 and len(nearResult[2]) == 1:
                allMemory2 = self.NoveltyTestSuccessorsV1(1, nearResult[0][0][1])
                allMemory2.update({self.allies[0]: self.StateParent.cacheMemory[self.allies[0]], self.allies[1]: self.StateParent.cacheMemory[self.allies[1]]})
                cacheMemory = allMemory2
            else:
                raise Exception('Not possible condition')
            
            self.getSuccessorNovel( cacheMemory )  ###need to change

        NovelSuccActionStateNodeList = []
        for actions, SuccStateNode in self.SuccStateNodeDict.items():
            #if not SuccStateNode.novel:
                #rn = ReplaceNode( SuccStateNode.depth )
                #self.SuccStateNodeDict[ actions ] = rn
                #SuccStateNode.novel = False
                ### delete an instance of StateNode
                #del SuccStateNode
            #else:
            if SuccStateNode.novel:
                NovelSuccActionStateNodeList.append( ( SuccStateNode, actions ) ) 
        #if len(NovelSuccActionStateNodeList) == 0 and self.StateParent is None:
        #    print " The rootNode has no SuccStateNode! "
        #    print self.IndexPositions
        #    print cacheMemory
         
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
        for actions, SuccStateNode, _, _ in SortedNovelSuccStateNodeList:
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
        for actionKeys,eachStateSucc in self.SuccStateNodeDict.items():
            for eachAgent in eachStateSucc.allies + eachStateSucc.enemies:
                if eachAgent not in eachStateSucc.deadAgentList:
                    self.updateCacheMemory(eachStateSucc.cacheMemory, {eachAgent: cacheMemory[eachAgent]})
            if eachStateSucc.novel:
                if not eachStateSucc.AlliesActionParent.novel or not eachStateSucc.EnemiesActionParent.novel:
                    #self.SuccStateNodeDict[actionKeys] = ReplaceNode(eachStateSucc.depth)
                    eachStateSucc.novel = False
                #del eachStateSucc

    def updateCacheMemory(self, allMemory, addMemory):
        for eachKey in addMemory.iterkeys():
            allMemory[eachKey] = allMemory[eachKey] | addMemory[eachKey]
        return allMemory

    def NoveltyTestSuccessorsV1(self, character, ignore=-1):
        ###character : allies or enemies
        # 0 is allies
        # 1 is enemies
        ########
        if character == 0:
            ChildrenNone = self.AlliesSuccActionsNodeDict
            ourTeam = self.allies
        else:
            ChildrenNone = self.EnemiesSuccActionsNodeDict
            ourTeam = self.enemies
        this_atoms_tuples1 = self.generateTuples(ourTeam[0])
        this_atoms_tuples2 = self.generateTuples(ourTeam[1])

        ### cacheMemory is a list consist of set
        # print self.StateParent
        # print self.cacheMemory[character]
        if self.StateParent is None:
            '''
            if len( self.cacheMemory[ourTeam[0]] ) == 0 or len( self.cacheMemory[ourTeam[1]] ) == 0:
                self.cacheMemory[ourTeam[0]] = this_atoms_tuples1
                self.cacheMemory[ourTeam[1]] = this_atoms_tuples2
                print "refresh cacheMemory00000000000001111111111", self.cacheMemory
            elif len(self.cacheMemory[ourTeam[0]]) == 0:
                self.cacheMemory[ourTeam[0]] = this_atoms_tuples1
                self.cacheMemory = self.updateCacheMemory( self.cacheMemory, {ourTeam[1]:this_atoms_tuples2})
                print "refresh cacheMemory0000000000", self.cacheMemory
            elif len(self.cacheMemory[ourTeam[1]]) == 0:
                self.cacheMemory[ourTeam[1]] = this_atoms_tuples2
                self.cacheMemory = self.updateCacheMemory( self.cacheMemory, {ourTeam[0]:this_atoms_tuples1})
                print "refresh cacheMemory1111111111",self.cacheMemory
            else:
                self.cacheMemory = self.updateCacheMemory( self.cacheMemory, {ourTeam[0]:this_atoms_tuples1, ourTeam[1]:this_atoms_tuples2})
            '''
            self.cacheMemory = self.updateCacheMemory(self.cacheMemory,
                                                      {ourTeam[0]: set([this_atoms_tuples1]), ourTeam[1]: set([this_atoms_tuples2])})

        all_memory = defaultdict(set)
        parent_atoms_tuples = {ourTeam[0]:self.cacheMemory[ourTeam[0]], ourTeam[1]:self.cacheMemory[ourTeam[1]]}
        all_memory = self.updateCacheMemory(all_memory,parent_atoms_tuples)
        for actionKey,succ in ChildrenNone.items():
            # print succ.allies
            succ_atoms_tuples0 = succ.generateTuples(ourTeam[0])
            succ_atoms_tuples1 = succ.generateTuples(ourTeam[1])
            #print "succ_atoms_tuples0, succ_atoms_tuples1",succ_atoms_tuples0, succ_atoms_tuples1
            if ignore == -1:
                all_memory = self.updateCacheMemory(all_memory,{ourTeam[0]:set([succ_atoms_tuples0]), ourTeam[1]:set([succ_atoms_tuples1])})
                x = set([succ_atoms_tuples0]) - parent_atoms_tuples[ourTeam[0]]
                #print set([succ_atoms_tuples0])
                #print parent_atoms_tuples[ourTeam[0]]
                #print "x"*20,x
                if len(x) == 0:
                    succ.novel = False
                    parent1_cache_positions = [each[0] for each in parent_atoms_tuples[ourTeam[1]]]
                    if len(set([succ_atoms_tuples1[0]])-set(parent1_cache_positions)) == 0:
                        succ.unnovelCause = [0,1]
                    else:
                        succ.unnovelCause = [0]
                    continue
                else:
                    parent0_cache_positions = [each[0] for each in parent_atoms_tuples[ourTeam[0]]]
                    parent1_cache_positions = [each[0] for each in parent_atoms_tuples[ourTeam[1]]]
                    if len(set([succ_atoms_tuples0[0]]) - set(parent1_cache_positions)) == 0:
                        if len(set([succ_atoms_tuples1[0]]) - set(parent0_cache_positions)) == 0:
                            succ.novel = False
                            succ.unnovelCause = [0,1]
                            continue
                        elif len(set([succ_atoms_tuples1]) - parent_atoms_tuples[ourTeam[1]]) == 0:
                            succ.novel = False
                            succ.unnovelCause = [1]
                            continue
                    else:
                        if len(set([succ_atoms_tuples1]) - parent_atoms_tuples[ourTeam[1]]) == 0:
                            succ.novel = False
                            succ.unnovelCause = [1]
                            continue
            else:
                if ignore == ourTeam[0]:
                    all_memory = self.updateCacheMemory(all_memory, {ourTeam[1]:set([succ_atoms_tuples1])})
                    if len(set([succ_atoms_tuples1]) - parent_atoms_tuples[ourTeam[1]]) == 0:
                        succ.novel = False
                        succ.unnovelCause = [1]
                        continue
                elif ignore == ourTeam[1]:
                    all_memory = self.updateCacheMemory(all_memory, {ourTeam[0]:set([succ_atoms_tuples0])})
                    if len(set([succ_atoms_tuples0]) - parent_atoms_tuples[ourTeam[0]]) == 0:
                        succ.novel = False
                        succ.unnovelCause = [0]
                        continue

        return all_memory

class ActionNode( BasicNode ):

    def __init__(self, allies, enemies, Actions, StateParent, cause=[]):
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
        self.unnovelCause = cause
        '''
        []:for none
        [0]: agent0's fault
        [1]: agent1's fault
        [0,1]: both agent0 and agent1's fault
        '''

    def getLatentScore( self ):
        if self.LatentScore is not None:
            return self.LatentScore
        else:
            LatentScore = 0
            for index, action in zip( self.allies, self.LastActions ):
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














 



