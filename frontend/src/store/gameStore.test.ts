import { describe, it, expect, beforeEach, vi } from 'vitest'
import { act, renderHook } from '@testing-library/react'
import { useGameStore } from './gameStore'
import { WebSocketClient } from '../services/WebSocketClient'

vi.mock('../services/WebSocketClient')

describe('gameStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useGameStore.setState({
      // Game state
      gridSize: [10, 10],
      robots: {},
      obstacles: [],
      paths: {},
      stepCount: 0,
      paused: true,
      pausedRobots: [],
      collisionInfo: null,

      // UI state
      selectedRobot: null,
      obstacleMode: 'place',
      simulationSpeed: 5,
      isConnected: false,
      connectionError: null,

      // WebSocket
      wsClient: null,

      // Logs
      logs: []
    })
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial values', () => {
      const { result } = renderHook(() => useGameStore())

      expect(result.current.gridSize).toEqual([10, 10])
      expect(result.current.robots).toEqual({})
      expect(result.current.obstacles).toEqual([])
      expect(result.current.paused).toBe(true)
      expect(result.current.obstacleMode).toBe('place')
      expect(result.current.simulationSpeed).toBe(5)
      expect(result.current.isConnected).toBe(false)
    })
  })

  describe('WebSocket Connection', () => {
    it('should connect to WebSocket server', () => {
      const mockClient = {
        connect: vi.fn(),
        onConnect: vi.fn(),
        onDisconnect: vi.fn(),
        onGameState: vi.fn(),
        onError: vi.fn(),
        isConnected: vi.fn().mockReturnValue(true)
      }

      vi.mocked(WebSocketClient).mockImplementation(() => mockClient as any)

      const { result } = renderHook(() => useGameStore())

      act(() => {
        result.current.connect('ws://localhost:8000')
      })

      expect(WebSocketClient).toHaveBeenCalledWith('ws://localhost:8000')
      expect(mockClient.onConnect).toHaveBeenCalled()
      expect(mockClient.onDisconnect).toHaveBeenCalled()
      expect(mockClient.onGameState).toHaveBeenCalled()
      expect(mockClient.onError).toHaveBeenCalled()
      expect(result.current.wsClient).toBe(mockClient)
    })

    it('should disconnect from WebSocket server', () => {
      const mockClient = {
        connect: vi.fn(),
        disconnect: vi.fn(),
        onConnect: vi.fn(),
        onDisconnect: vi.fn(),
        onGameState: vi.fn(),
        onError: vi.fn(),
        isConnected: vi.fn().mockReturnValue(false)
      }

      vi.mocked(WebSocketClient).mockImplementation(() => mockClient as any)

      const { result } = renderHook(() => useGameStore())

      act(() => {
        result.current.connect('ws://localhost:8000')
      })

      act(() => {
        result.current.disconnect()
      })

      expect(mockClient.disconnect).toHaveBeenCalled()
      expect(result.current.wsClient).toBe(null)
      expect(result.current.isConnected).toBe(false)
    })
  })

  describe('Game State Updates', () => {
    it('should update game state from server', () => {
      const { result } = renderHook(() => useGameStore())

      const gameState = {
        width: 15,
        height: 15,
        robots: {
          robot0: {
            id: 'robot0',
            position: [0, 0],
            goal: [9, 9],
            path: [[0, 0], [1, 0], [2, 0]],
            is_stuck: false,
            is_paused: false
          }
        },
        obstacles: [[3, 3], [4, 4]],
        paused: false,
        stuck_robots: ['robot1'],
        collision_info: {
          type: 'same_cell',
          robots: ['robot0', 'robot1']
        }
      }

      act(() => {
        result.current.updateGameState(gameState)
      })

      expect(result.current.gridSize).toEqual([15, 15])
      expect(result.current.robots).toEqual({
        robot0: { pos: [0, 0], goal: [9, 9] }
      })
      expect(result.current.obstacles).toEqual(gameState.obstacles)
      expect(result.current.paths).toEqual({
        robot0: [[0, 0], [1, 0], [2, 0]]
      })
      expect(result.current.stepCount).toBe(0) // step_count not in new format
      expect(result.current.paused).toBe(false)
      expect(result.current.pausedRobots).toEqual(['robot1'])
      expect(result.current.collisionInfo).toEqual(gameState.collision_info)
    })
  })

  describe('UI State Management', () => {
    it('should select and deselect robot', () => {
      const { result } = renderHook(() => useGameStore())

      act(() => {
        result.current.selectRobot('robot0')
      })

      expect(result.current.selectedRobot).toBe('robot0')

      act(() => {
        result.current.selectRobot(null)
      })

      expect(result.current.selectedRobot).toBe(null)
    })

    it('should toggle obstacle mode', () => {
      const { result } = renderHook(() => useGameStore())

      expect(result.current.obstacleMode).toBe('place')

      act(() => {
        result.current.toggleObstacleMode()
      })

      expect(result.current.obstacleMode).toBe('draw')

      act(() => {
        result.current.toggleObstacleMode()
      })

      expect(result.current.obstacleMode).toBe('place')
    })

    it('should set simulation speed', () => {
      const { result } = renderHook(() => useGameStore())

      act(() => {
        result.current.setSimulationSpeed(8)
      })

      expect(result.current.simulationSpeed).toBe(8)
    })
  })

  describe('Game Commands', () => {
    it('should send pause command', () => {
      const mockClient = {
        sendPause: vi.fn(),
        connect: vi.fn(),
        onConnect: vi.fn(),
        onDisconnect: vi.fn(),
        onGameState: vi.fn(),
        onError: vi.fn()
      }

      const { result } = renderHook(() => useGameStore())

      act(() => {
        useGameStore.setState({ wsClient: mockClient as any })
        result.current.pauseSimulation()
      })

      expect(mockClient.sendPause).toHaveBeenCalled()
    })

    it('should send resume command', () => {
      const mockClient = {
        sendResume: vi.fn(),
        connect: vi.fn(),
        onConnect: vi.fn(),
        onDisconnect: vi.fn(),
        onGameState: vi.fn(),
        onError: vi.fn()
      }

      const { result } = renderHook(() => useGameStore())

      act(() => {
        useGameStore.setState({ wsClient: mockClient as any })
        result.current.resumeSimulation()
      })

      expect(mockClient.sendResume).toHaveBeenCalled()
    })

    it('should send add obstacle command', () => {
      const mockClient = {
        sendAddObstacle: vi.fn()
      }

      const { result } = renderHook(() => useGameStore())

      act(() => {
        useGameStore.setState({ wsClient: mockClient as any })
        result.current.addObstacle(3, 4)
      })

      expect(mockClient.sendAddObstacle).toHaveBeenCalledWith(3, 4)
    })

    it('should send remove obstacle command', () => {
      const mockClient = {
        sendRemoveObstacle: vi.fn()
      }

      const { result } = renderHook(() => useGameStore())

      act(() => {
        useGameStore.setState({ wsClient: mockClient as any })
        result.current.removeObstacle(5, 6)
      })

      expect(mockClient.sendRemoveObstacle).toHaveBeenCalledWith(5, 6)
    })
  })

  describe('Logging', () => {
    it('should add log messages', () => {
      const { result } = renderHook(() => useGameStore())

      act(() => {
        result.current.addLog('Test message', 'info')
      })

      expect(result.current.logs).toHaveLength(1)
      expect(result.current.logs[0].message).toBe('Test message')
      expect(result.current.logs[0].type).toBe('info')
      expect(result.current.logs[0].timestamp).toBeDefined()
    })

    it('should limit log messages to 100', () => {
      const { result } = renderHook(() => useGameStore())

      act(() => {
        for (let i = 0; i < 110; i++) {
          result.current.addLog(`Message ${i}`, 'info')
        }
      })

      expect(result.current.logs).toHaveLength(100)
      expect(result.current.logs[0].message).toBe('Message 10')
      expect(result.current.logs[99].message).toBe('Message 109')
    })

    it('should clear logs', () => {
      const { result } = renderHook(() => useGameStore())

      act(() => {
        result.current.addLog('Test', 'info')
        result.current.addLog('Test2', 'warning')
        result.current.clearLogs()
      })

      expect(result.current.logs).toHaveLength(0)
    })
  })
})