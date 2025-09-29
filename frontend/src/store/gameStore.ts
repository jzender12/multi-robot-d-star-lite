import { create } from 'zustand'
import { WebSocketClient } from '../services/WebSocketClient'

export interface LogMessage {
  id: string
  message: string
  type: 'info' | 'warning' | 'error' | 'success' | 'collision'
  timestamp: Date
}

export interface RobotInfo {
  pos: [number, number]
  goal: [number, number]
}

export interface CollisionInfo {
  type: string
  robots: string[]
}

export type CollisionList = CollisionInfo[]

interface GameStore {
  // Game state
  gridSize: [number, number]
  robots: Record<string, RobotInfo>
  obstacles: Array<[number, number]>
  paths: Record<string, Array<[number, number]>>
  stepCount: number
  paused: boolean
  pausedRobots: string[]
  stuckRobots: string[]
  collisionInfo: CollisionList | null
  activeCollisions: Set<string>  // Track which collisions we've already logged

  // UI state
  selectedRobot: string | null
  cursorMode: 'select' | 'draw' | 'erase'  // Current cursor mode
  robotPlacementMode: boolean  // True when placing a robot manually
  placingRobotGoal: boolean    // True when placing goal after robot
  ghostPosition: [number, number] | null  // Preview position for robot placement
  simulationSpeed: number
  isConnected: boolean
  connectionError: string | null
  expectingNewRobot: boolean  // True when we just added a robot and waiting for it

  // WebSocket
  wsClient: WebSocketClient | null

  // Logs
  logs: LogMessage[]

  // Actions
  connect: (url: string) => void
  disconnect: () => void
  updateGameState: (state: any) => void
  selectRobot: (robotId: string | null) => void
  setCursorMode: (mode: 'select' | 'draw' | 'erase') => void
  setSimulationSpeed: (speed: number) => void
  pauseSimulation: () => void
  resumeSimulation: () => void
  addObstacle: (x: number, y: number) => void
  removeObstacle: (x: number, y: number) => void
  setGoal: (robotId: string, x: number, y: number) => void
  addRobot: (startX: number, startY: number, goalX: number, goalY: number) => void
  removeRobot: (robotId: string) => void
  resizeArena: (width: number, height: number) => void
  addLog: (message: string, type: LogMessage['type']) => void
  clearLogs: () => void
  setRobotPlacementMode: (enabled: boolean) => void
  setGhostPosition: (position: [number, number] | null) => void
  setPlacingRobotGoal: (placing: boolean) => void
  clearBoard: () => void
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  gridSize: [10, 10],
  robots: {},
  obstacles: [],
  paths: {},
  stepCount: 0,
  paused: true,
  pausedRobots: [],
  stuckRobots: [],
  collisionInfo: null,
  activeCollisions: new Set(),

  selectedRobot: null,
  cursorMode: 'select',  // Default to select mode
  robotPlacementMode: false,
  placingRobotGoal: false,
  ghostPosition: null,
  simulationSpeed: 2,  // Default to 2 steps/s
  isConnected: false,
  connectionError: null,
  expectingNewRobot: false,

  wsClient: null,
  logs: [],

  // WebSocket actions
  connect: (url: string) => {
    const client = new WebSocketClient(url)

    // Set up event handlers
    client.onConnect(() => {
      set({ isConnected: true, connectionError: null })
      get().addLog('Connected to server', 'success')
    })

    client.onDisconnect(() => {
      set({ isConnected: false })
      get().addLog('Disconnected from server', 'warning')
    })

    client.onGameState((state) => {
      get().updateGameState(state)
    })

    client.onError((error) => {
      set({ connectionError: error.message || 'Connection error' })
      get().addLog(`Connection error: ${error.message}`, 'error')
    })

    client.connect()
    set({ wsClient: client })
  },

