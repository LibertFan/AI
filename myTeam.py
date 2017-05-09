# myTeam.py
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
class ExploreNode:
  def __init__( self, GameState, cooperators_index, parent = None ):
    """
    the order of indexes of allies and enemies are also important!
    In the process of playing out, the value of nVisit should increment ?
    """      
    self.GameState = GameState  
    self.cooperators_index = cooperators_index
    self.totalValue = 0.0
    self.nVisit = 0
    self.parent = parent
    self.LegalActions = self.getLegalActions()
    print len(self.LegalActions)
    self.Children_Nodes = {}
    self.FullExpand = False  
    self.C = math.sqrt(2)
  
  def getLegalActions( self ):
    IndexActions = []  
    for index in self.cooperators_index:  
      actions = (self.GameState).getLegalActions( index )
      IndexActions.append( actions )
    return tuple( itertools.product( IndexActions[0], IndexActions[1] ) ) 
  
  def AddChildNode( self, action, Child_Node ):
    if self.Children_Nodes.get( action ) is not None:
      return 
    else:  
      self.Children_Nodes[ action ] = Child_Node 
        
  def isFullExpand( self ):  
    if len( self.Children_Nodes ) < len( self.LegalActions ):
      self.FullExpand = False
    else:
      self.FullExpand = True
  
  def RandSuccNode( self ):
    """
    if self.FullNextExpand:
      return None     
    else:
    """  
    self.nVisit += 1
    Rands = []
    for action in self.LegalActions:
      if self.Children_Nodes.get( action ) is None:
        Rands.append( action ) 
    actions = random.choice( Rands )
    newGameState = copy.deepcopy( self.GameState )
    for index, action in zip( self.cooperators_index, actions ):
      newGameState = newGameState.generateSuccessor( index, action )
      
    SuccNode = ExploreNode( newGameState, self.cooperators_index, self )
    self.AddChildNode( actions, SuccNode)
    
    return SuccNode
    
  def UCB1SuccNode( self ):  
    if not self.FullExpand:  
      return None
    else:
      self.nVisit += 1
      SuccNode = None
      min_score = 9999
      for child_node in self.Children_Nodes.values():
        score = child_node.totalValue + self.C * math.sqrt( math.log( self.nVisit ) / child_node.nVisit )
        if score < min_score:
          min_score = score
          SuccNode = child_node
      return SuccNode

  def getBestAction( self ):
    highest_score = 0
    best_action = None
    for action, child_node in self.Children_Nodes.items():
      if child_node.totalValue >= highest_score:
        highest_score = child_node.totalValue / float( child_node.nVisit )
        best_action = action
    print highest_score    
    return best_action    
      
class MCTSCaptureAgent(CaptureAgent):
        
  def registerInitialState(self, gameState): 
    CaptureAgent.registerInitialState(self, gameState)   
    self.allies = self.getTeam( gameState )
    if self.allies[0] != self.index:
       self.allies = self.allies[::-1] 
    #print self.allies   
    self.enemies = self.getOpponents( gameState )
    self.MCTS_ITERATION = 10000
    self.ROLLOUT_DEPTH = 20

  def chooseAction( self, GameState ):
    """ 
    we return the best a ction for current GameState. 
    we hope to return the best two action for two pacman! 
    """    
    def Select():
      currentNode = self.rootNode
      while True:
        currentNode.isFullExpand()  
        if not currentNode.FullExpand:
          return currentNode.RandSuccNode() 
        else:
          currentNode = currentNode.UCB1SuccNode()
          
    def PlayOut( CurrentNode ):
      iters = 0
      while iters < self.ROLLOUT_DEPTH:
        CurrentNode = CurrentNode.RandSuccNode()
        EnemyNode = ExploreNode( CurrentNode.GameState, self.enemies )
        EnemyNode.RandSuccNode()
        CurrentNode.GameState = EnemyNode.GameState
        iters += 1      
      return CurrentNode      
    
    def BackPropagate( endNode ):
      score = self.getScore( endNode.GameState )
      print score
      currentNode = endNode
      while currentNode is not None:
        currentNode.totalValue += score
        currentNode = currentNode.parent 
    
    start = time.time()
    self.rootNode = ExploreNode( GameState, self.allies, None)
    node = self.rootNode
    iters = 0
    running_time = 0.0
    while( running_time < 0.9 and iters < self.MCTS_ITERATION ):
       node = Select()
       EndNode = PlayOut( node )
       BackPropagate( EndNode )       
       end = time.time()
       running_time = end - start
       iters += 1
    
    bestActions = (self.rootNode).getBestAction()
    return bestActions[0]
  """
  def Select( self ):
    currentNode = self.rootNode
    while True:
      if not currentNode.isFullExpand():
        return currentNode.RandSuccNode() 
        break                    
      else:
        currentNode = currentNode.UCB1SuccNode()
  """     
  """            
  def PlayOut( self, CurrentNode ):
    iters = 0
    while iters < self.ROLLOUT_DEPTH:
      CurrentNode = CurrentNode.RandSuccNode()
      print self.enemies
      EnemyNode = ExploreNode( copy.deepcopy( CurrentNode.GameState ), self.enemies )
      EnemyNode.RandSuccNode()
      CurrentNode.GameState = copy.deepcopy( EnemyNode.GameState )
      iters += 1
      
    return CurrentNode

  def BackPropagate( self, endNode):
    score = self.getScore( endNode.GameState )
    currentNode = endNode
    while currentNode is not None:
       currentNode.totalValue += score
       currentNode = currentNode.parent       
  """        
      



















