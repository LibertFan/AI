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
#from SimulateAgents import SimulateAgent, SimulateAgentV1

class Distancer:

    def __init__( self, layout ):
        """
        Attention: the coodinate begins from 1 instead of 0
        """
        self.height = layout.height - 2
        self.width = layout.width - 2
        self.positions_dict = dict()
        self.layout = layout
        self.count = 1
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
    
    def construct_dict( self ):
        self.adj()  
        for position2 in self.positions:
            for position1 in self.positions:
                for position3 in self.positions:
                    self.positions_dict[ position1 ][ position3 ]\
                    = min( self.positions_dict[ position1][position3],\
                    self.positions_dict[ position1 ][ position2 ] +\
                    self.positions_dict[ position2 ][ position3 ] )

        self.DistanceMatrix = []
        for i,poi in enumerate(self.positions):
            distanceList = []
            for j,poi2 in enumerate(self.positions):
                if j <= i:
                    distanceList.append(self.positions_dict[poi][poi2])
            self.DistanceMatrix.append(distanceList)

    def getDistancer( self, pos1 ,pos2 ):
        
        #self.count += 1
        #if self.count % 100000 == 1:
        #    print self.count
        
        return self.positions_dict[pos1][pos2]
        
        #index1 = self.positions.index(pos1)
        #index2 = self.positions.index(pos2)
        #if index1 >= index2:
        #    return self.DistanceMatrix[index1][index2]
        #else:
        #    return self.DistanceMatrix[index2][index1]

class ParallelAgent:
    def __init__( self, allies, enemies, ROLLOUT_DEPTH, PositionsDict, getMazeDistance ):
        self.index = allies[0]
        self.allies = allies
        self.enemies = enemies
        self.PositionDictManager = PositionsDict
        #self.PositionDictManager = None
        self.getMazeDistance = getMazeDistance
        print self.getMazeDistance  
        self.ROLLOUT_DEPTH = ROLLOUT_DEPTH

    def PlayOut3(self, GameState, InitialActions, PositionDict ): 
        #print "PlayOut3 Initial playout",PositionDict[(1,10)][(30,1)]
        """
        PositionDictM = PositionDict
        def getMazeDistance( pos1, pos2 ):
            #print pos1, pos2
            iters = 0
            while True:
                try:
                    #iters += 1
                    #if iters > 2:
                        
                    return PositionDictM[pos1][pos2]
                except:
                    #continue
                    print "something goes wrong!",pos1, pos2
                    raise Exception
        print getMazeDistance( (1.0,2.0),(17,6))
        print getMazeDistance( (1.0,2.0),(21,12))
        """
        PositionDict = None
      
        t1 = time.time()
        #print InitialActions, "playout begin!"      
        getMazeDistance = self.getMazeDistance

        n1 = SimulateAgent( self.allies[0], self.allies, self.enemies, GameState, getMazeDistance, PositionDict )
        n2 = SimulateAgent( self.allies[1], self.allies, self.enemies, GameState, getMazeDistance, PositionDict )
        m1 = SimulateAgent( self.enemies[0], self.enemies, self.allies, GameState, getMazeDistance, PositionDict )
        m2 = SimulateAgent( self.enemies[1], self.enemies, self.allies, GameState, getMazeDistance, PositionDict ) 

        ActionSeries = []
        ActionSeries.extend( InitialActions )

        iters = 0
        CurrentGameState = copy.deepcopy( GameState )

        while iters < ( self.ROLLOUT_DEPTH - len( InitialActions ) ):

            a1 = n1.chooseAction( CurrentGameState )
            a2 = n2.chooseAction( CurrentGameState )

            b1 = m1.chooseAction( CurrentGameState )
            b2 = m2.chooseAction( CurrentGameState )

            Actions = ( a1, a2, b1, b2 )
            for Agent, Action in zip( self.allies + self.enemies, Actions):
                CurrentGameState = CurrentGameState.generateSuccessor( Agent, Action )
                 
            iters += 1
            ActionSeries.append( ( ( a1, a2 ) , ( b1, b2 ) ) )     

        t2 = time.time()
        #print InitialActions, t2 - t1
        return ActionSeries

    def PlayOut4( self, poses, PositionDict ):
        def getMazeDistance( pos1, pos2 ):
            #print pos1, pos2
            try:
                #print "try"
                return PositionDict[pos1][pos2]
            except:
                print pos1, pos2
                raise Exception

        print "start"
        pos1, pos2 = poses
        val = getMazeDistance( pos1, pos2)
        time.sleep(1)
        print "finish",val

        return val

    def P2( self ):
        t1 = time.time()
        p = mp.ProcessPool( 4 )
        HelpLists = []
        results = []
        for _ in range(10):
            results.append( p.apipe( self.PlayOut4, ((10,1),(30,14)) , self.PositionDictManager ) )
        for r in results:
            HelpLists.append( r.get() )

        p.close()
        p.join()
        p.clear()
        t2 = time.time()
        print "2 Finish", t2 - t1
     
    def P1( self, GameStateActionList ):
        p = mp.ProcessPool( 4 )
        #p = mp.Pool( processes=4 )  
        t1 = time.time()
        
        #print "Parallel Begin"
        ActionSeriesLists = []
        results = []
        for gs, a in GameStateActionList:
            results.append( p.apipe( self.PlayOut3, gs, a, self.PositionDictManager ) ) 
        for r in results:
            ActionSeriesLists.append( r.get() )

        p.close()
        p.join()
        p.clear()
        
        t2 = time.time()
        #print "P1 Finish!", t2 - t1
         
        return ActionSeriesLists

