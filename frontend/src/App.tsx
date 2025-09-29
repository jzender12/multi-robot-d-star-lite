import { useEffect } from 'react'
import { Grid2D } from './components/Grid2D'
import { ControlPanel } from './components/ControlPanel'
import { GameLog } from './components/GameLog'
import { useGameStore } from './store/gameStore'
import styles from './App.module.css'

function App() {
  const {
    // Game state
    gridSize,
    robots,
    obstacles,
    paused,
    cursorMode,
    simulationSpeed,
    logs,
    isConnected,
    wsClient,
    selectedRobot,
    robotPlacementMode,

    // Actions
    connect,
    disconnect,
    pauseSimulation,
    resumeSimulation,
    addRobot,
    removeRobot,
    resizeArena,
    setCursorMode,
    setSimulationSpeed,
    clearLogs,
    selectRobot,
    addLog,
    setRobotPlacementMode,
    clearBoard
  } = useGameStore()

  // Connect to WebSocket on mount with a small delay
  useEffect(() => {
    // Add a small delay to ensure everything is initialized
    const timer = setTimeout(() => {
      connect('ws://localhost:8000')
    }, 500) // 500ms delay

    return () => {
      clearTimeout(timer)
      disconnect()
    }
  }, [connect, disconnect])

  // Keyboard controls
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Prevent space from scrolling page
      if (e.key === ' ') {
        e.preventDefault()
        if (paused) {
          resumeSimulation()
        } else {
          pauseSimulation()
        }
      }

      // Cursor mode shortcuts (Minecraft-style)
      if (e.key === '1') {
        setCursorMode('select')
      }
      if (e.key === '2') {
        setCursorMode('draw')
      }
      if (e.key === '3') {
        setCursorMode('erase')
      }

      // Deselect robot
      if (e.key === 'Escape') {
        selectRobot(null)
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [paused, pauseSimulation, resumeSimulation, setCursorMode, selectRobot])

  // Auto-step simulation
  useEffect(() => {
    if (!paused && wsClient && isConnected) {
      const interval = setInterval(() => {
        wsClient.sendStep()
      }, 1000 / simulationSpeed)

      return () => clearInterval(interval)
    }
  }, [paused, simulationSpeed, wsClient, isConnected])

  // Handle control panel actions
  const handleAddRobot = () => {
    // Get free positions (not obstacles and not occupied by robots)
    const freePositions: Array<[number, number]> = []
    const [width, height] = gridSize

    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        // Check if position is free (not obstacle and not robot)
        const isObstacle = obstacles.some(([ox, oy]) => ox === x && oy === y)
        const isRobot = Object.values(robots).some(r => r.pos[0] === x && r.pos[1] === y)

        if (!isObstacle && !isRobot) {
          freePositions.push([x, y])
        }
      }
    }

    // Need at least 2 free positions for start and goal
    if (freePositions.length >= 2) {
      // Random select start position
      const startIdx = Math.floor(Math.random() * freePositions.length)
      const [startX, startY] = freePositions[startIdx]

      // Remove start from free positions for goal selection
      freePositions.splice(startIdx, 1)

      // Random select goal position
      const goalIdx = Math.floor(Math.random() * freePositions.length)
      const [goalX, goalY] = freePositions[goalIdx]

      addRobot(startX, startY, goalX, goalY)
    } else {
      addLog('Not enough free space for a new robot', 'error')
    }
  }

  const handleRemoveRobot = () => {
    // Remove the selected robot
    if (selectedRobot) {
      removeRobot(selectedRobot)
      selectRobot(null)
    }
  }

  const handlePlaceRobot = () => {
    // Enable robot placement mode and switch to select mode
    setCursorMode('select')
    setRobotPlacementMode(true)
    addLog('Click on the grid to place a robot', 'info')
  }

  const handleClearBoard = () => {
    clearBoard()
  }

  const handleTogglePause = () => {
    if (paused) {
      resumeSimulation()
    } else {
      pauseSimulation()
    }
  }

  return (
    <div className={styles.app}>
      {/* Connection status bar */}
      <div className={styles.statusBar}>
        <div className={styles.statusLeft}>
          <span className={isConnected ? styles.connected : styles.disconnected}>
            {isConnected ? '● Connected' : '○ Disconnected'}
          </span>
        </div>
        <div className={styles.statusCenter}>
          <span className={styles.title}>Multi-Robot Playground</span>
        </div>
        <div className={styles.statusRight}></div>
      </div>

      {/* Main layout */}
      <div className={styles.mainLayout}>
        {/* Left: Game Log */}
        <div className={styles.logPanel}>
          <GameLog
            messages={logs}
            maxHeight={window.innerHeight - 40}
            onClear={clearLogs}
          />
        </div>

        {/* Center: Grid */}
        <div className={styles.gridPanel}>
          <Grid2D cellSize={50} />
        </div>

        {/* Right: Control Panel */}
        <div className={styles.controlPanel}>
          <ControlPanel
            robotCount={Object.keys(robots).length}
            isPaused={paused}
            cursorMode={cursorMode}
            simulationSpeed={simulationSpeed}
            selectedRobot={selectedRobot}
            onAddRobot={handleAddRobot}
            onPlaceRobot={handlePlaceRobot}
            onRemoveRobot={handleRemoveRobot}
            onResizeArena={(size) => resizeArena(size, size)}
            onTogglePause={handleTogglePause}
            onSetCursorMode={setCursorMode}
            onSpeedChange={setSimulationSpeed}
            onClearBoard={handleClearBoard}
          />
        </div>
      </div>
    </div>
  )
}

export default App