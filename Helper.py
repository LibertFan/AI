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

        #print "What are the keys like ?"
        #k1 = self.PositionDictManager.keys()[0]
        #print k1
        #print self.PositionDictManager[k1].keys()[0]

        self.getMazeDistance = getMazeDistance
        self.ROLLOUT_DEPTH = ROLLOUT_DEPTH
    """
    def getMazeDistance( self, pos1, pos2 ):
        try:
            return self.PositionDictManager[ pos1 ][ pos2 ]
        except:
            print "sad news", pos1, pos2
            raise Exception
            return 0
    """

    def PlayOut3(self, GameState, InitialAction, PositionDict ): 
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
        #print InitialAction, "playout begin!"      
        getMazeDistance = self.getMazeDistance
        n1 = SimulateAgentV1( self.allies[0], self.allies, self.enemies, GameState, getMazeDistance, PositionDict )
        a1s = n1.chooseAction( GameState, 2 )
        n2 = SimulateAgentV1( self.allies[1], self.allies, self.enemies, GameState, getMazeDistance, PositionDict )
        a2s = n2.chooseAction( GameState, 2 )
        a12s = list( itertools.product( a1s , a2s ) )
        if len( a12s ) > 3:
            a12s = a12s[:1]

            #mindist = self.getDistancer( myPos, invader_positions )
        m1 = SimulateAgentV1( self.enemies[0], self.enemies, self.allies, GameState, getMazeDistance, PositionDict )
        b1s = m1.chooseAction( GameState, 2 )
        m2 = SimulateAgentV1( self.enemies[1], self.enemies, self.allies, GameState, getMazeDistance, PositionDict )
        b2s = m2.chooseAction( GameState, 2 )

        b12s = list( itertools.product( b1s, b2s ) )
        if len(b12s) > 3:
            b12s = b12s[:1]

        ActionList = tuple( itertools.product( a12s, b12s ) )

        ActionSeriesList = [ None, ] * len( ActionList )
        for index in range( len( ActionList ) ):
            ActionSeriesList[ index ] = [ InitialAction, ] 

        n1 = SimulateAgent( self.allies[0], self.allies, self.enemies, GameState, getMazeDistance, PositionDict )
        n2 = SimulateAgent( self.allies[1], self.allies, self.enemies, GameState, getMazeDistance, PositionDict )
        m1 = SimulateAgent( self.enemies[0], self.enemies, self.allies, GameState, getMazeDistance, PositionDict )
        m2 = SimulateAgent( self.enemies[1], self.enemies, self.allies, GameState, getMazeDistance, PositionDict ) 

        for index, Actions in enumerate(ActionList):
            ActionSeriesList[ index ].append( Actions )
            iters = 0
            CurrentGameState = copy.deepcopy( GameState )
            for Agent, Action in zip( self.allies + self.enemies, Actions[0] + Actions[1] ):
                CurrentGameState = CurrentGameState.generateSuccessor( Agent, Action )
          
            while iters < ( self.ROLLOUT_DEPTH - 1 ):

                a1 = n1.chooseAction( CurrentGameState )
                a2 = n2.chooseAction( CurrentGameState )

                b1 = m1.chooseAction( CurrentGameState )
                b2 = m2.chooseAction( CurrentGameState )

                Actions = ( a1, a2, b1, b2 )
                for Agent, Action in zip( self.allies + self.enemies, Actions):
                    CurrentGameState = CurrentGameState.generateSuccessor( Agent, Action )
                     
                iters += 1
                ActionSeriesList[ index ].append( ( ( a1, a2 ) , ( b1, b2 ) ) )     

        t2 = time.time()
        #print InitialAction, t2 - t1
        return ActionSeriesList

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
     
    def P1( self, CurrentInfo ):
        p = mp.ProcessPool( 4 )
        #p = mp.Pool( processes=4 )  
        t1 = time.time()
        GameStateList = [ ( copy.deepcopy( CurrentState.GameState ), Action ) for CurrentState, Action in CurrentInfo ]
        
        #print "Parallel Begin"
        ActionSeriesLists = []
        results = []
        for gs, a in GameStateList:
            results.append( p.apipe( self.PlayOut3, gs, a, self.PositionDictManager ) ) 
        for r in results:
            ActionSeriesLists.append( r.get() )

        p.close()
        p.join()
        p.clear()
        
        t2 = time.time()
        #print "P1 Finish!", t2 - t1
         
        return ActionSeriesLists