class SimulateAgent:
    """
    In BaselineTeam, the agents are divided into Defensive Agent and Offensive Agent, there we shoul allocate an "Defensive" or "Offensive" 
    state for our agent here
    For simplification, here if the Agent in its own field, then we consider it as Defensive state, else we consider it as Offensive State.
    Obviouly, this method is quite bad! 
    We should reset the their State !
    """
    def __init__(self, index, allies, enemies, GameState, getDistancer, getDistanceDict = None ):
        self.index = index
        self.allies = allies
        self.enemies = enemies
        self.GameState = GameState
        self.getMazeDistance = getDistancer
        self.getDistanceDict = getDistanceDict
        self.startPosition = self.GameState.getAgentPosition( self.index )
        self.isPacman = self.GameState.getAgentState( self.index ).isPacman
        self.red = self.GameState.isOnRedTeam( self.index )

    def chooseAction(self, gameState, nums=None):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = gameState.getLegalActions( self.index )    

        values = [self.evaluate(gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
        foodLeft = self.getFood( gameState ).asList()
     
        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                if self.getDistanceDict is not None:
                    dist = self.getDistanceDict[self.startPosition][pos2]
                else:
                    dist = self.getMazeDistance( self.startPosition, pos2 )
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction
      
        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):
        # Finds the next successor which is a grid position (location tuple).
        successor = gameState.generateSuccessor( self.index, action)
        pos = successor.getAgentState( self.index ).getPosition()
        if pos != nearestPoint(pos):
           # Only half a grid position was covered
            return successor.generateSuccessor( self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        features = self.getFeatures( gameState, action ) 
        weights = self.getWeights( )
        return features * weights

    def getFood( self, gameState ):
        if self.red:
            foodLeft = gameState.getBlueFood()
        else:
            foodLeft = gameState.getRedFood()
        return foodLeft

    def getFeatures(self, state, action):
        
        food = self.getFood( state ) 
        foodList = food.asList()
        walls = state.getWalls()
        isPacman = self.getSuccessor(state, action).getAgentState(self.index).isPacman

        # Zone of the board agent is primarily responsible for
        zone = (self.index - self.index % 2) / 2

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
   
    def getWeights( self ):
        return {'eats-invader': 5, 'invaders-1-step-away': 0, 'teammateDist': 1.5, 'closest-food': -1,
                'eats-capsules': 10.0, '#-of-dangerous-ghosts-1-step-away': -20, 'eats-ghost': 1.0,
                '#-of-harmless-ghosts-1-step-away': 0.1, 'stopped': -5, 'eats-food': 1}

### the following subclass would be abandoned in New RollOut Method ? Yep
class SimulateAgentV1( SimulateAgent ):

    def chooseAction(self, GameState, nums=None):
        gameState = copy.deepcopy(GameState)
        actions = gameState.getLegalActions(self.index )

        values = [self.evaluate(gameState, a) for a in actions]
        ActionValues = list( zip( actions, values ) )
        sorted(ActionValues, lambda x, y: -cmp(x[1], y[1]))
        SortActionValues = sorted( ActionValues, lambda x, y: -cmp( x[1], y[1] ) )
        TopAction = []
        for i in range(nums):
            try:
                TopAction.append( SortActionValues[i][0] )
            except:
                break
        
        foodLeft = self.getFood()
        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition( self.index )
                if self.getDistanceDict is not None:
                    dist = self.getDistanceDict[self.startPosition][pos2]
                else:
                    dist = self.getDistancer(self.startPosition, pos2)
                
                #dist = self.getDistancer(self.startPosition,pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction

        return TopAction


