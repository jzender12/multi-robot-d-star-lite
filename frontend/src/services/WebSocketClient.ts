export interface GameState {
  width: number
  height: number
  robots: Record<string, RobotState>
  obstacles: Array<[number, number]>
  paused: boolean
  collision_info: CollisionInfo | null
  stuck_robots: string[]
}

export interface RobotState {
  id: string
  position: [number, number]
  goal: [number, number]
  path: Array<[number, number]>
  is_stuck: boolean
  is_paused: boolean
}

export interface CollisionInfo {
  type: string
  robots: string[]
  positions: Array<[number, number]>
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private messageQueue: any[] = []
  private listeners: Map<string, Set<Function>> = new Map()

  constructor(url: string) {
    // Convert http URL to ws URL
    this.url = url.replace('http://', 'ws://').replace('https://', 'wss://')
    if (!this.url.endsWith('/ws')) {
      this.url += '/ws'
    }
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.flushMessageQueue()
        this.emit('connect')
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          // Handle different message types from backend
          if (data.type === 'state') {
            this.emit('game_state', data)
          } else if (data.type === 'error') {
            this.emit('error', data)
          } else {
            // Assume it's a game state if no type specified
            this.emit('game_state', data)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.emit('error', error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.emit('disconnect')
        this.handleReconnect()
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      this.handleReconnect()
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      setTimeout(() => this.connect(), delay)
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected()) {
      const message = this.messageQueue.shift()
      this.send(message)
    }
  }

  private send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      this.messageQueue.push(data)
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  // Event emitter methods
  private emit(event: string, data?: any): void {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.forEach(listener => listener(data))
    }
  }

  on(event: string, listener: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(listener)
  }

  off(event: string, listener: Function): void {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.delete(listener)
    }
  }

  // Convenience methods for event listeners
  onConnect(handler: () => void): void {
    this.on('connect', handler)
  }

  onDisconnect(handler: () => void): void {
    this.on('disconnect', handler)
  }

  onGameState(handler: (state: GameState) => void): void {
    this.on('game_state', handler)
  }

  onError(handler: (error: any) => void): void {
    this.on('error', handler)
  }

  offGameState(handler: (state: GameState) => void): void {
    this.off('game_state', handler)
  }

  // Command methods
  sendCommand(command: any): void {
    this.send(command)
  }

  sendStep(): void {
    this.sendCommand({ type: 'step' })
  }

  sendPause(): void {
    this.sendCommand({ type: 'pause' })
  }

  sendResume(): void {
    this.sendCommand({ type: 'resume' })
  }

  sendAddObstacle(x: number, y: number): void {
    this.sendCommand({ type: 'add_obstacle', x, y })
  }

  sendRemoveObstacle(x: number, y: number): void {
    this.sendCommand({ type: 'remove_obstacle', x, y })
  }

  sendSetGoal(robotId: string, goalX: number, goalY: number): void {
    this.sendCommand({
      type: 'set_goal',
      robot_id: robotId,
      x: goalX,
      y: goalY
    })
  }

  sendAddRobot(startX: number, startY: number, goalX: number, goalY: number): void {
    this.sendCommand({
      type: 'add_robot',
      start: [startX, startY],
      goal: [goalX, goalY]
    })
  }

  sendRemoveRobot(robotId: string): void {
    this.sendCommand({
      type: 'remove_robot',
      robot_id: robotId
    })
  }

  sendResizeArena(width: number, height: number): void {
    this.sendCommand({
      type: 'resize_arena',
      width,
      height
    })
  }
}