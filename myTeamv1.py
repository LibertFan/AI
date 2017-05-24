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
        return 0

class StateNode( BasicNode):
	def __init__( self, allies = None, enemies = None, GameState = None, AlliesActions = dict(), OpponentsActions = dict(), AlliesActionParent = None, OpponentsActionParent = None, StateParent = None, getDistancer = None, getDistanceDict = None ):      	        
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
            self.LastActions = dict( AlliesActions, **OpponentsActions )
        except:
            raise Exception( " the format of AlliesActions and OpponentsAction go wrong!" )	
        self.StateParent = StateParent
        self.AlliesActionParent = AlliesActionParent
        self.OpponentsActionParent = OpponentsActionParent   
        if StateParent is None:     
            if getDistancer is None or allies is None or enemies is None:
                raise Exception( "the function of getDistancer or allies or enemies missing!")
            self.GameState = GameState
	    self.getDistancer = getDistancer
	    self.Bound = self.getBound()
            self.allies = allies
            self.enemies = enemies
        elif GameState is None:
	    self.StateParent = StateParent
            self.allies = self.StateParent.allies
            self.enemies = self.StateParent.enemies 
	    self.getDistancer = self.StateParent.getDistancer
	    self.Bound = self.StateParent.Bound
            self.Bound = self.getBound()
            CurrentGameState = copy.deepcopy( self.StateParent.GameState ) 
            for index, action in self.LastActions.items():
		CurrentGameState = CurrentGameState.generateSuccessor( index, action )
            self.GameState = CurrentGameState        
        # self.LegalIndexActions is an auxiliary variables that store a dict which key is the agent index 
        # and the value is its corresponding legal actions  
        self.LegalIndexActions = dict()
        self.IndexPositions = dict()
        for index in self.allies + self.enemies:
            self.LegalIndexActions[ index ] = self.GameState.getLegalActions( index )
            self.IndexPositions[ index ] = self.GameState.getAgentState( index ).getPosition() 
        # combine different actions for different indexes
        self.LegalAlliesActions = tuple( itertools.product( self.LegalIndexActions(self.allies[0]), self.LegalIndexActions(self.allies[1]) ) )    
        self.LegalEnemiesActions = tuple(itertools.product( self.LegalIndexActions(self.enemies[0]), self.LegalIndexActions(self.enemies[1]) ) ) 
        # self.LegalActions = self.LegalAlliesActions + self.LegalEnemiesActions
        # the following attributes 
        self.AlliesSuccActionsNode = dict()
  	self.EnemiesSuccActionsNode = dict()
	self.SuccStateNode = dict()	
        self.nVisit = 0.0
        self.totalValue = 0.0
        self.C1 = math.sqrt( 2 )
        self.red = self.GameState.isOnRedTeam( self.allies[0] )  
        self.novel = True
        self.cacheMemory = set()

    def getBestActions( self ):
	return 0        	 

    def isPruned( self ):
        """
        isPrune is related to the self.AlliesActionParent and self.OpponentsActionParent, 
        the return value is True or False.
        """
	if AlliesActionParent
	    return True	       

    def isFullExpand( self ):
		return 0

    def RandGenerateActions( self ):
        if self.isFullExpand():
            raise Exception( " This Node has been full Expanded, you should choose UCB1" )
        else:
            if len( self.LegalAlliesActions ) == len( self.AlliesSuccActionsNode.keys() ):
                ChosedAlliesAction = radom.choice( self.LegalAlliesActions )
            else:    
                PreparedAlliesAcitons = []
                for alliesAction in self.LegalAlliesActions:
                   if self.AlliesSuccActionsNode.get( alliesAction ) is None:
                       PrepareAlliesActions.append( alliesAction ) 
                ChosedAlliesAction = random.choice( PreparedAlliesActions )
                AlliesActionNode = ActionNode( self.allies, self.enemies, ChosedAction, self )
                self.AlliesSuccActions is 
              
            if self.  
            PreparedEnemoesActions = []
            for enemiesAction in self.LegalEnemiesActions:
                if self.EnemiesSuccActionsNode.get( enemoesAction ) is None:
                    PrepareEnemiesActions.append( enemiesAction )

        

    def UCB1ChooseSuccNode( self ):
	return 0  
   
    # GenerateSuccActionNode is used in 
    def GenerateSuccActionNode( self , actions ):
	return 0
    
    """
    RandGenerateSuccStateNode function is used in the condition when the node is not fully Expand, which means some certain action is still not be 
    taken that the corresponding child node has not been built. 
    """
    def RandGenerateSuccStateNode( self ):
	return 0
    
    """
    RandChooseSuccNode is used in the course of MCTS's playout,  
    """
    def RandChooseSuccNode( self ):
	return 0

    """
    The following method is used to compute the in the process of 
 
    getBound is used to scale the features value to interval [ 0, 0.5 ], and we name the final score as LatentScore!
    getFeatures is used to compute the features in 
    getWeights returns a dictionary that record the different features and their corresponding weight
    getLatentScore is used to 
    """
    def getBound( self ): 
	return 0

    def getFetures( self ):
	return 0

    def getWeights( self ):
	return 0

    def getLatentScore( self ):
	return 0    

    """
	The following functions are used to compute the novelty of an StateNode
    """
    def getScore( self ): 
	return 0

    def getNoveltyFeatures( self ):
	return 0

    def generateTuples( self ):
	return 0

    def computeNovelty( self, tuples_set, all_tuples_set):
	return 0

    def NoveltyTestSuccessors( self ):
	return 0

