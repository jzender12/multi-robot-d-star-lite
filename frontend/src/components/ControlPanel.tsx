import React from 'react'
import styles from './ControlPanel.module.css'

interface ControlPanelProps {
  robotCount: number
  isPaused: boolean
  cursorMode: 'select' | 'draw' | 'erase'
  simulationSpeed: number
  selectedRobot: string | null
  onAddRobot: () => void
  onPlaceRobot: () => void
  onRemoveRobot: () => void
  onResizeArena: (size: number) => void
  onTogglePause: () => void
  onSetCursorMode: (mode: 'select' | 'draw' | 'erase') => void
  onSpeedChange: (speed: number) => void
  onClearBoard: () => void
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  robotCount,
  isPaused,
  cursorMode,
  simulationSpeed,
  selectedRobot,
  onAddRobot,
  onPlaceRobot,
  onRemoveRobot,
  onResizeArena,
  onTogglePause,
  onSetCursorMode,
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
    <div className={styles.panel}>
      <h3 className={styles.title}>Controls</h3>

      {/* Robot Management */}
      <div className={styles.section}>
        <div className={styles.label}>Robots: {robotCount}</div>
        <button
          className={styles.button}
          onClick={onAddRobot}
          disabled={robotCount >= 10}
        >
          Add Random Robot
        </button>
        <button
          className={styles.button}
          onClick={onPlaceRobot}
          disabled={robotCount >= 10}
        >
          Place Robot
        </button>
        <button
          className={styles.button}
          onClick={onRemoveRobot}
          disabled={!selectedRobot}
        >
          Remove {selectedRobot ? selectedRobot.replace('robot', 'Robot ') : 'Robot'}
        </button>
      </div>

      {/* Arena Size */}
      <div className={styles.section}>
        <div className={styles.label}>Arena Size</div>
        <div className={styles.buttonRow}>
          <button
            className={styles.smallButton}
            onClick={() => onResizeArena(10)}
          >
            10x10
          </button>
          <button
            className={styles.smallButton}
            onClick={() => onResizeArena(15)}
          >
            15x15
          </button>
          <button
            className={styles.smallButton}
            onClick={() => onResizeArena(20)}
          >
            20x20
          </button>
        </div>
      </div>

      {/* Simulation Speed */}
      <div className={styles.section}>
        <div className={styles.label}>Speed: {simulationSpeed} steps/s</div>
        <div className={styles.buttonRow}>
          <button
            className={styles.smallButton}
            onClick={handleSpeedDecrease}
            disabled={simulationSpeed <= 1}
          >
            Speed -
          </button>
          <button
            className={styles.smallButton}
            onClick={handleSpeedIncrease}
            disabled={simulationSpeed >= 10}
          >
            Speed +
          </button>
        </div>
      </div>

      {/* Cursor Modes */}
      <div className={styles.section}>
        <div className={styles.label}>Cursor Mode</div>
        <div className={styles.buttonRow}>
          <button
            className={`${styles.smallButton} ${cursorMode === 'select' ? styles.activeButton : ''}`}
            onClick={() => onSetCursorMode('select')}
            disabled={cursorMode === 'select'}
            title="Select Mode (1)"
          >
            ↯ Select
          </button>
          <button
            className={`${styles.smallButton} ${cursorMode === 'draw' ? styles.activeButton : ''}`}
            onClick={() => onSetCursorMode('draw')}
            disabled={cursorMode === 'draw'}
            title="Draw Mode (2)"
          >
            ▣ Draw
          </button>
          <button
            className={`${styles.smallButton} ${cursorMode === 'erase' ? styles.activeButton : ''}`}
            onClick={() => onSetCursorMode('erase')}
            disabled={cursorMode === 'erase'}
            title="Erase Mode (3)"
          >
            ⌫ Erase
          </button>
        </div>
      </div>

      {/* Simulation Control */}
      <div className={styles.section}>
        <button
          className={`${styles.button} ${isPaused ? styles.playButton : styles.pauseButton}`}
          onClick={onTogglePause}
        >
          {isPaused ? '▶ Resume' : '❚❚ Pause'}
        </button>
      </div>

      {/* Clear Control */}
      <div className={styles.section}>
        <button
          className={styles.button}
          onClick={onClearBoard}
        >
          Clear Board
        </button>
      </div>

      {/* Keyboard Shortcuts */}
      <div className={styles.section}>
        <div className={styles.label}>Keyboard Shortcuts</div>
        <div className={styles.shortcutsList}>
          <div className={styles.shortcut}>
            <span className={styles.key}>Space</span>
            <span className={styles.action}>Pause/Play</span>
          </div>
          <div className={styles.shortcut}>
            <span className={styles.key}>1</span>
            <span className={styles.action}>Select Mode</span>
          </div>
          <div className={styles.shortcut}>
            <span className={styles.key}>2</span>
            <span className={styles.action}>Draw Mode</span>
          </div>
          <div className={styles.shortcut}>
            <span className={styles.key}>3</span>
            <span className={styles.action}>Erase Mode</span>
          </div>
          <div className={styles.shortcut}>
            <span className={styles.key}>Esc</span>
            <span className={styles.action}>Deselect</span>
          </div>
        </div>
      </div>
    </div>
  )
}