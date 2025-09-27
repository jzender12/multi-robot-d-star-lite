/**
 * Coordinate transformation utilities
 */

export function gridToPixel(
  gridX: number,
  gridY: number,
  cellSize: number
): [number, number] {
  return [
    gridX * cellSize + cellSize / 2,
    gridY * cellSize + cellSize / 2
  ]
}

export function pixelToGrid(
  pixelX: number,
  pixelY: number,
  cellSize: number
): [number, number] {
  return [
    Math.floor(pixelX / cellSize),
    Math.floor(pixelY / cellSize)
  ]
}

export function isValidGridPos(
  x: number,
  y: number,
  width: number,
  height: number
): boolean {
  return x >= 0 && x < width && y >= 0 && y < height
}