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
class ExploreNode:
  def __init__( self, GameState, cooperators_index, parent = None, last_action = None ):
    """
    the order of indexes of allies and enemies are also important!
    In the process of playing out, the value of nVisit should increment ?
    """      
    self.GameState = GameState  
    self.cooperators_index = cooperators_index
    self.totalValue = 0.0
    self.nVisit = 1
    self.parent = parent
    self.LegalActions = self.getLegalActions()
    self.Children_Nodes = {}
    self.last_action = last_action
    self.Bound = self.getBound()
    self.C = math.sqrt(2)/10
    self.novel = True
    self.cacheMemory = None
    self.red = self.GameState.isOnRedTeam( self.cooperators_index[0] )
    self.positions = []
    for index in self.cooperators_index:
      self.positions.append( self.GameState.getAgentState( index ).getPosition() )  

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
    
    return self.FullExpand
  
  def RandGenerateSuccNode( self ): 
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
 
  def ChooseSuccNode( self, actions):
    """
    if self.Children_Nodes.get( actions ) is not None, then we can obviously see that
    the childNode is 
    """
    if self.Children_Nodes.get( actions ) is not None:
      SuccNode = self.Children_Nodes.get( actions )
    else:     
      newGameState = copy.deepcopy(self.GameState)
      for index, action in zip(self.cooperators_index, actions):
        try:  
          newGameState = newGameState.generateSuccessor(index, action)
        except:
          print index, action
          raise Exception( "Illigal action" )

      SuccNode = ExploreNode( newGameState, self.cooperators_index, self )
      if self.Children_Nodes.get(actions) is None:
        self.AddChildNode(actions, SuccNode)
    return SuccNode

  def RandChooseSuccNode( self ):
    self.nVisit += 1
    actions = random.choice(self.LegalActions)
    """
    if self.Children_Nodes.get( actions ) is not None, then we can obviously see that
    the childNode is 
    """
    if self.Children_Nodes.get( actions ) is not None:
      SuccNode = self.Children_Nodes.get( actions )
    else:     
      newGameState = copy.deepcopy(self.GameState)
      for index, action in zip(self.cooperators_index, actions):
        newGameState = newGameState.generateSuccessor(index, action)

      SuccNode = ExploreNode(newGameState, self.cooperators_index, self )
      if self.Children_Nodes.get(actions) is None:
        self.AddChildNode(actions, SuccNode)
    return SuccNode
    
  def UCB1SuccNode( self ):  
    if not self.isFullExpand():  
      return None
    else:
      self.nVisit += 1
      SuccNode = None
      max_score = 0
      un_novel_num = 0
      for child_node in self.Children_Nodes.values():
        #print child_node.novel  
        if child_node.novel:
          score = child_node.totalValue / float( child_node.nVisit ) + self.C * math.sqrt( math.log( self.nVisit ) / child_node.nVisit )
          if score >= max_score:
            max_score = score
            SuccNode = child_node
        else:
          un_novel_num += 1
      if un_novel_num == len(self.Children_Nodes):
          self.novel = False
      '''
      if SuccNode is None:
        print "*"*50
        for actions, child_node in self.Children_Nodes.items():
          print self.cooperators_index, child_node.positions 
          print actions  
          print child_node.cacheMemory
          print "*"*50
        print "*"*50
        p = self
        while p is not None:
          print p.positions
          p = p.parent
        print "*"*50
        
        raise Exception("All succNode is not novel!")  
      '''
      return SuccNode

  def getBestAction( self ):
    """
    Whether we need to consider novelty here ?
    """
    highest_score = 0
    best_action = None
    for action, child_node in self.Children_Nodes.items():
      if child_node.novel:
          score = child_node.totalValue / child_node.nVisit
          if score >= highest_score:
            highest_score = score
            best_action = action
        #print highest_score
    return best_action    

  def getSupScore( self, enemies, distancer_layout, getMazeDistance ):
    weights = self.getWeights()  
    features = self.getFeatures( enemies, distancer_layout, getMazeDistance )                        
    #print features
    lower_bound = self.Bound[0]
    upper_bound = self.Bound[1]
    return ( features * weights - lower_bound ) * 0.5 / ( upper_bound - lower_bound) 

  def getFeatures( self, enemies, distancer_layout, getMazeDistance ):
    features = util.Counter()
    if self.red:
      foodList = self.GameState.getBlueFood().asList()
    else:
      foodList = self.GameState.getRedFood().asList()          
    features['successorScore'] = len(foodList)
    
    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      for index in self.cooperators_index:
        myPos = self.GameState.getAgentState(index).getPosition()
        """
        Replace getMazeDistance with distancer_layout
        """
        minDistance = distancer_layout.min_position_distance( myPos, foodList )
        minDistance1 = min([getMazeDistance(myPos, food) for food in foodList] )
        if minDistance != minDistance1:
          raise Exception("discriniment in distancer_layout.min_position_distance and getMazeDistance!")
        features['distanceToFood' + str(index)] = minDistance 
 
    enemies = [self.GameState.getAgentState(i) for i in enemies]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    #print len(invaders)
    features['numInvaders'] = len(invaders)
    
    for index in self.cooperators_index:
      myState = self.GameState.getAgentState(index)
      myPos = myState.getPosition()
      if myState.isPacman: 
        features['onDefense'+ str(index)] = 1
        if len(invaders) > 0:
          """
          Replace get MazeDistance with distancer_layout
          """
          invaders_positions = [ a.getPosition() for a in invaders ]
          mindist = distancer_layout.min_position_distance( myPos, invaders_positions )
          mindist1 = min([getMazeDistance(myPos, a) for a in invaders_positions])
          #print "compare", mindist, dists
          if mindist != mindist:
            raise Exception("mindist wrong!")
          features['invaderDistance' + str(index)] = mindist1          
      else: 
        features['onDefense'+ str(index)] = 0  
                 
    self.features = features          
    
    return features              

  def getWeights( self ):
    """
    Features we used here are:
        1. successorScore
        2. distanceToFood1 and distanceToFood2
        3. onDefense1 and onDefense2
        4. numInvaders
        5. invaderDistance1 and invaderDistance2 ( minimum distance to invaders )
           the score to invaderDistance should be positive.
           Only when the pacmac is oin their own field, they can compute this score.
        6. When the pacman in the opposite field, there is no effective computation 
           method to measure its behavior.
    """  
    weights = {'successorScore': -1, 'numInvaders': -20 }
   
    for index in self.cooperators_index:
      weights['onDefense' + str( index )] = 20
      weights['distanceToFood' + str( index )] = -1   
      weights['invaderDistance' + str( index )] = -1                 
    
    return weights

  def getBound( self ):
    if self.parent is not None:
      return self.parent.Bound
    else:  
      weights = self.getWeights()
      features1 = util.Counter()
      for index in self.cooperators_index:
        features1['onDefense' + str(index)] = 1 
             
      features2 = util.Counter()
      red = self.GameState.isOnRedTeam(self.cooperators_index[0])
      if red:
        foodList = self.GameState.getBlueFood().asList()
      else:
        foodList = self.GameState.getRedFood().asList()      
      features2['successorScore'] = len(foodList)
      
      for index in self.cooperators_index:
        features2['onDefense' + str( index )] = 2
        features2['distanceToFood' + str(index) ] = 50 
        features2['invaderDistance' + str(index) ] = 50           
    
      features2["numInvaders"] = 2                      
                
      return [features2 * weights, features1 * weights]  

  """
  The following parts are novelty computations!
  """
  def getNoveltyFeatures( self ):
    gameState = self.GameState
    features = []
    for i, agent in enumerate(gameState.data.agentStates):
      #print agent.getPosition()  
      features.append(('agent'+str(i), agent.getPosition())) 
    for j, position in enumerate(gameState.data.capsules):
      features.append(('capsule'+str(j),position))  
    food = gameState.data.food.asList()
    for position in food:
      features.append(('food',position)) 
    return features  

  def generateTuples(self):
    # get all features representation
    features_list = self.getNoveltyFeatures()
    atoms_tuples = set()
    """
    why 1~3?
    """
    #for i in range(1,len(features_list)+1):
    for i in range(1,3):
      atoms_tuples = atoms_tuples | set(itertools.combinations(features_list, i))
    #self.cacheMemory = self.cacheMemory | atoms_tuples  
    return atoms_tuples

  def computeNovelty(self, tuples_set, all_tuples_set):
    diff = tuples_set - all_tuples_set
    if len(diff) > 0:
      novelty = min([len(each) for each in diff])
      return novelty
    else:
      return 9999

  def getScore(self):
    if self.red:
      return self.GameState.getScore()
    else:
      return self.GameState.getScore() * -1

  def NoveltyTestSuccessors(self):
    threshold = 2
    if not self.isFullExpand():
      raise Exception("this node is not fully expanded that is not support Novelty computation!")
      #return None
    else:
      all_atoms_tuples = set()
      this_atoms_tuples = self.generateTuples()
      all_atoms_tuples = all_atoms_tuples | this_atoms_tuples
      """
      How to initilize the cachyMemory of the rootNode?
      """
      if self.parent is None and self.cacheMemory is None:
        self.cacheMemory = this_atoms_tuples

      sorted_childNones = []
      for succ in self.Children_Nodes.values():
        succ_atoms_tuples = succ.generateTuples()
        diff = len(succ_atoms_tuples - all_atoms_tuples)
        sorted_childNones.append((succ, diff))
      sorted_childNones = sorted(sorted_childNones, lambda x, y: -cmp(x[1], y[1]))

      for each_pair in sorted_childNones:
        each_succ = each_pair[0]
        succ_atoms_tuples = each_succ.generateTuples()
        novelty = self.computeNovelty(succ_atoms_tuples, all_atoms_tuples)
        if novelty > threshold:
          each_succ.novel = False
        else:
          p = each_succ.parent
          while p is not None:
            parent_atoms_tuples = p.cacheMemory
            if parent_atoms_tuples is None:
              raise Exception("parent_atom_tuple is None, which goes wrong!")  
            novelty = self.computeNovelty(succ_atoms_tuples, parent_atoms_tuples)
            if novelty > threshold:
              each_succ.novel = False
              break
            p = p.parent
        all_atoms_tuples = all_atoms_tuples | succ_atoms_tuples

      for succ in self.Children_Nodes.values():
        if succ.getScore() > self.getScore():
          succ.novel = True

      for succ in self.Children_Nodes.values():
        succ.cacheMemory = all_atoms_tuples  

