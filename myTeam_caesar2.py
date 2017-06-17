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
        first = 'Caesar'
    elif firstIndex < 4:
        first = 'Caesar1'
    if secondIndex < 2:
        second = 'Caesar'
    else:
        second = 'Caesar1'
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
        print "self.index", self.index
        CaptureAgent.registerInitialState(self, gameState)

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


class Caesar(ReflexCaptureAgent):
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
        return {'teammateDist': 0.670685525269193, 'closest-food': -2.4757255329635885, 'eats-capsules': 9.151090095372206,
                '#-of-dangerous-ghosts-1-step-away': -5.9359156068251435, 'eats-ghost': 1.6024076564176668,
                'invaders-1-step-away': 2.2753823928201524,'#-of-harmless-ghosts-1-step-away': -0.15556132085075183, 'stopped': -6.09968075796784,
                'eats-invader': 7.375147922205873, 'eats-food': 1.4164376623849293}


class Caesar1(ReflexCaptureAgent):
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
        return {'teammateDist': 2.3288358401737907, 'closest-food': -1.0886931940414803,
                'eats-capsules': 13.477959551487604, '#-of-dangerous-ghosts-1-step-away': -23.049701530623054,
                'eats-ghost': 0.8669584765237215, 'invaders-1-step-away': 1.516349279877483,
                '#-of-harmless-ghosts-1-step-away': 3.2681732714016074, 'stopped': -5.403057778510077,
                'eats-invader': 9.366224198321031, 'eats-food': 0.8724156679043709}


class Caesar2(ReflexCaptureAgent):
    def registerInitialState(self, origin, givenWeights):
        if origin is True:
            self.setWeights = {}
            self.randomWeights()
        else:
            self.setWeights = givenWeights

    def randomWeights(self):
        self.setWeights['eats-invader'] = round(random.random() * 10, 2)
        self.setWeights['invaders-1-step-away'] = round(random.random() * 5, 2)
        self.setWeights['teammateDist'] = round(random.random() * 5, 2)
        self.setWeights['closest-food'] = round(-random.random() * 5, 2)
        self.setWeights['eats-capsules'] = round(random.random() * 20, 2)
        self.setWeights['#-of-dangerous-ghosts-1-step-away'] = round(-random.random() * 40, 2)
        self.setWeights['eats-ghost'] = round(random.random() * 3, 2)
        self.setWeights['#-of-harmless-ghosts-1-step-away'] = round(random.random(), 2)
        self.setWeights['stopped'] = round(-random.random() * 10, 2)
        self.setWeights['eats-food'] = round(random.random() * 3, 2)

    def mybin(self, float, bit=10):
        """ 
        这个程序用来将十进制数转化为二进制数,也可以转化浮点数 
        用法: mybin(float, bit=10) 
        float是指要转化的十进制数，可以为浮点数 
        bit是用来指定小数点后面的位数，默认为10位。 
        函数返回字符串 
        """
        negative = 0
        if float < 0:
            negative = 1
            float = -1 * float
        integer = int(float)  # 整数部分
        decimal = Decimal(str(float)) - integer  # 小数部分
        integer_convert = ""  # 转化后的整数部分
        decimal_convert = ""  # 转化后的小数部分
        binary = ""  # 最后的二进制数

        if integer == 0:
            binary = "0"
        else:
            while integer != 0:
                result = int(integer % 2)
                integer = integer / 2
                integer_convert = str(result) + integer_convert
            if decimal == 0:
                binary = integer_convert
            else:
                i = 0
                while decimal != 0 and i < bit:
                    result = int(decimal * 2)
                    decimal = decimal * 2 - result
                    decimal_convert = decimal_convert + str(result)
                    i = i + 1
                binary = integer_convert + '.' + decimal_convert

        if negative == 1:
            binary = '-' + binary
        return binary

    def mydec(self, binary):
        """ 
        将二进制数变成十进制数，包括浮点数 
        用法：mydec(binary) 
        binary是一个字符型二进制数，可以是浮点数 
        返回一个浮点数或者整数 
        """
        negative = 0
        if binary[0] == '-':
            negative = 1
            binary = binary[1:]
        integer = ""
        decimal = ""
        dot = binary.find('.')
        if dot == -1:
            integer = binary
        else:
            integer = binary[:dot]
            decimal = binary[dot + 1:]

        cnt1 = integer.__len__()
        cnt2 = decimal.__len__()
        if cnt1 != 0:
            temp = 0
            index_reverse = range(0, cnt1)
            for i in index_reverse:
                temp = temp + int(integer[i]) * (2 ** (cnt1 - i - 1))
            integer = temp
        else:
            integer = 0
        if cnt2 != 0:
            temp = 0
            index = range(1, cnt1 + 1)
            for i in index:
                temp = temp + int(decimal[i - 1]) * (2 ** (-1 * i))
            decimal = temp
        else:
            decimal = 0

        result = integer + decimal
        if negative == 1:
            result = -1 * result

        return result

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
        return self.setWeights


