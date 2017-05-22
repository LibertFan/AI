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
               first='MCTSCaptureAgent', second='MCTSCaptureAgent'):
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
    # return [eval(first)(firstIndex), eval(second)(secondIndex)]
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########
class ExploreNode:
    def __init__(self, GameState, cooperators_index, parent=None, last_action=None):
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
        self.C = math.sqrt(2)
        self.novel = True
        self.cacheMemory = None

    def getLegalActions(self):
        IndexActions = []
        for index in self.cooperators_index:
            actions = (self.GameState).getLegalActions(index)
            IndexActions.append(actions)
        return tuple(itertools.product(IndexActions[0], IndexActions[1]))

    def AddChildNode(self, action, Child_Node):
        if self.Children_Nodes.get(action) is not None:
            return
        else:
            self.Children_Nodes[action] = Child_Node

    def isFullExpand(self):
        if len(self.Children_Nodes) < len(self.LegalActions):
            self.FullExpand = False
        else:
            self.FullExpand = True

    def RandGenerateSuccNode(self):
        self.nVisit += 1
        Rands = []
        for action in self.LegalActions:
            if self.Children_Nodes.get(action) is None:
                Rands.append(action)
        actions = random.choice(Rands)
        newGameState = copy.deepcopy(self.GameState)
        for index, action in zip(self.cooperators_index, actions):
            newGameState = newGameState.generateSuccessor(index, action)
        SuccNode = ExploreNode(newGameState, self.cooperators_index, self)
        self.AddChildNode(actions, SuccNode)

        return SuccNode

    def RandChooseSuccNode(self):
        self.nVisit += 1
        actions = random.choice(self.LegalActions)
        """
    if self.Children_Nodes.get( actions ) is not None, then we can obviously see that
    the childNode is 
    """
        if self.Children_Nodes.get(actions) is not None:
            SuccNode = self.Children_Nodes.get(actions)
        else:
            newGameState = copy.deepcopy(self.GameState)
            for index, action in zip(self.cooperators_index, actions):
                newGameState = newGameState.generateSuccessor(index, action)

            SuccNode = ExploreNode(newGameState, self.cooperators_index, self)
            if self.Children_Nodes.get(actions) is None:
                self.AddChildNode(actions, SuccNode)
        return SuccNode

    def UCB1SuccNode(self):
        if not self.FullExpand:
            return None
        else:
            self.nVisit += 1
            SuccNode = None
            min_score = 9999
            print 'self',self.novel
            for i,child_node in enumerate(self.Children_Nodes.values()):
                print i,child_node.novel
                if child_node.novel:
                    score = child_node.totalValue / float(child_node.nVisit) + self.C * math.sqrt(
                        math.log(self.nVisit) / child_node.nVisit)
                    if score < min_score:
                        min_score = score
                        SuccNode = child_node
            return SuccNode

    def getBestAction(self):
        highest_score = 0
        best_action = None
        for action, child_node in self.Children_Nodes.items():
            if child_node.totalValue >= highest_score:
                highest_score = child_node.totalValue / float(child_node.nVisit)

                best_action = action
        # print highest_score
        return best_action

    def getSupScore(self, enemies, getMazeDistance):
        weights = self.getWeights()
        features = self.getFeatures(enemies, getMazeDistance)
        # print features
        lower_bound = self.Bound[0]
        upper_bound = self.Bound[1]
        return (features * weights - lower_bound) * 0.5 / (upper_bound - lower_bound)

    def getFeatures(self, enemies, getMazeDistance):
        features = util.Counter()
        self.red = self.GameState.isOnRedTeam(self.cooperators_index[0])
        if self.red:
            foodList = self.GameState.getBlueFood().asList()
        else:
            foodList = self.GameState.getRedFood().asList()
        features['successorScore'] = len(foodList)

        if len(foodList) > 0:  # This should always be True,  but better safe than sorry
            for index in self.cooperators_index:
                myPos = self.GameState.getAgentState(index).getPosition()
                minDistance = min([getMazeDistance(myPos, food) for food in foodList])
                features['distanceToFood' + str(index)] = minDistance

        enemies = [self.GameState.getAgentState(i) for i in enemies]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        # print len(invaders)
        features['numInvaders'] = len(invaders)

        for index in self.cooperators_index:
            myState = self.GameState.getAgentState(index)
            myPos = myState.getPosition()
            if myState.isPacman:
                features['onDefense' + str(index)] = 1
                if len(invaders) > 0:
                    dists = [getMazeDistance(myPos, a.getPosition()) for a in invaders]
                    features['invaderDistance' + str(index)] = min(dists)
            else:
                features['onDefense' + str(index)] = 0

        self.features = features
        return features

    def getWeights(self):
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
        weights = {'successorScore': -1, 'numInvaders': -20}

        for index in self.cooperators_index:
            weights['onDefense' + str(index)] = 20
            weights['distanceToFood' + str(index)] = -1
            weights['invaderDistance' + str(index)] = -1

        return weights

    def getBound(self):
        if self.parent is not None:
            return self.parent.Bound
        else:
            weights = self.getWeights()
            features1 = util.Counter()
            features1["onDefense"] = 2

            features2 = util.Counter()
            red = self.GameState.isOnRedTeam(self.cooperators_index[0])
            if red:
                foodList = self.GameState.getBlueFood().asList()
            else:
                foodList = self.GameState.getRedFood().asList()
            features2['successorScore'] = len(foodList)

            for index in self.cooperators_index:
                features2['onDefense' + str(index)] = 2
                features2['distanceToFood' + str(index)] = 50
                features2['invaderDistance' + str(index)] = 50

            features2["numInvaders"] = 2

            return [features2 * weights, features1 * weights]

    def getNoveltyFeatures(self):
        """
    Here we need to consider the layout
    """
        gameState = self.Children_Nodes.values()[0].GameState

        features = []
        for i,agent in enumerate(gameState.data.agentStates):
            features.append(('agent'+str(i),agent.getPosition()))

        for j,position in enumerate(gameState.data.capsules):
            features.append(('capsule'+str(j),position))

        food = gameState.data.food.asList()
        for position in food:
            features.append(('food:',position))
        return features

    def generateTuples(self):
        #features_list = self.getNoveltyFeatures()
        features_list = self.getNoveltyFeatures()
        atoms_tuples = set()
        for i in range(1, 3):
            atoms_tuples = atoms_tuples | set(itertools.combinations(features_list, i))
        return atoms_tuples

    def computeNovelty(self, tuples_set, all_tuples_set):
        diff = tuples_set - all_tuples_set
        if len(diff)>0:
            novelty = min([len(each) for each in diff])
            return novelty
        else:
            return 9999

    def getScore(self):
        if self.GameState.isRed:
            return self.GameState.getScore()
        else:
            return self.GameState.getScore() * -1

    def NoveltyTestSuccessors(self):
        threshold = 2
        if not self.FullExpand:
            print "this node is not fully expanded"
            return None
        else:
            all_atoms_tuples = set()
            this_atoms_tuples = self.generateTuples()
            all_atoms_tuples = all_atoms_tuples | this_atoms_tuples
            if self.parent is None and self.cacheMemory is None:
                self.cacheMemory = this_atoms_tuples

            for each_succ in self.Children_Nodes.values():
                succ_atoms_tuples = each_succ.generateTuples()
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

            for succ in self.Children_Nodes.values():
                if succ.getScore() > self.getScore():
                    succ.novel = True

            for succ in self.Children_Nodes.values():
                succ.cacheMemory = all_atoms_tuples



class MCTSCaptureAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.allies = self.getTeam(gameState)
        if self.allies[0] != self.index:
            self.allies = self.allies[::-1]
            # print self.allies
        self.enemies = self.getOpponents(gameState)
        self.MCTS_ITERATION = 10000
        self.ROLLOUT_DEPTH = 5

    def chooseAction(self, GameState):
        """ 
    we return the best a ction for current GameState. 
    we hope to return the best two action for two pacman! 
    """
        start = time.time()
        self.rootNode = ExploreNode(GameState, self.allies, None)
        node = self.rootNode
        iters = 0
        running_time = 0.0
        while (running_time < 0.9 and iters < self.MCTS_ITERATION):
            node = self.Select()
            EndNode = self.PlayOut(node)
            self.BackPropagate(EndNode)
            end = time.time()
            running_time = end - start
            iters += 1

        bestActions = (self.rootNode).getBestAction()
        return bestActions[0]

    def Select(self):
        currentNode = self.rootNode
        while True:
            currentNode.isFullExpand()
            if not currentNode.FullExpand:
                return currentNode.RandGenerateSuccNode()
            else:
                currentNode.NoveltyTestSuccessors()
                currentNode = currentNode.UCB1SuccNode()

    def PlayOut(self, CurrentNode):
        iters = 0
        while iters < self.ROLLOUT_DEPTH:
            CurrentNode = CurrentNode.RandChooseSuccNode()
            EnemyNode = ExploreNode(CurrentNode.GameState, self.enemies)
            NextNode = EnemyNode.RandChooseSuccNode()
            CurrentNode.GameState = NextNode.GameState
            iters += 1
        return CurrentNode

    def BackPropagate(self, endNode):
        score = self.getScore(endNode.GameState)
        if score == self.getScore(self.rootNode.GameState):
            supscore = endNode.getSupScore(self.enemies, self.getMazeDistance)
            score += supscore
        currentNode = endNode
        while currentNode is not None:
            currentNode.totalValue += score
            currentNode = currentNode.parent





















