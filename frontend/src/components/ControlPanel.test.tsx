import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ControlPanel } from './ControlPanel'

describe('ControlPanel', () => {
  const defaultProps = {
    robotCount: 2,
    isPaused: true,
    obstacleMode: 'place' as const,
    simulationSpeed: 5,
    onAddRobot: vi.fn(),
    onRemoveRobot: vi.fn(),
    onResizeArena: vi.fn(),
    onTogglePause: vi.fn(),
    onToggleObstacleMode: vi.fn(),
    onSpeedChange: vi.fn(),
    onReset: vi.fn(),
    onClearAll: vi.fn()
  }

  describe('Rendering', () => {
    it('should render all control buttons', () => {
      render(<ControlPanel {...defaultProps} />)

      expect(screen.getByText('Add Robot')).toBeTruthy()
      expect(screen.getByText('Remove Robot')).toBeTruthy()
      expect(screen.getByText('10x10')).toBeTruthy()
      expect(screen.getByText('15x15')).toBeTruthy()
      expect(screen.getByText('20x20')).toBeTruthy()
      expect(screen.getByText('Speed -')).toBeTruthy()
      expect(screen.getByText('Speed +')).toBeTruthy()
      expect(screen.getByText('Place Mode')).toBeTruthy()
      expect(screen.getByText('Reset')).toBeTruthy()
      expect(screen.getByText('Clear All')).toBeTruthy()
    })

    it('should show correct robot count', () => {
      render(<ControlPanel {...defaultProps} robotCount={3} />)

      expect(screen.getByText('Robots: 3')).toBeTruthy()
    })

    it('should show correct simulation speed', () => {
      render(<ControlPanel {...defaultProps} simulationSpeed={7.5} />)

      expect(screen.getByText('Speed: 7.5 steps/s')).toBeTruthy()
    })

    it('should show Play button when paused', () => {
      render(<ControlPanel {...defaultProps} isPaused={true} />)

      expect(screen.getByText('▶ Play')).toBeTruthy()
    })

    it('should show Pause button when running', () => {
      render(<ControlPanel {...defaultProps} isPaused={false} />)

      expect(screen.getByText('⏸ Pause')).toBeTruthy()
    })

    it('should show correct obstacle mode', () => {
      const { rerender } = render(<ControlPanel {...defaultProps} obstacleMode="place" />)
      expect(screen.getByText('Place Mode')).toBeTruthy()

      rerender(<ControlPanel {...defaultProps} obstacleMode="draw" />)
      expect(screen.getByText('Draw Mode')).toBeTruthy()
    })
  })

  describe('Button Interactions', () => {
    it('should call onAddRobot when Add Robot clicked', () => {
      const onAddRobot = vi.fn()
      render(<ControlPanel {...defaultProps} onAddRobot={onAddRobot} />)

      fireEvent.click(screen.getByText('Add Robot'))
      expect(onAddRobot).toHaveBeenCalledOnce()
    })

    it('should call onRemoveRobot when Remove Robot clicked', () => {
      const onRemoveRobot = vi.fn()
      render(<ControlPanel {...defaultProps} onRemoveRobot={onRemoveRobot} />)

      fireEvent.click(screen.getByText('Remove Robot'))
      expect(onRemoveRobot).toHaveBeenCalledOnce()
    })

    it('should call onResizeArena with correct size', () => {
      const onResizeArena = vi.fn()
      render(<ControlPanel {...defaultProps} onResizeArena={onResizeArena} />)

      fireEvent.click(screen.getByText('10x10'))
      expect(onResizeArena).toHaveBeenCalledWith(10)

      fireEvent.click(screen.getByText('15x15'))
      expect(onResizeArena).toHaveBeenCalledWith(15)

      fireEvent.click(screen.getByText('20x20'))
      expect(onResizeArena).toHaveBeenCalledWith(20)
    })

    it('should call onTogglePause when pause/play clicked', () => {
      const onTogglePause = vi.fn()
      render(<ControlPanel {...defaultProps} onTogglePause={onTogglePause} />)

      fireEvent.click(screen.getByText('▶ Play'))
      expect(onTogglePause).toHaveBeenCalledOnce()
    })

    it('should call onToggleObstacleMode when mode button clicked', () => {
      const onToggleObstacleMode = vi.fn()
      render(<ControlPanel {...defaultProps} onToggleObstacleMode={onToggleObstacleMode} />)

      fireEvent.click(screen.getByText('Place Mode'))
      expect(onToggleObstacleMode).toHaveBeenCalledOnce()
    })

    it('should call onReset when Reset clicked', () => {
      const onReset = vi.fn()
      render(<ControlPanel {...defaultProps} onReset={onReset} />)

      fireEvent.click(screen.getByText('Reset'))
      expect(onReset).toHaveBeenCalledOnce()
    })

    it('should call onClearAll when Clear All clicked', () => {
      const onClearAll = vi.fn()
      render(<ControlPanel {...defaultProps} onClearAll={onClearAll} />)

      fireEvent.click(screen.getByText('Clear All'))
      expect(onClearAll).toHaveBeenCalledOnce()
    })
  })

  describe('Speed Controls', () => {
    it('should increase speed when Speed+ clicked', () => {
      const onSpeedChange = vi.fn()
      render(<ControlPanel {...defaultProps} simulationSpeed={5} onSpeedChange={onSpeedChange} />)

      fireEvent.click(screen.getByText('Speed +'))
      expect(onSpeedChange).toHaveBeenCalledWith(5.5)
    })

    it('should decrease speed when Speed- clicked', () => {
      const onSpeedChange = vi.fn()
      render(<ControlPanel {...defaultProps} simulationSpeed={5} onSpeedChange={onSpeedChange} />)

      fireEvent.click(screen.getByText('Speed -'))
      expect(onSpeedChange).toHaveBeenCalledWith(4.5)
    })

    it('should not exceed max speed of 10', () => {
      const onSpeedChange = vi.fn()
      render(<ControlPanel {...defaultProps} simulationSpeed={10} onSpeedChange={onSpeedChange} />)

      fireEvent.click(screen.getByText('Speed +'))
      expect(onSpeedChange).not.toHaveBeenCalled()
    })

    it('should not go below min speed of 0.5', () => {
      const onSpeedChange = vi.fn()
      render(<ControlPanel {...defaultProps} simulationSpeed={0.5} onSpeedChange={onSpeedChange} />)

      fireEvent.click(screen.getByText('Speed -'))
      expect(onSpeedChange).not.toHaveBeenCalled()
    })
  })

  describe('Button States', () => {
    it('should disable Remove Robot when robot count is 0', () => {
      render(<ControlPanel {...defaultProps} robotCount={0} />)

      const removeButton = screen.getByText('Remove Robot')
      expect(removeButton.closest('button')).toHaveProperty('disabled', true)
    })

    it('should disable Add Robot when robot count is 10', () => {
      render(<ControlPanel {...defaultProps} robotCount={10} />)

      const addButton = screen.getByText('Add Robot')
      expect(addButton.closest('button')).toHaveProperty('disabled', true)
    })
  })
})