  disconnect: () => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.disconnect()
      set({ wsClient: null, isConnected: false })
    }
  },

  updateGameState: (state: any) => {
    // Transform robot data from backend format to frontend format
    const robots: Record<string, RobotInfo> = {}
    const paths: Record<string, Array<[number, number]>> = {}
    const previousRobots = get().robots
    let newRobotId: string | null = null

    if (state.robots) {
      for (const [robotId, robotData] of Object.entries(state.robots)) {
        const robot = robotData as any
        robots[robotId] = {
          pos: robot.position as [number, number],
          goal: robot.goal as [number, number]
        }
        paths[robotId] = robot.path || []

        // Check if this is a new robot
        if (!(robotId in previousRobots)) {
          newRobotId = robotId
        }
      }
    }

    // If we were expecting a new robot and one appeared, select it
    if (get().expectingNewRobot && newRobotId) {
      set({ expectingNewRobot: false, selectedRobot: newRobotId, placingRobotGoal: true })
      get().addLog('Robot placed. Click to set its goal', 'info')
    }

    // Check for robots reaching their goals
    for (const [robotId, robot] of Object.entries(robots)) {
      const prevRobot = previousRobots[robotId]
      if (prevRobot) {
        const wasAtGoal = prevRobot.pos[0] === prevRobot.goal[0] && prevRobot.pos[1] === prevRobot.goal[1]
        const isAtGoal = robot.pos[0] === robot.goal[0] && robot.pos[1] === robot.goal[1]

        // Robot just reached its goal
        if (!wasAtGoal && isAtGoal) {
          get().addLog(`${robotId} reached its goal!`, 'success')
        }
      }
    }

    // Handle collision logging - only log NEW collisions
    const currentActiveCollisions = get().activeCollisions
    const newActiveCollisions = new Set<string>()

    if (state.collision_info && Array.isArray(state.collision_info)) {
      for (const collision of state.collision_info) {
        const { type, robots, position, positions, blocked_by } = collision
        const collisionKey = `${type}:${robots.sort().join('-')}`
        newActiveCollisions.add(collisionKey)

        // Only log if this is a new collision
        if (!currentActiveCollisions.has(collisionKey)) {
          let message = ''

          if (type === 'same_cell' && position) {
            // Format: "Collision at (x,y): robot1, robot2"
            message = `Collision at (${position[0]},${position[1]}): ${robots.join(', ')}`
          } else if (type === 'swap') {
            // Format: "Swap collision: robot1 ↔ robot2"
            message = robots.length >= 2
              ? `Swap collision: ${robots[0]} ↔ ${robots[1]}`
              : `Swap collision: ${robots.join(', ')}`
          } else if (type === 'shear' && position) {
            // Format: "Shear collision at (x,y): robot1 ↔ robot2"
            message = robots.length >= 2
              ? `Shear collision at (${position[0]},${position[1]}): ${robots[0]} ↔ ${robots[1]}`
              : `Shear collision: ${robots.join(', ')}`
          } else if (type === 'blocked_robot' && blocked_by) {
            // Format: "Blocked: robot1 (by robot2)"
            message = `Blocked: ${robots[0]} (by ${blocked_by})`
          } else {
            // Fallback format
            message = robots.length >= 2
              ? `${type}: ${robots[0]} and ${robots[1]}`
              : `${type}: ${robots[0]}`
          }

          get().addLog(message, 'collision')
        }
      }
    }

    set({
      gridSize: [state.width || 10, state.height || 10],
      robots,
      obstacles: state.obstacles || [],
      paths,
      stepCount: state.step_count || 0,
      paused: state.paused ?? true,
      pausedRobots: state.paused_robots || [],
      stuckRobots: state.stuck_robots || [],
      collisionInfo: state.collision_info || null,
      activeCollisions: newActiveCollisions
    })
  },

  // UI actions
  selectRobot: (robotId: string | null) => {
    set({ selectedRobot: robotId })
  },

  setCursorMode: (mode) => {
    set({ cursorMode: mode })
  },

  setSimulationSpeed: (speed: number) => {
    set({ simulationSpeed: Math.max(1, Math.min(10, speed)) })
  },

  // Game commands
  pauseSimulation: () => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.sendPause()
      set({ paused: true })
      get().addLog('Simulation paused', 'info')
    }
  },

  resumeSimulation: () => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.sendResume()
      set({ paused: false })
      get().addLog('Simulation resumed', 'info')
    }
  },

  addObstacle: (x: number, y: number) => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.sendAddObstacle(x, y)
    }
  },

  removeObstacle: (x: number, y: number) => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.sendRemoveObstacle(x, y)
    }
  },

  setGoal: (robotId: string, x: number, y: number) => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.sendSetGoal(robotId, x, y)
      get().addLog(`Set ${robotId} goal to (${x}, ${y})`, 'info')
    }
  },

  addRobot: (startX: number, startY: number, goalX: number, goalY: number) => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.sendAddRobot(startX, startY, goalX, goalY)
      // Don't log here if we're in placement mode - will log when state updates
      if (!get().robotPlacementMode) {
        get().addLog(`Added new robot at (${startX}, ${startY})`, 'success')
      }
    }
  },

  removeRobot: (robotId: string) => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.sendRemoveRobot(robotId)
      get().addLog(`Removed ${robotId}`, 'info')
    }
  },

  resizeArena: (width: number, height: number) => {
    const { wsClient } = get()
    if (wsClient) {
      wsClient.sendResizeArena(width, height)
      get().addLog(`Resized arena to ${width}x${height}`, 'info')
    }
  },

  // Logging
  addLog: (message: string, type: LogMessage['type']) => {
    const log: LogMessage = {
      id: `${Date.now()}-${Math.random()}`,
      message,
      type,
      timestamp: new Date()
    }

    set((state) => ({
      logs: [...state.logs.slice(-99), log] // Keep last 100 messages
    }))
  },

  clearLogs: () => {
    set({ logs: [] })
  },

  setRobotPlacementMode: (enabled: boolean) => {
    set({ robotPlacementMode: enabled, ghostPosition: null })
    if (!enabled) {
      set({ placingRobotGoal: false })
    }
  },

  setGhostPosition: (position: [number, number] | null) => {
    set({ ghostPosition: position })
  },

  setPlacingRobotGoal: (placing: boolean) => {
    set({ placingRobotGoal: placing })
  },

  clearBoard: () => {
    const { wsClient } = get()
    if (wsClient) {
      // Pause the simulation first
      get().pauseSimulation()
      // Clear obstacles
      wsClient.sendCommand({ type: 'clear_obstacles' })
      // Clear all robots
      const robots = get().robots
      Object.keys(robots).forEach(robotId => {
        wsClient.sendRemoveRobot(robotId)
      })
      get().addLog('Cleared board', 'info')
    }
  }
}))