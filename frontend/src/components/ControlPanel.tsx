import React from 'react'

interface ControlPanelProps {
  robotCount: number
  isPaused: boolean
  obstacleMode: 'place' | 'draw'
  simulationSpeed: number
  selectedRobot: string | null
  onAddRobot: () => void
  onPlaceRobot: () => void
  onRemoveRobot: () => void
  onResizeArena: (size: number) => void
  onTogglePause: () => void
  onToggleObstacleMode: () => void
  onSpeedChange: (speed: number) => void
  onClearBoard: () => void
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  robotCount,
  isPaused,
  obstacleMode,
  simulationSpeed,
  selectedRobot,
  onAddRobot,
  onPlaceRobot,
  onRemoveRobot,
  onResizeArena,
  onTogglePause,
  onToggleObstacleMode,
  onSpeedChange,
  onClearBoard
}) => {
  const handleSpeedIncrease = () => {
    if (simulationSpeed < 10) {
      onSpeedChange(Math.min(10, simulationSpeed + 1))
    }
  }

  const handleSpeedDecrease = () => {
    if (simulationSpeed > 1) {
      onSpeedChange(Math.max(1, simulationSpeed - 1))
    }
  }

  return (
    <div style={styles.panel}>
      <h3 style={styles.title}>Controls</h3>

      {/* Robot Management */}
      <div style={styles.section}>
        <div style={styles.label}>Robots: {robotCount}</div>
        <button
          style={styles.button}
          onClick={onAddRobot}
          disabled={robotCount >= 10}
        >
          Add Random Robot
        </button>
        <button
          style={styles.button}
          onClick={onPlaceRobot}
          disabled={robotCount >= 10}
        >
          Place Robot
        </button>
        <button
          style={styles.button}
          onClick={onRemoveRobot}
          disabled={!selectedRobot}
        >
          Remove {selectedRobot ? selectedRobot.replace('robot', 'Robot ') : 'Robot'}
        </button>
      </div>

      {/* Arena Size */}
      <div style={styles.section}>
        <div style={styles.label}>Arena Size</div>
        <div style={styles.buttonRow}>
          <button
            style={styles.smallButton}
            onClick={() => onResizeArena(10)}
          >
            10x10
          </button>
          <button
            style={styles.smallButton}
            onClick={() => onResizeArena(15)}
          >
            15x15
          </button>
          <button
            style={styles.smallButton}
            onClick={() => onResizeArena(20)}
          >
            20x20
          </button>
        </div>
      </div>

      {/* Simulation Speed */}
      <div style={styles.section}>
        <div style={styles.label}>Speed: {simulationSpeed} steps/s</div>
        <div style={styles.buttonRow}>
          <button
            style={styles.smallButton}
            onClick={handleSpeedDecrease}
            disabled={simulationSpeed <= 1}
          >
            Speed -
          </button>
          <button
            style={styles.smallButton}
            onClick={handleSpeedIncrease}
            disabled={simulationSpeed >= 10}
          >
            Speed +
          </button>
        </div>
      </div>

      {/* Obstacle Mode */}
      <div style={styles.section}>
        <button
          style={styles.button}
          onClick={onToggleObstacleMode}
        >
          {obstacleMode === 'place' ? 'Obstacle: Place (O)' : 'Obstacle: Draw (O)'}
        </button>
      </div>

      {/* Simulation Control */}
      <div style={styles.section}>
        <button
          style={{
            ...styles.button,
            ...(isPaused ? styles.playButton : styles.pauseButton)
          }}
          onClick={onTogglePause}
        >
          {isPaused ? '▶ Resume' : '❚❚ Pause'}
        </button>
      </div>

      {/* Clear Control */}
      <div style={styles.section}>
        <button
          style={styles.button}
          onClick={onClearBoard}
        >
          Clear Board
        </button>
      </div>
    </div>
  )
}

const styles = {
  panel: {
    width: '200px',
    padding: '10px',
    backgroundColor: '#0f0f14',
    borderLeft: '1px solid #1a1a1f',
    height: '100%',
    overflowY: 'auto' as const
  },
  title: {
    margin: '0 0 15px 0',
    fontSize: '16px',
    fontWeight: 'normal' as const,
    textAlign: 'center' as const,
    color: '#e4e4e7'
  },
  section: {
    marginBottom: '15px'
  },
  label: {
    marginBottom: '5px',
    fontSize: '13px',
    fontWeight: 'normal' as const,
    color: '#9ca3af'
  },
  button: {
    width: '100%',
    padding: '8px',
    marginBottom: '5px',
    backgroundColor: '#1a1a1f',
    border: '1px solid #2a2a35',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '13px',
    color: '#e4e4e7',
    transition: 'all 0.15s'
  },
  smallButton: {
    flex: 1,
    padding: '8px',
    marginRight: '5px',
    backgroundColor: '#1a1a1f',
    border: '1px solid #2a2a35',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '13px',
    color: '#e4e4e7',
    transition: 'all 0.15s'
  },
  buttonRow: {
    display: 'flex',
    gap: '5px'
  },
  playButton: {
    backgroundColor: '#10b981',
    color: '#0a0a0f',
    fontWeight: 'normal' as const,
    fontSize: '14px',
    borderColor: '#10b981'
  },
  pauseButton: {
    backgroundColor: '#6b7280',
    color: '#e4e4e7',
    fontWeight: 'normal' as const,
    fontSize: '14px',
    borderColor: '#6b7280'
  }
}