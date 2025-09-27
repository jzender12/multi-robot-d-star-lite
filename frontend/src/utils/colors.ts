/**
 * Generate consistent colors for robots
 */

export interface RobotColors {
  main: string
  path: string
  goal: string
}

const PREDEFINED_COLORS: Record<string, RobotColors> = {
  robot0: {
    main: '#0064C8',  // Blue
    path: 'rgba(0, 100, 200, 0.3)',
    goal: '#003264'
  },
  robot1: {
    main: '#C83200',  // Red
    path: 'rgba(200, 50, 0, 0.3)',
    goal: '#641900'
  }
}

const COLOR_PALETTE = [
  { main: '#00C864', path: 'rgba(0, 200, 100, 0.3)', goal: '#006432' },  // Green
  { main: '#C800C8', path: 'rgba(200, 0, 200, 0.3)', goal: '#640064' },  // Purple
  { main: '#C8C800', path: 'rgba(200, 200, 0, 0.3)', goal: '#646400' },  // Yellow
  { main: '#00C8C8', path: 'rgba(0, 200, 200, 0.3)', goal: '#006464' },  // Cyan
  { main: '#FF6600', path: 'rgba(255, 102, 0, 0.3)', goal: '#803300' },  // Orange
  { main: '#FF0066', path: 'rgba(255, 0, 102, 0.3)', goal: '#800033' },  // Pink
]

export function getRobotColors(robotId: string): RobotColors {
  // Check predefined colors first
  if (PREDEFINED_COLORS[robotId]) {
    return PREDEFINED_COLORS[robotId]
  }

  // Generate color based on robot number
  const match = robotId.match(/\d+/)
  const robotNum = match ? parseInt(match[0]) : 0
  const colorIndex = (robotNum - 2) % COLOR_PALETTE.length

  return COLOR_PALETTE[colorIndex]
}