class SingleExploreNode:

  def __init__(self, index, enemies, gameState, distancer_layout, getMazeDistance ):
    self.index = index
    self.start = gameState.getAgentPosition(self.index)
    self.getMazeDistance = getMazeDistance
    self.distancer_layout = distancer_layout
    self.isPacman = gameState.getAgentState(self.index).isPacman
    self.enemies = enemies

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)    

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    foodLeft = len(gameState.data.layout.food.asList())
     
    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction
      
    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    if self.isPacman:
      features = self.getDefensiveFeatures(gameState, action)
    else:
      features = self.getOffensiveFeatures(gameState, action)

    weights = self.getWeights(gameState, action)
    return features * weights

  def getOffensiveFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    """
    foodList can not be achieved by self.getFood!
    """
    foodList = gameState.data.layout.food.asList() 
    features['successorScore'] = -len(foodList)#self.getScore(successor)

    # Compute distance to the nearest food

    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      """
      We replace self.getMazeDistance with self.distancer_layout.min_position_distance 
      """
      minDistance = self.distancer_layout.min_position_distance( myPos, foodList)
      minDistance1 = min([self.getMazeDistance(myPos, food) for food in foodList])
      if minDistance != minDistance1:
        raise Exception("Value error!")  
      features['distanceToFood'] = minDistance1

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
      """
      Replace self.getMazeDistance with self.distancer_dict
      """
      invader_positions = [ a.getPosition() for a in invaders ]
      mindist = self.distancer_layout.min_position_distance( myPos, invaders_positions )
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders_positions]
      features['invaderDistance'] = mindist

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features
   
  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 100, 'distanceToFood': -1, 'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}