class ActionNode( BasicNode, ):
    def __init__( self, allies, enemies, Actions, StateParent ): 
	self.StateParent = StateParent
	self.allies = allies
	self.enemies = enemies
        self.LastActions  = Actions
        CurrentGameState = copy.deepcopy( StateParent.GameState )
        for index, action in zip( self.allies, self.LastActions):
             CurrentGameState = CurrentGameState.generateSuccessor( index, action )
        self.GameState = CurrentGameState    
        self.GameState = self.StateParent.GameState.
	self.getDistancer = self.StateParent.getDistancer
	self.novel = True
        self.cacheMemory = set()
    """
    The following method is used to novelty computation in order to prune 
    """
    def isPrune( self ):
        return 0

    """
    The following functions are used to compute the novelty of an StateNode
    """
    def getScore( self ): 
	return 0

    def getNoveltyFeatures( self ):
	return 0

    def generateTuples( self ):
	return 0

    def computeNovelty( self, tuples_set, all_tuples_set):
	return 0

    def NoveltyTestSuccessors( self ):
	return 0


class SimulateAgent:
	def __init__( self ):
    	return 0 

	def chooseAction(self, gameState):
		return 0

	def getSuccessor(self, gameState, action):
		return 0

	def evaluate(self, gameState, action):
		return 0

	def getOffensiveFeatures(self, gameState, action):
		return 0

	def getDefensiveFeatures(self, gameState, action):
		return 0

	def getWeights(self, gameState, action):
		return 0

class Distancer:
	def __init__( self ):
		return 0

class MCTSCaptureAgent(CaptureAgent):
        
  def registerInitialState(self, gameState): 
    CaptureAgent.registerInitialState(self, gameState)   
    self.allies = self.getTeam( gameState )
    if self.allies[0] != self.index:
       self.allies = self.allies[::-1]   
    self.enemies = self.getOpponents( gameState )
    self.MCTS_ITERATION = 10000
    self.ROLLOUT_DEPTH = 10

  def chooseAction( self, GameState ):
    """ 
    we return the best a ction for current GameState. 
    we hope to return the best two action for two pacman! 
    """    
    start = time.time()
    self.rootNode = ExploreNode( GameState, self.allies, None)
    node = self.rootNode
    iters = 0
    running_time = 0.0
    while( running_time < 10 and iters < self.MCTS_ITERATION ):
       node = self.select()
       EndNode = self.playOut( node )
       self.BackPropagate( EndNode )       
       end = time.time()
       running_time = end - start
       iters += 1
    """

    """
    return bestActions[0]

  def select( self ):
    currentNode = self.rootNode
    while True:
        if not currentNode.isFullExpand():
          return currentNode.RandGenerateSuccNode() 
        else:
          currentNode.NoveltyTestSuccessors()
          currentNode = currentNode.UCB1SuccNode()
  """
  gameState was transformed to Enenmy after modified by allies, thus 
  enemies knowns allies movement!
  """
  def PlayOut( self, CurrentNode ):
    iters = 0
    while iters < self.ROLLOUT_DEPTH:
      """
      In SingleExporeNode, Func self.distancer_layout is used
      """
      n1 = SingleExploreNode( self.allies[0], self.enemies, CurrentNode.GameState, self.getMazeDistance ) 
      a1 = n1.chooseAction( CurrentNode.GameState )
      n2 = SingleExploreNode( self.allies[1], self.enemies, CurrentNode.GameState, self.getMazeDistance )
      a2 = n2.chooseAction( CurrentNode.GameState )
      CurrentNode = CurrentNode.ChooseSuccNode( (a1,a2) ) 

      EnemyNode = ExploreNode( CurrentNode.GameState, self.enemies )
      n1 = SingleExploreNode( self.enemies[0], self.allies, CurrentNode.GameState, self.getMazeDistance ) 
      a1 = n1.chooseAction( CurrentNode.GameState )
      n2 = SingleExploreNode( self.enemies[1], self.allies, CurrentNode.GameState, self.getMazeDistance )
      a2 = n2.chooseAction( CurrentNode.GameState )
      NextNode = EnemyNode.ChooseSuccNode( (a1,a2) )
      CurrentNode.GameState = NextNode.GameState
      iters += 1      
    return CurrentNode 
 
  def PlayOut1( self, CurrentNode ):
    iters = 0
    while iters < self.ROLLOUT_DEPTH:
      CurrentNode = CurrentNode.RandChooseSuccNode()
      EnemyNode = ExploreNode( CurrentNode.GameState, self.enemies )
      NextNode = EnemyNode.RandChooseSuccNode()
      CurrentNode.GameState = NextNode.GameState
      iters += 1      
    return CurrentNode 

  def BackPropagate( self, endNode):
    """
    In ExploreNode.getSupScore, self.distance_layout is used!
    """
    score = self.getScore( endNode.GameState )
    if score == self.getScore( self.rootNode.GameState ):
      supscore = endNode.getSupScore( self.enemies, self.distancer_layout, self.getMazeDistance )
      score += supscore
    else:
      print "Oh My God", score  
    currentNode = endNode
    while currentNode is not None:
       currentNode.totalValue += score
       currentNode = currentNode.parent   

















