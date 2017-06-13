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
from game import Directions, Actions
import game
import math
from util import nearestPoint
import copy
from collections import defaultdict, deque
from pathos import multiprocessing as mp
import sys
import numpy as np
import multiprocessing 
from nodes import StateNode, ActionNode
#from SimulateAgents import SimulateAgent, SimulateAgentV1
from Helper import Distancer, ParallelAgent, SimulateAgent, SimulateAgentV1
#import copy_reg
#import types
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
    print func_name, obj, cls
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
        return func.__get__(obj, cls)

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

class MCTSCaptureAgent(CaptureAgent):

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.allies = self.getTeam( gameState )
        if self.allies[0] != self.index:
            self.allies = self.allies[::-1]
        self.enemies = self.getOpponents( gameState )
        print self.allies, self.enemies
        self.MCTS_ITERATION = 10000
        self.ROLLOUT_DEPTH = 15
        self.LastRootNode = None
        self.M = 4
        self.count = 0 
        self.D = Distancer( gameState.data.layout )
        self.PositionDict = self.D.positions_dict
        self.getMazeDistance = self.D.getDistancer
       
        self.mgr = multiprocessing.Manager()
        self.PositionDictManager = self.mgr.dict()
        for k1 in self.PositionDict.keys():
            self.PositionDictManager[k1] = self.PositionDict[k1]
            #for k2 in self.PositionDict[k1].keys():
            #    val = self.PositionDict[k1][k2]
            #    PositionDictManager[k1][k2] = val
        
        #print "set Parallel"
        #print "simulate",self.PositionDict[(1.0,3.0)][(17,6)],self.PositionDictManager[(1.0,3.0)][(17,6)]
        #print type(self.PositionDict), type(self.PositionDictManager)
        #raise Exception
        self.ChildParallelAgent = ParallelAgent( self.allies, self.enemies, self.ROLLOUT_DEPTH,\
                                                 self.PositionDictManager, self.getMazeDistance )

    def TreeReuse( self, GameState):
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

    ### the following part is used to compute the number of leaf and noveltree in search tree
                    import Queue
                    Depth = 0 
                    CandidateStates = Queue.Queue()
                    root = self.rootNode
                    CandidateStates.put( ( root ) )
                    num = 0
                    novelnum = 0 
                    while not CandidateStates.empty():              
                        CurrentState = CandidateStates.get()
                        CurrentState.depth = CurrentState.depth - 1 
                        try: 
                            if CurrentState.isFullExpand() and CurrentState.depth > Depth:
                                Depth = CurrentState.depth
                        except:
                            pass  
                        num += 1
                        if CurrentState.novel:
                            novelnum += 1
                            #if CurrentState.nVisit == 0:
                            #    print self.rootNode.IndexPositions
                            #    raise Exception( "nVisit of some StateNode is 0")                           
                            for successor in CurrentState.SuccStateNodeDict.values():
                                CandidateStates.put( successor ) 
                    print "The Last Tree:"
                    print "leaf nodes:",num, "novel leaf nodes:",novelnum,"depth of the search tree:",Depth
                    self.leaf = num
                    self.novelleaf = novelnum

                    return self.rootNode
  
            self.leaf = None
            self.novelleaf = None   
            return None   

    def chooseAction( self, GameState):
        self.n = 0
        print "="* 25, "new process", "="*25
        start = time.time()
        self.rootNode = self.TreeReuse( GameState )
        if self.rootNode is None:
            print "The Last Trees is no use!"
            self.rootNode = StateNode(self.allies, self.enemies, GameState,  getDistancer = self.getMazeDistance)
            self.leaf is None
               
        else:
            print "The Last Tree is in use!" 
        print "=" * 50
        print "Start Position",self.rootNode.IndexPositions
        print "=" * 50  

        iters = 0
        running_time = 0.0
        if self.novelleaf is None or self.novelleaf < 2000:  
            while( iters < 40 and running_time < 60 ):        
                node = self.Select()
                if node is None:
                    print "Invalid Selections"
                    if node == self.rootNode or id(node) == id(self.rootNode):
                        raise Exception("MCTS/chooseAction: No Node in the tree is novel")
                    continue
                print "iters",iters, "select node position:", node.IndexPositions,               
                self.ParallelGenerateSuccNode( node )
                end = time.time()
                running_time = end - start
                iters += 1
             
        print "iters", iters  
        self.LastRootNode = self.rootNode
        bestActions = self.rootNode.getBestActions()
        bestAction = bestActions[0]
        print "="*50
        print "="*25,"basic condition of this step","="*25
        print "Positions:", self.rootNode.IndexPositions
        print "index:", self.index, "beseAction:", bestAction, "PlayOut Times:", self.n
        
        for Actions, SuccStateNode in self.rootNode.SuccStateNodeDict.items():
            AlliesActions, EnemiesActions = Actions
            AlliesActionNode = self.rootNode.AlliesSuccActionsNodeDict[AlliesActions]
            EnemiesActionNode = self.rootNode.EnemiesSuccActionsNodeDict[EnemiesActions]     
            if SuccStateNode.novel:
                print "-"*50
                try:
		    print Actions, SuccStateNode.IndexPositions, SuccStateNode.nVisit, SuccStateNode.totalValue / float(SuccStateNode.nVisit), SuccStateNode.novel
                    print "Allies", AlliesActionNode.nVisit, AlliesActionNode.totalValue / float( AlliesActionNode.nVisit) 
                    print "Enemies", EnemiesActionNode.nVisit, EnemiesActionNode.totalValue / float( EnemiesActionNode.nVisit )
		except:
		    print Actions, SuccStateNode.nVisit, SuccStateNode.totalValue, SuccStateNode.novel
		    
        print "=" * 50
        print "=" * 50
        return bestAction

    def Select( self ):

        currentNode = self.rootNode
        while True:
            if not currentNode.isFullExpand():
                return currentNode
            else:
                currentNode = currentNode.UCB1ChooseSuccNode()
                if currentNode is None:
                    #raise Exception( "No StateNode in tree is novel!")
                    return None 

    def TopKSuccStateNodeList( self, CurrentStateNode, PreActions = [] ):
        CandidataFTSSNL = list()
        NovelSuccStateNodeList = CurrentStateNode.FullExpandFunc()
        if len(NovelSuccStateNodeList) == 0:
            CurrentStateNode.novel = False
            return []
        SortedSuccStateNodes, LeftNum = CurrentStateNode.getSortedSuccStateNodes( self.M, PreActions )
        CandidataFTSSNL.extend( SortedSuccStateNodes )
        
        j = 0
        while( len(CandidataFTSSNL) > 0 and len( CandidataFTSSNL ) < self.M ):
            #print CandidataFTSSNL 
            #print j
            FirstStateNode, PreActions = CandidataFTSSNL.pop()
            NovelSuccStateNodeList = FirstStateNode.FullExpandFunc()
            if len(NovelSuccStateNodeList) == 0:
                FirstStateNode.novel = False
                continue
            SortedSuccStateNodes, LeftNum = FirstStateNode.getSortedSuccStateNodes( LeftNum, PreActions )           
            CandidataFTSSNL.extend( SortedSuccStateNodes )
            j += 1  

        if len(CandidataFTSSNL) == 0:
            CurrentStateNode.novel = False
            return []
        else:      
            return CandidataFTSSNL[-self.M:]
        
    def ParallelGenerateSuccNode(self, CurrentStateNode):
        NovelSuccActionStateNodeList = CurrentStateNode.FullExpandFunc() 
        if len( NovelSuccActionStateNodeList ) == 0:
            print "All children StateNode of the chosed StateNode is not novel"
            CurrentStateNode.novel = False
            return
        #print "Prepare Begin"
        print len(NovelSuccActionStateNodeList)
        TopKNovelSuccStateNodeList = [] 
        #i = 0
        t1 = time.time()
        for SuccStateNode, actions in NovelSuccActionStateNodeList:
            #i += 1
            #print i,"begin",actions
            TopKNovelSuccStateNodeList.extend( self.TopKSuccStateNodeList( SuccStateNode, [ actions, ] ) )
            #print i,"finish"
        t2 = time.time()
        print t2 - t1 
        #print "Prepare Finish" 
        #print "The number of branch is:", len(CurrentInfo)

        ### Parallel Begin
        if len( TopKNovelSuccStateNodeList ) > 200:
            t1 = time.time()
            print len(TopKNovelSuccStateNodeList) 
            CurrentInfo = []
            for SuccStateNode, ActionList in TopKNovelSuccStateNodeList:
                CurrentInfo.append( ( SuccStateNode.GameState, ActionList ) )
            ActionSeriesList = self.ChildParallelAgent.P1( CurrentInfo )
            t2 = time.time()
            print t2 - t1  
            #for ActionSeriesList in ActionSeriesLists:
            for ActionSeries in ActionSeriesList:
                EndStateNode = CurrentStateNode.update( ActionSeries )
                self.BackPropagate(EndStateNode)
        else:
            for info in TopKNovelSuccStateNodeList:
                _, EndStateNode = self.PlayOut3( info )
                #for EndStateNode in EndStateNodeList: 
                self.BackPropagate( EndStateNode )

    def PlayOut3( self, CurrentStateInfo ): 
        self.n += 1       
 
        CurrentStateNode, Action = CurrentStateInfo
        #time1 = time.time()
        n1 = SimulateAgent( self.allies[0], self.allies, self.enemies, CurrentStateNode.GameState, self.getMazeDistance )
        n2 = SimulateAgent( self.allies[1], self.allies, self.enemies, CurrentStateNode.GameState, self.getMazeDistance )
        m1 = SimulateAgent( self.enemies[0], self.enemies, self.allies, CurrentStateNode.GameState, self.getMazeDistance )
        m2 = SimulateAgent( self.enemies[1], self.enemies, self.allies, CurrentStateNode.GameState, self.getMazeDistance )
        
        iters = 0
           
        while iters < ( self.ROLLOUT_DEPTH - len( Action ) ):

            a1 = n1.chooseAction( CurrentStateNode.GameState )
            a2 = n2.chooseAction( CurrentStateNode.GameState )

            b1 = m1.chooseAction( CurrentStateNode.GameState )
            b2 = m2.chooseAction( CurrentStateNode.GameState )

            CurrentStateNode = CurrentStateNode.ChooseSuccNode(((a1, a2), (b1, b2)))

            iters += 1

        #time2 = time.time()
        #print Action, time2 - time1
        return Action, CurrentStateNode

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
        flag = 0    
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
            if currentNode == self.rootNode or id( currentNode ) == id( self.rootNode ):
                flag = 1
                
        if flag == 0:
            print "rootNode", self.rootNode.IndexPositions, endNode.IndexPositions
            raise Exception
       
