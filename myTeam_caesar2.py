# -*- coding: utf-8 -*-
# __author__ = 'siyuan'

# myTeam_caesar.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import random, time, util, sys
from game import Directions, Actions
from util import nearestPoint
from decimal import Decimal


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='OffensiveReflexAgent', second='DefensiveReflexAgent'):
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
    
    if firstIndex < 2:        
        first = 'BlueCaesarv1'
    elif firstIndex < 4:
        first = 'BlueCaesarv2'
    if secondIndex < 2:
        second = 'BlueCaesarv1'
    else:
        second = 'BlueCaesarv2'
    """
    if firstIndex < 2:        
        first = 'Caesarv3'
    elif firstIndex < 4:
        first = 'Caesarv4'
    if secondIndex < 2:
        second = 'Caesarv3'
    else:
        second = 'Caesarv4'
    """ 
    print first
    print second
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that chooses score-maximizing actions
    """

    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        #print "self.index", self.index
        CaptureAgent.registerInitialState(self, gameState)
        #print self.index, self.getWeights( gameState, "Stop")


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

        foodLeft = len(self.getFood(gameState).asList())

        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start, pos2)
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
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        """
        Returns a counter of features for the state
        """
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self, gameState, action):
        """
        Normally, weights do not depend on the gamestate.  They can be either
        a counter or a dictionary.
        """
        return {'successorScore': 1.0}


class OffensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that seeks food. This is an agent
    we give you to get an idea of what an offensive agent might look like,
    but it is by no means the best or only way to build an offensive agent.
    """

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        foodList = self.getFood(successor).asList()
        features['successorScore'] = -len(foodList)  # self.getScore(successor)

        # Compute distance to the nearest food

        if len(foodList) > 0:  # This should always be True,  but better safe than sorry
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance
        return features

    def getWeights(self, gameState, action):
        return {'successorScore': 100, 'distanceToFood': -1}


class DefensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free. Again,
    this is to give you an idea of what a defensive agent
    could be like.  It is not the best or only way to make
    such an agent.
    """

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)

        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        # Computes whether we're on defense (1) or offense (0)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0

        # Computes distance to invaders we can see
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = min(dists)

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def getWeights(self, gameState, action):
        return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}


class Caesarv3(ReflexCaptureAgent):
    def getFeatures(self, state, action):
        food = self.getFood(state)
        foodList = food.asList()
        walls = state.getWalls()
        isPacman = self.getSuccessor(state, action).getAgentState(self.index).isPacman

        # Zone of the board agent is primarily responsible for
        zone = (self.index - self.index % 2) / 2

        teammates = [state.getAgentState(i).getPosition() for i in self.getTeam(state)]
        opponents = [state.getAgentState(i) for i in self.getOpponents(state)]
        chasers = [a for a in opponents if not (a.isPacman) and a.getPosition() != None]
        prey = [a for a in opponents if a.isPacman and a.getPosition() != None]

        features = util.Counter()
        if action == Directions.STOP:
            features["stopped"] = 1.0
        # compute the location of pacman after he takes the action
        x, y = state.getAgentState(self.index).getPosition()
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
        if state.getAgentState(self.index).scaredTimer == 0:
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
                myMinDist = min([self.getMazeDistance((next_x, next_y), food) for food in myFood])
                if myMinDist is not None:
                    features["closest-food"] = float(myMinDist) / (walls.width * walls.height)

        features.divideAll(10.0)

        return features

    def getWeights(self, gameState, action):
        return {'teammateDist': -1.6395824002102957, 'closest-food': -3.4973081509764254, 'eats-capsules': 7.238652234996785,
                '#-of-dangerous-ghosts-1-step-away': -39.61086104504979, 'eats-ghost': -10.593381278815142,
                'invaders-1-step-away': 7.989671624181696, '#-of-harmless-ghosts-1-step-away': 11.180878459598198,
                'stopped': -5.258450995314007, 'eats-invader': 10.822719669376905, 'eats-food': 5.9309125137902114}



class Caesarv4(ReflexCaptureAgent):
    def getFeatures(self, state, action):
        food = self.getFood(state)
        foodList = food.asList()
        walls = state.getWalls()
        isPacman = self.getSuccessor(state, action).getAgentState(self.index).isPacman

        # Zone of the board agent is primarily responsible for
        zone = (self.index - self.index % 2) / 2

        teammates = [state.getAgentState(i).getPosition() for i in self.getTeam(state)]
        opponents = [state.getAgentState(i) for i in self.getOpponents(state)]
        chasers = [a for a in opponents if not (a.isPacman) and a.getPosition() != None]
        prey = [a for a in opponents if a.isPacman and a.getPosition() != None]

        features = util.Counter()
        if action == Directions.STOP:
            features["stopped"] = 1.0
        # compute the location of pacman after he takes the action
        x, y = state.getAgentState(self.index).getPosition()
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
        if state.getAgentState(self.index).scaredTimer == 0:
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
                myMinDist = min([self.getMazeDistance((next_x, next_y), food) for food in myFood])
                if myMinDist is not None:
                    features["closest-food"] = float(myMinDist) / (walls.width * walls.height)

        features.divideAll(10.0)

        return features

    def getWeights(self, gameState, action):
        return  {'teammateDist': -0.7739904026405786, 'closest-food': -0.3810123824558789,
                 'eats-capsules': 21.648755947859833, '#-of-dangerous-ghosts-1-step-away': 1.5588921806538147,
                 'eats-ghost': 5.533733315411954, 'invaders-1-step-away': 0.15723651886364845,
                 '#-of-harmless-ghosts-1-step-away': -5.050793272474184, 'stopped': -8.872050962861328,
                 'eats-invader': 7.023539875082848, 'eats-food': 5.914893900312887}

class BlueCaesarv1( Caesarv3 ):
    def getWeights( self, gameState, action ):
        return {'teammateDist': 4.194330087863693, 'closest-food': -4.542780932555895, 'eats-capsules': 4.36699040855961,
                '#-of-dangerous-ghosts-1-step-away': -1.213524627718394, 'eats-ghost': 1.8779111664875483,
                'invaders-1-step-away': 0.016256701411800467, '#-of-harmless-ghosts-1-step-away': -2.112397982585541,
                'stopped': -10.016134801388748, 'eats-invader': 10.672277359871996, 'eats-food': 2.007714754533258}

class BlueCaesarv2( Caesarv4 ):
    def getWeights( self, gameState, action ):
        return {'teammateDist': 2.7616129475787803, 'closest-food': -6.34089184938779, 'eats-capsules': 11.224762976653109,
                '#-of-dangerous-ghosts-1-step-away': -2.8038067666001965, 'eats-ghost': -0.8808169242759187,
                'invaders-1-step-away': 1.345931798887575, '#-of-harmless-ghosts-1-step-away': 4.1357164671898685, 
                'stopped': -15.681689977660952, 'eats-invader': 6.263093277373304, 'eats-food': -2.0651675890647927}








