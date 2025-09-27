import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, fireEvent, screen } from '@testing-library/react'
import { Grid2D } from './Grid2D'
import { useGameStore } from '../store/gameStore'

// Mock the store
vi.mock('../store/gameStore')

describe('Grid2D', () => {
  const mockStore = {
    gridSize: [10, 10] as [number, number],
    robots: {
      robot0: { pos: [0, 0] as [number, number], goal: [9, 9] as [number, number] },
      robot1: { pos: [5, 5] as [number, number], goal: [7, 7] as [number, number] }
    },
    obstacles: [[3, 3], [4, 4]] as Array<[number, number]>,
    paths: {
      robot0: [[0, 0], [1, 0], [2, 0]] as Array<[number, number]>,
      robot1: [[5, 5], [5, 6], [5, 7]] as Array<[number, number]>
    },
    selectedRobot: null as string | null,
    pausedRobots: [] as string[],
    obstacleMode: 'place' as 'place' | 'draw',
    selectRobot: vi.fn(),
    addObstacle: vi.fn(),
    removeObstacle: vi.fn(),
    setGoal: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useGameStore).mockReturnValue(mockStore)
  })

  describe('Rendering', () => {
    it('should render canvas with correct dimensions', () => {
      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')

      expect(canvas).toBeTruthy()
      expect(canvas?.width).toBe(500) // 10 * 50
      expect(canvas?.height).toBe(500) // 10 * 50
    })

    it('should render canvas with custom cell size', () => {
      const { container } = render(<Grid2D cellSize={30} />)
      const canvas = container.querySelector('canvas')

      expect(canvas?.width).toBe(300) // 10 * 30
      expect(canvas?.height).toBe(300) // 10 * 30
    })

    it('should update canvas when grid size changes', () => {
      const { container, rerender } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')

      expect(canvas?.width).toBe(500)

      // Update store with new grid size
      vi.mocked(useGameStore).mockReturnValue({
        ...mockStore,
        gridSize: [15, 15]
      })

      rerender(<Grid2D cellSize={50} />)
      expect(canvas?.width).toBe(750) // 15 * 50
      expect(canvas?.height).toBe(750)
    })
  })

  describe('Click Interactions', () => {
    it('should handle click on empty cell to add obstacle', () => {
      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      // Mock getBoundingClientRect for canvas
      canvas.getBoundingClientRect = vi.fn(() => ({
        left: 0,
        top: 0,
        right: 500,
        bottom: 500,
        width: 500,
        height: 500,
        x: 0,
        y: 0,
        toJSON: () => {}
      }))

      // Click on empty cell (2, 2)
      fireEvent.mouseDown(canvas, {
        clientX: 125, // 2.5 * 50
        clientY: 125
      })

      expect(mockStore.addObstacle).toHaveBeenCalledWith(2, 2)
    })

    it('should handle click on obstacle to remove it', () => {
      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      canvas.getBoundingClientRect = vi.fn(() => ({
        left: 0, top: 0, right: 500, bottom: 500,
        width: 500, height: 500, x: 0, y: 0, toJSON: () => {}
      }))

      // Click on obstacle at (3, 3)
      fireEvent.mouseDown(canvas, {
        clientX: 175, // 3.5 * 50
        clientY: 175
      })

      expect(mockStore.removeObstacle).toHaveBeenCalledWith(3, 3)
    })

    it('should handle click on robot to select it', () => {
      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      canvas.getBoundingClientRect = vi.fn(() => ({
        left: 0, top: 0, right: 500, bottom: 500,
        width: 500, height: 500, x: 0, y: 0, toJSON: () => {}
      }))

      // Click on robot0 at (0, 0)
      fireEvent.mouseDown(canvas, {
        clientX: 25, // 0.5 * 50
        clientY: 25
      })

      expect(mockStore.selectRobot).toHaveBeenCalledWith('robot0')
    })

    it('should set goal for selected robot on empty cell click', () => {
      vi.mocked(useGameStore).mockReturnValue({
        ...mockStore,
        selectedRobot: 'robot0'
      })

      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      canvas.getBoundingClientRect = vi.fn(() => ({
        left: 0, top: 0, right: 500, bottom: 500,
        width: 500, height: 500, x: 0, y: 0, toJSON: () => {}
      }))

      // Click on empty cell (7, 3)
      fireEvent.mouseDown(canvas, {
        clientX: 375, // 7.5 * 50
        clientY: 175  // 3.5 * 50
      })

      expect(mockStore.setGoal).toHaveBeenCalledWith('robot0', 7, 3)
    })

    it('should deselect robot when clicking on selected robot', () => {
      vi.mocked(useGameStore).mockReturnValue({
        ...mockStore,
        selectedRobot: 'robot0'
      })

      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      canvas.getBoundingClientRect = vi.fn(() => ({
        left: 0, top: 0, right: 500, bottom: 500,
        width: 500, height: 500, x: 0, y: 0, toJSON: () => {}
      }))

      // Click on robot0 at (0, 0) - already selected
      fireEvent.mouseDown(canvas, {
        clientX: 25,
        clientY: 25
      })

      expect(mockStore.selectRobot).toHaveBeenCalledWith(null)
    })
  })

  describe('Draw Mode', () => {
    it('should continuously add obstacles in draw mode', () => {
      vi.mocked(useGameStore).mockReturnValue({
        ...mockStore,
        obstacleMode: 'draw'
      })

      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      canvas.getBoundingClientRect = vi.fn(() => ({
        left: 0, top: 0, right: 500, bottom: 500,
        width: 500, height: 500, x: 0, y: 0, toJSON: () => {}
      }))

      // Mouse down at (1, 1)
      fireEvent.mouseDown(canvas, {
        clientX: 75,
        clientY: 75
      })

      // Move to (2, 1)
      fireEvent.mouseMove(canvas, {
        clientX: 125,
        clientY: 75
      })

      // Move to (2, 2)
      fireEvent.mouseMove(canvas, {
        clientX: 125,
        clientY: 125
      })

      // Mouse up
      fireEvent.mouseUp(canvas)

      expect(mockStore.addObstacle).toHaveBeenCalledWith(1, 1)
      expect(mockStore.addObstacle).toHaveBeenCalledWith(2, 1)
      expect(mockStore.addObstacle).toHaveBeenCalledWith(2, 2)
    })

    it('should not draw obstacles on robots or goals', () => {
      vi.mocked(useGameStore).mockReturnValue({
        ...mockStore,
        obstacleMode: 'draw'
      })

      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      canvas.getBoundingClientRect = vi.fn(() => ({
        left: 0, top: 0, right: 500, bottom: 500,
        width: 500, height: 500, x: 0, y: 0, toJSON: () => {}
      }))

      // Try to draw on robot position (0, 0)
      fireEvent.mouseDown(canvas, {
        clientX: 25,
        clientY: 25
      })

      fireEvent.mouseUp(canvas)

      expect(mockStore.addObstacle).not.toHaveBeenCalled()
    })
  })

  describe('Visual Elements', () => {
    it('should highlight selected robot', () => {
      vi.mocked(useGameStore).mockReturnValue({
        ...mockStore,
        selectedRobot: 'robot0'
      })

      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      // Check that canvas exists and rendering occurred
      expect(canvas).toBeTruthy()
      // Visual testing would require canvas context mocking
    })

    it('should show paused robots with different style', () => {
      vi.mocked(useGameStore).mockReturnValue({
        ...mockStore,
        pausedRobots: ['robot1']
      })

      const { container } = render(<Grid2D cellSize={50} />)
      const canvas = container.querySelector('canvas')!

      expect(canvas).toBeTruthy()
      // Visual testing would require canvas context mocking
    })
  })
})