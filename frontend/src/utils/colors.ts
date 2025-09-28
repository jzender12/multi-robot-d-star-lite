/**
 * Generate consistent colors for robots
 * Cool, techy, purple-based palette with high contrast
 */

export interface RobotColors {
  main: string
  path: string
  goal: string
}

// Distinct color themes for each robot - cool, techy, purple-based palette
const ROBOT_THEMES: RobotColors[] = [
  // Robot 0 - Deep violet
  {
    main: '#7c3aed',
    path: 'rgba(124, 58, 237, 0.4)',
    goal: '#9333ea'
  },
  // Robot 1 - Electric cyan
  {
    main: '#06b6d4',
    path: 'rgba(6, 182, 212, 0.4)',
    goal: '#22d3ee'
  },
  // Robot 2 - Hot magenta
  {
    main: '#ec4899',
    path: 'rgba(236, 72, 153, 0.4)',
    goal: '#f472b6'
  },
  // Robot 3 - Electric lime
  {
    main: '#84cc16',
    path: 'rgba(132, 204, 22, 0.4)',
    goal: '#a3e635'
  },
  // Robot 4 - Neon orange
  {
    main: '#f97316',
    path: 'rgba(249, 115, 22, 0.4)',
    goal: '#fb923c'
  },
  // Robot 5 - Teal
  {
    main: '#14b8a6',
    path: 'rgba(20, 184, 166, 0.4)',
    goal: '#2dd4bf'
  },
  // Robot 6 - Soft lavender
  {
    main: '#a78bfa',
    path: 'rgba(167, 139, 250, 0.4)',
    goal: '#c4b5fd'
  },
  // Robot 7 - Gold
  {
    main: '#eab308',
    path: 'rgba(234, 179, 8, 0.4)',
    goal: '#facc15'
  },
  // Robot 8 - Rose
  {
    main: '#f43f5e',
    path: 'rgba(244, 63, 94, 0.4)',
    goal: '#fb7185'
  },
  // Robot 9 - Mint
  {
    main: '#10b981',
    path: 'rgba(16, 185, 129, 0.4)',
    goal: '#34d399'
  }
]

export function getRobotColors(robotId: string): RobotColors {
  // Extract robot number from robotId (e.g., "robot0" -> 0)
  const match = robotId.match(/robot(\d+)/)
  if (!match) {
    // Fallback to first theme if no match
    return ROBOT_THEMES[0]
  }

  const robotNum = parseInt(match[1], 10)

  // Use modulo to cycle through themes if we have more than 10 robots
  return ROBOT_THEMES[robotNum % ROBOT_THEMES.length]
}