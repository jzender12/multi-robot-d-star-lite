import React from 'react'

interface ControlPanelProps {
  robotCount: number
  isPaused: boolean
  obstacleMode: 'place' | 'draw'
  simulationSpeed: number
  onAddRobot: () => void
  onRemoveRobot: () => void
  onResizeArena: (size: number) => void
  onTogglePause: () => void
  onToggleObstacleMode: () => void
  onSpeedChange: (speed: number) => void
  onReset: () => void
  onClearAll: () => void
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  robotCount,
  isPaused,
  obstacleMode,
  simulationSpeed,
  onAddRobot,
  onRemoveRobot,
  onResizeArena,
  onTogglePause,
  onToggleObstacleMode,
  onSpeedChange,
  onReset,
  onClearAll
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
          Add Robot
        </button>
        <button
          style={styles.button}
          onClick={onRemoveRobot}
          disabled={robotCount === 0}
        >
          Remove Robot
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
          {obstacleMode === 'place' ? 'Place Mode' : 'Draw Mode'}
        </button>
      </div>

      {/* Simulation Control */}
      <div style={styles.section}>
        <button
          style={{...styles.button, ...styles.playButton}}
          onClick={onTogglePause}
        >
          {isPaused ? '▶ Play' : '⏸ Pause'}
        </button>
      </div>

      {/* Reset Controls */}
      <div style={styles.section}>
        <button
          style={styles.button}
          onClick={onReset}
        >
          Reset
        </button>
        <button
          style={styles.button}
          onClick={onClearAll}
        >
          Clear All
        </button>
      </div>
    </div>
  )
}

const styles = {
  panel: {
    width: '200px',
    padding: '10px',
    backgroundColor: '#f0f0f0',
    borderLeft: '1px solid #ddd',
    height: '100%',
    overflowY: 'auto' as const
  },
  title: {
    margin: '0 0 15px 0',
    fontSize: '18px',
    fontWeight: 'bold' as const,
    textAlign: 'center' as const
  },
  section: {
    marginBottom: '15px'
  },
  label: {
    marginBottom: '5px',
    fontSize: '14px',
    fontWeight: 'bold' as const
  },
  button: {
    width: '100%',
    padding: '8px',
    marginBottom: '5px',
    backgroundColor: '#fff',
    border: '1px solid #ccc',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'background-color 0.2s'
  },
  smallButton: {
    flex: 1,
    padding: '8px',
    marginRight: '5px',
    backgroundColor: '#fff',
    border: '1px solid #ccc',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'background-color 0.2s'
  },
  buttonRow: {
    display: 'flex',
    gap: '5px'
  },
  playButton: {
    backgroundColor: '#4CAF50',
    color: 'white',
    fontWeight: 'bold' as const,
    fontSize: '16px'
  }
}