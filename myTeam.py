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
    self.Children_Nodes = {}
    self.FullExpand = False  
    self.C = math.sqrt(2)
    self.novel = True
    self.cacheMemory = None
  
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

  def RandALLSuccNode(self):
    self.nVisit += 1
    actions = random.choice(self.LegalActions)
    newGameState = copy.deepcopy(self.GameState)
    for index, action in zip(self.cooperators_index, actions):
      newGameState = newGameState.generateSuccessor(index, action)

    SuccNode = ExploreNode(newGameState, self.cooperators_index, self)
    if self.Children_Nodes.get(actions) is None:
      self.AddChildNode(actions, SuccNode)
    return SuccNode

  def generateTuples(self, node):
    # get all features representation
    features_list = []
    atoms_tuples = set()
    for i in range(1,len(features_list)+1):
      atoms_tuples = atoms_tuples | set(itertools.combinations(features_list, i))
    return atoms_tuples

  def computeNovelty(self,tuples_set,all_tuples_set):
    diff = tuples_set - all_tuples_set
    novelty = min([len(each) for each in diff])
    return len(diff)

  def getScore(self, node):
    if node.isRed:
      return node.gameState.getScore()
    else:
      return node.gameState.getScore() * -1

  def NoveltyTestSuccessors(self):
    threshold = 1
    node = self
    if not node.FullExpand:
      print "this node is not fully expanded"
      return None
    else:
      all_atoms_tuples = set()
      this_atoms_tuples = self.generateTuples(node)
      all_atoms_tuples = all_atoms_tuples | this_atoms_tuples

      for each_succ in node.Children_Nodes.values():
        succ_atoms_tuples = self.generateTuples(each_succ)
        novelty = self.computeNovelty(succ_atoms_tuples, all_atoms_tuples)
        if novelty > threshold:
          each_succ.novel = False
        else:
          p = each_succ.parent
          while p is not None:
            parent_atoms_tuples = p.cacheMemory
            novelty = self.computeNovelty(succ_atoms_tuples, parent_atoms_tuples)
            if novelty > threshold:
              each_succ.novel = False
              break
            p = p.parent
        all_atoms_tuples = all_atoms_tuples | succ_atoms_tuples

      for succ in node.Children_Nodes.values():
        if self.getScore(succ) > self.getScore(node):
          succ.novel = True

      num_novelty = 0
      for succ in node.Children_Nodes.values():
        succ.cacheMemory = all_atoms_tuples
        if not succ.novel:
          num_novelty += 1
      if num_novelty == len(node.Children_Nodes):
        node.novel = False

  def UCB1SuccNode( self ):  
    if not self.FullExpand:  
      return None
    else:
      self.nVisit += 1
      SuccNode = None
      min_score = 9999
      for child_node in self.Children_Nodes.values():
        if child_node.novel == True:
          score = child_node.totalValue / float( self.nVisit ) + self.C * math.sqrt( math.log( self.nVisit ) / child_node.nVisit )
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
    #print highest_score    
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

    #if a higher score, store it
    #only horizontal or vertical

    def Select():
      currentNode = self.rootNode
      while True:
        currentNode.isFullExpand()  
        if not currentNode.FullExpand:
          return currentNode.RandSuccNode() 
        else:
          currentNode.NoveltyTestSuccessors()
          currentNode = currentNode.UCB1SuccNode()
          
    def PlayOut( CurrentNode ):
      iters = 0
      while iters < self.ROLLOUT_DEPTH:
        CurrentNode = CurrentNode.RandALLSuccNode()
        EnemyNode = ExploreNode( CurrentNode.GameState, self.enemies )
        EnemyNode.RandALLSuccNode()
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
       node = self.Select()
       EndNode = self.PlayOut( node )
       self.BackPropagate( EndNode )       
       end = time.time()
       running_time = end - start
       iters += 1    
    bestActions = (self.rootNode).getBestAction()
    return bestActions[0]

      
