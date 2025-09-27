import React, { useRef, useEffect, useState } from 'react'
import { useGameStore } from '../store/gameStore'
import { getRobotColors } from '../utils/colors'
import { gridToPixel, pixelToGrid, isValidGridPos } from '../utils/coordinates'

interface Grid2DProps {
  cellSize?: number
}

export const Grid2D: React.FC<Grid2DProps> = ({ cellSize = 50 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [lastDragCell, setLastDragCell] = useState<[number, number] | null>(null)

  const {
    gridSize,
    robots,
    obstacles,
    paths,
    selectedRobot,
    pausedRobots,
    stuckRobots,
    collisionInfo,
    obstacleMode,
    selectRobot,
    addObstacle,
    removeObstacle,
    setGoal
  } = useGameStore()

  const [width, height] = gridSize
  const canvasWidth = width * cellSize
  const canvasHeight = height * cellSize

  // Draw the grid
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvasWidth, canvasHeight)

    // Draw grid lines
    ctx.strokeStyle = '#ccc'
    ctx.lineWidth = 1
    for (let i = 0; i <= width; i++) {
      ctx.beginPath()
      ctx.moveTo(i * cellSize, 0)
      ctx.lineTo(i * cellSize, canvasHeight)
      ctx.stroke()
    }
    for (let j = 0; j <= height; j++) {
      ctx.beginPath()
      ctx.moveTo(0, j * cellSize)
      ctx.lineTo(canvasWidth, j * cellSize)
      ctx.stroke()
    }

    // Draw obstacles
    ctx.fillStyle = '#323232'
    obstacles.forEach(([x, y]) => {
      ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize)
    })

    // Draw paths
    Object.entries(paths).forEach(([robotId, path]) => {
      if (!path || path.length < 2) return

      const colors = getRobotColors(robotId)
      ctx.strokeStyle = colors.path
      ctx.lineWidth = 3
      ctx.setLineDash([5, 5])

      ctx.beginPath()
      const [startX, startY] = gridToPixel(path[0][0], path[0][1], cellSize)
      ctx.moveTo(startX, startY)

      for (let i = 1; i < path.length; i++) {
        const [x, y] = gridToPixel(path[i][0], path[i][1], cellSize)
        ctx.lineTo(x, y)
      }
      ctx.stroke()
      ctx.setLineDash([])
    })

    // Draw goals
    Object.entries(robots).forEach(([robotId, robot]) => {
      const colors = getRobotColors(robotId)
      const [goalX, goalY] = gridToPixel(robot.goal[0], robot.goal[1], cellSize)

      // Draw goal marker
      ctx.fillStyle = colors.goal
      ctx.beginPath()
      ctx.arc(goalX, goalY, cellSize / 4, 0, Math.PI * 2)
      ctx.fill()

      // Draw goal label
      ctx.fillStyle = 'white'
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText('G', goalX, goalY)
    })

    // Draw robots
    Object.entries(robots).forEach(([robotId, robot]) => {
      const colors = getRobotColors(robotId)
      const [robotX, robotY] = gridToPixel(robot.pos[0], robot.pos[1], cellSize)

      // Draw selection highlight
      if (selectedRobot === robotId) {
        ctx.strokeStyle = '#FFD700'
        ctx.lineWidth = 3
        ctx.strokeRect(
          robot.pos[0] * cellSize + 2,
          robot.pos[1] * cellSize + 2,
          cellSize - 4,
          cellSize - 4
        )
      }

      // Check if robot is in collision
      const isInCollision = collisionInfo && collisionInfo.some(collision =>
        collision.robots.includes(robotId)
      )

      // Draw collision or stuck indicator
      if (isInCollision) {
        // Orange thick border for collision
        ctx.strokeStyle = '#FF6600'
        ctx.lineWidth = 3
        ctx.strokeRect(
          robot.pos[0] * cellSize + 5,
          robot.pos[1] * cellSize + 5,
          cellSize - 10,
          cellSize - 10
        )
      } else if (stuckRobots.includes(robotId)) {
        // Red border for stuck robots (cannot reach goal)
        ctx.strokeStyle = '#FF0000'
        ctx.lineWidth = 2
        ctx.strokeRect(
          robot.pos[0] * cellSize + 5,
          robot.pos[1] * cellSize + 5,
          cellSize - 10,
          cellSize - 10
        )
      }

      // Draw robot
      ctx.fillStyle = colors.main
      ctx.beginPath()
      ctx.arc(robotX, robotY, cellSize / 3, 0, Math.PI * 2)
      ctx.fill()

      // Draw robot ID
      ctx.fillStyle = 'white'
      ctx.font = 'bold 14px Arial'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(robotId.replace('robot', 'R'), robotX, robotY)
    })
  }, [gridSize, robots, obstacles, paths, selectedRobot, stuckRobots, collisionInfo, cellSize, canvasWidth, canvasHeight, width, height])

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const [gridX, gridY] = pixelToGrid(x, y, cellSize)

    if (!isValidGridPos(gridX, gridY, width, height)) return

    // Check if clicking on a robot
    const clickedRobot = Object.entries(robots).find(
      ([_, robot]) => robot.pos[0] === gridX && robot.pos[1] === gridY
    )

    if (clickedRobot) {
      const [robotId] = clickedRobot
      if (selectedRobot === robotId) {
        selectRobot(null)
      } else {
        selectRobot(robotId)
      }
      return
    }

    // If robot is selected, set its goal
    if (selectedRobot) {
      // Check if position is valid for goal (not on obstacle or other robot)
      const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)
      if (!isObstacle) {
        setGoal(selectedRobot, gridX, gridY)
        selectRobot(null)
      }
      return
    }

    // Otherwise, toggle obstacle
    const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)
    const isGoal = Object.values(robots).some(
      robot => robot.goal[0] === gridX && robot.goal[1] === gridY
    )

    if (!isGoal) {
      if (isObstacle) {
        removeObstacle(gridX, gridY)
      } else {
        addObstacle(gridX, gridY)
      }
    }
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (obstacleMode === 'draw') {
      setIsDragging(true)
      handleDrawMode(e)
    } else {
      handleCanvasClick(e)
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging && obstacleMode === 'draw') {
      handleDrawMode(e)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    setLastDragCell(null)
  }

  const handleDrawMode = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const [gridX, gridY] = pixelToGrid(x, y, cellSize)

    if (!isValidGridPos(gridX, gridY, width, height)) return

    // Check if this is a new cell
    if (lastDragCell && lastDragCell[0] === gridX && lastDragCell[1] === gridY) {
      return
    }

    setLastDragCell([gridX, gridY])

    // Don't place obstacles on robots or goals
    const hasRobot = Object.values(robots).some(
      robot => robot.pos[0] === gridX && robot.pos[1] === gridY
    )
    const hasGoal = Object.values(robots).some(
      robot => robot.goal[0] === gridX && robot.goal[1] === gridY
    )

    if (!hasRobot && !hasGoal) {
      const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)
      if (!isObstacle) {
        addObstacle(gridX, gridY)
      }
    }
  }

  return (
    <canvas
      ref={canvasRef}
      width={canvasWidth}
      height={canvasHeight}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{
        border: '2px solid #333',
        cursor: selectedRobot ? 'crosshair' : 'pointer',
        display: 'block'
      }}
    />
  )
}