class distance_layout:

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
    """    
    print self.positions_dict
    print "="*50
    print len(self.positions_dict.keys())
    print self.positions
    """
  def construct_dict( self ):
    self.adj()
    
    for position2 in self.positions:
      for position1 in self.positions:
        for position3 in self.positions:
          self.positions_dict[ position1 ][ position3 ]\
          = min( self.positions_dict[ position1][position3],\
          self.positions_dict[ position1 ][ position2 ] +\
          self.positions_dict[ position2 ][ position3 ] )  
    """
    self.distancer_dict = dict()      
    for position in self.positions:
      self.distancer_dict[ position ] = defaultdict(int)
      sorted_distances = sorted( self.positions_dict[ position ].items(), lambda x, y: cmp( x[1], y[1] ) )
      for child_position, distance in sorted_distances:
        if self.distancer_dict[ position ].get( distance ) is None:
          self.distancer_dict[ position ][ distance ] = []
        self.distancer_dict[ position ][ distance ].append( child_position )
    """
  """
  We need to find the target that has the nearest distance from the start_position
  """
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


class MCTSCaptureAgent(CaptureAgent):
        
  def registerInitialState(self, gameState): 
    CaptureAgent.registerInitialState(self, gameState)   
    self.allies = self.getTeam( gameState )
    if self.allies[0] != self.index:
       self.allies = self.allies[::-1] 
    #print self.allies   
    self.enemies = self.getOpponents( gameState )
    self.MCTS_ITERATION = 10000
    self.ROLLOUT_DEPTH = 10
    """
    Prepare distance data for further computation!
    """
    self.distancer_layout = distance_layout( gameState.data.layout )
    #print self.distancer_layout.distancer_dict
    print type( self.distancer_layout )

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
       node = self.Select()
       if node is None:
           continue
       EndNode = self.PlayOut( node )
       self.BackPropagate( EndNode )       
       end = time.time()
       running_time = end - start
       iters += 1

    for action, succNode in self.rootNode.Children_Nodes.items(): 
      print action, succNode.nVisit, succNode.novel, succNode.totalValue / succNode.nVisit

      #print succNode.novel, succNode.cacheMemory
      print succNode.Children_Nodes.keys()
      print "-"*50

    bestActions = (self.rootNode).getBestAction()
    print iters, bestActions
    print self.rootNode.Bound
    print "=" * 50
    return bestActions[0]

  def Select( self ):
    currentNode = self.rootNode
    while True:
        if not currentNode.isFullExpand():
          return currentNode.RandGenerateSuccNode() 
        else:
          currentNode.NoveltyTestSuccessors()
          currentNode = currentNode.UCB1SuccNode()
          if currentNode is None:
              return None

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
      n1 = SingleExploreNode( self.allies[0], self.enemies, CurrentNode.GameState, self.distancer_layout, self.getMazeDistance ) 
      a1 = n1.chooseAction( CurrentNode.GameState )
      n2 = SingleExploreNode( self.allies[1], self.enemies, CurrentNode.GameState, self.distancer_layout, self.getMazeDistance )
      a2 = n2.chooseAction( CurrentNode.GameState )
      CurrentNode = CurrentNode.ChooseSuccNode( (a1,a2) ) 

      EnemyNode = ExploreNode( CurrentNode.GameState, self.enemies )
      n1 = SingleExploreNode( self.enemies[0], self.allies, CurrentNode.GameState, self.distancer_layout, self.getMazeDistance ) 
      a1 = n1.chooseAction( CurrentNode.GameState )
      n2 = SingleExploreNode( self.enemies[1], self.allies, CurrentNode.GameState, self.distancer_layout, self.getMazeDistance )
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
      
      

