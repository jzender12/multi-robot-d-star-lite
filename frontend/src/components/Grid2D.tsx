import React, { useRef, useEffect, useState } from 'react'
import { useGameStore } from '../store/gameStore'
import { getRobotColors } from '../utils/colors'
import { gridToPixel, pixelToGrid, isValidGridPos } from '../utils/coordinates'
import styles from './Grid2D.module.css'

interface Grid2DProps {
  cellSize?: number
}

export const Grid2D: React.FC<Grid2DProps> = ({ cellSize = 50 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [lastDragCell, setLastDragCell] = useState<[number, number] | null>(null)
  const [mousePos, setMousePos] = useState<[number, number] | null>(null)

  const {
    gridSize,
    robots,
    obstacles,
    paths,
    selectedRobot,
    pausedRobots,
    stuckRobots,
    goalBlockedRobots,
    collisionInfo,
    cursorMode,
    robotPlacementMode,
    placingRobotGoal,
    ghostPosition,
    selectRobot,
    addObstacle,
    removeObstacle,
    setGoal,
    addRobot,
    setRobotPlacementMode,
    setPlacingRobotGoal,
    setGhostPosition,
    addLog
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
    ctx.strokeStyle = '#2a2a35'
    ctx.lineWidth = 0.5
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
    ctx.fillStyle = '#2d2d35'
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

      // Draw goal marker (square)
      ctx.fillStyle = colors.goal
      const goalSize = cellSize / 2
      ctx.fillRect(goalX - goalSize / 2, goalY - goalSize / 2, goalSize, goalSize)

      // Draw goal label
      ctx.fillStyle = '#0a0a0f'
      ctx.font = '12px monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      const robotNumber = robotId.replace('robot', '')
      ctx.fillText(robotNumber, goalX, goalY)
    })

    // Draw robots
    Object.entries(robots).forEach(([robotId, robot]) => {
      const colors = getRobotColors(robotId)
      const [robotX, robotY] = gridToPixel(robot.pos[0], robot.pos[1], cellSize)

      // Draw selection highlight
      if (selectedRobot === robotId) {
        ctx.strokeStyle = '#a855f7'
        ctx.lineWidth = 2
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
        // Muted orange border for collision
        ctx.strokeStyle = '#ea580c'
        ctx.lineWidth = 2
        ctx.strokeRect(
          robot.pos[0] * cellSize + 5,
          robot.pos[1] * cellSize + 5,
          cellSize - 10,
          cellSize - 10
        )
      } else if (goalBlockedRobots.includes(robotId)) {
        // Yellow border for goal-blocked robots (goal has obstacle)
        ctx.strokeStyle = '#eab308'
        ctx.lineWidth = 2
        ctx.strokeRect(
          robot.pos[0] * cellSize + 5,
          robot.pos[1] * cellSize + 5,
          cellSize - 10,
          cellSize - 10
        )
      } else if (stuckRobots.includes(robotId)) {
        // Muted red border for stuck robots (cannot reach goal)
        ctx.strokeStyle = '#dc2626'
        ctx.lineWidth = 2
        ctx.strokeRect(
          robot.pos[0] * cellSize + 5,
          robot.pos[1] * cellSize + 5,
          cellSize - 10,
          cellSize - 10
        )
      }

      // Check if robot is at its goal
      const isAtGoal = robot.pos[0] === robot.goal[0] && robot.pos[1] === robot.goal[1]
      if (isAtGoal) {
        // Green border for robots at goal
        ctx.strokeStyle = '#22c55e'
        ctx.lineWidth = 3
        ctx.strokeRect(
          robot.pos[0] * cellSize + 3,
          robot.pos[1] * cellSize + 3,
          cellSize - 6,
          cellSize - 6
        )
      }

      // Draw robot
      ctx.fillStyle = colors.main
      ctx.beginPath()
      ctx.arc(robotX, robotY, cellSize / 3, 0, Math.PI * 2)
      ctx.fill()

      // Draw robot ID
      ctx.fillStyle = '#0a0a0f'
      ctx.font = 'bold 14px monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      const robotNum = robotId.replace('robot', '')
      ctx.fillText(robotNum, robotX, robotY)
    })

    // Draw ghost robot preview when in placement mode
    if (robotPlacementMode && ghostPosition) {
      const [ghostX, ghostY] = gridToPixel(ghostPosition[0], ghostPosition[1], cellSize)

      // Draw semi-transparent purple circle
      ctx.fillStyle = 'rgba(124, 58, 237, 0.5)'
      ctx.beginPath()
      ctx.arc(ghostX, ghostY, cellSize / 3, 0, Math.PI * 2)
      ctx.fill()

      // Draw preview text
      ctx.fillStyle = 'rgba(10, 10, 15, 0.5)'
      ctx.font = 'bold 14px monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText('?', ghostX, ghostY)
    }
  }, [gridSize, robots, obstacles, paths, selectedRobot, stuckRobots, goalBlockedRobots, collisionInfo, cellSize, canvasWidth, canvasHeight, width, height, robotPlacementMode, ghostPosition])

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const [gridX, gridY] = pixelToGrid(x, y, cellSize)

    if (!isValidGridPos(gridX, gridY, width, height)) return

    // Handle robot placement mode
    if (robotPlacementMode) {
      const hasRobot = Object.values(robots).some(
        robot => robot.pos[0] === gridX && robot.pos[1] === gridY
      )
      const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)

      if (!hasRobot && !isObstacle) {
        // Place robot with temporary goal at same position
        useGameStore.setState({ expectingNewRobot: true })
        addRobot(gridX, gridY, gridX, gridY)
        setRobotPlacementMode(false)
        // The robot will be auto-selected when the state update arrives
      }
      return
    }

    // Handle goal placement after robot placement
    if (placingRobotGoal && selectedRobot) {
      const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)
      // Check if another robot already has this goal
      const isGoalTaken = Object.entries(robots).some(
        ([id, robot]) => id !== selectedRobot &&
          robot.goal[0] === gridX && robot.goal[1] === gridY
      )
      // Allow placing goal on any position except obstacles and other robots' goals
      if (!isObstacle && !isGoalTaken) {
        setGoal(selectedRobot, gridX, gridY)
        setPlacingRobotGoal(false)
        selectRobot(null)
      }
      return
    }

    // Select mode: only handle robot selection and goal setting
    if (cursorMode === 'select') {
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
      } else if (selectedRobot) {
        // Set goal for selected robot
        const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)
        // Check if another robot already has this goal
        const isGoalTaken = Object.entries(robots).some(
          ([id, robot]) => id !== selectedRobot &&
            robot.goal[0] === gridX && robot.goal[1] === gridY
        )
        if (!isObstacle && !isGoalTaken) {
          setGoal(selectedRobot, gridX, gridY)
          selectRobot(null)
        }
      }
      return
    }

    // Draw/Erase modes: handle obstacles
    const hasRobot = Object.values(robots).some(
      robot => robot.pos[0] === gridX && robot.pos[1] === gridY
    )

    // Allow obstacles on goals but not on robots
    if (!hasRobot) {
      const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)

      if (cursorMode === 'draw' && !isObstacle) {
        addObstacle(gridX, gridY)
      } else if (cursorMode === 'erase' && isObstacle) {
        removeObstacle(gridX, gridY)
      }
    }
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (cursorMode === 'draw' || cursorMode === 'erase') {
      setIsDragging(true)
      handleDragMode(e)
    } else {
      handleCanvasClick(e)
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const [gridX, gridY] = pixelToGrid(x, y, cellSize)

    // Update ghost position for robot placement preview
    if (robotPlacementMode && isValidGridPos(gridX, gridY, width, height)) {
      const hasRobot = Object.values(robots).some(
        robot => robot.pos[0] === gridX && robot.pos[1] === gridY
      )
      const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)

      if (!hasRobot && !isObstacle) {
        setGhostPosition([gridX, gridY])
      } else {
        setGhostPosition(null)
      }
    }

    if (isDragging && (cursorMode === 'draw' || cursorMode === 'erase')) {
      handleDragMode(e)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    setLastDragCell(null)
  }

  const handleMouseLeave = () => {
    setIsDragging(false)
    setLastDragCell(null)
    if (robotPlacementMode) {
      setGhostPosition(null)
    }
  }

  const getCursorClassName = () => {
    if (robotPlacementMode) return styles.canvasCopy
    if (placingRobotGoal) return styles.canvasCrosshair

    switch (cursorMode) {
      case 'select':
        return selectedRobot ? styles.canvasCrosshair : styles.canvasPointer
      case 'draw':
        return styles.canvasCrosshair
      case 'erase':
        return styles.canvasGrab
      default:
        return styles.canvasPointer
    }
  }

  const handleDragMode = (e: React.MouseEvent<HTMLCanvasElement>) => {
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

    // Don't place obstacles on robots (but allow on goals)
    const hasRobot = Object.values(robots).some(
      robot => robot.pos[0] === gridX && robot.pos[1] === gridY
    )

    if (!hasRobot) {
      const isObstacle = obstacles.some(([ox, oy]) => ox === gridX && oy === gridY)

      if (cursorMode === 'draw' && !isObstacle) {
        addObstacle(gridX, gridY)
      } else if (cursorMode === 'erase' && isObstacle) {
        removeObstacle(gridX, gridY)
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
      onMouseLeave={handleMouseLeave}
      className={`${styles.canvas} ${getCursorClassName()}`}
    />
  )
}