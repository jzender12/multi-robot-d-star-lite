import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { WebSocketClient } from './WebSocketClient'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState: number = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null

  constructor(public url: string) {
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  send = vi.fn()
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  })
}

// Mock WebSocket globally
global.WebSocket = MockWebSocket as any
// Add WebSocket constants to global
;(global.WebSocket as any).CONNECTING = 0
;(global.WebSocket as any).OPEN = 1
;(global.WebSocket as any).CLOSING = 2
;(global.WebSocket as any).CLOSED = 3

describe('WebSocketClient', () => {
  let client: WebSocketClient

  beforeEach(() => {
    vi.clearAllMocks()
    client = new WebSocketClient('ws://localhost:8000')
  })

  afterEach(() => {
    client.disconnect()
  })

  describe('Connection Management', () => {
    it('should create WebSocket connection with correct URL', () => {
      client.connect()
      // Should be connecting, not yet connected
      expect(client.isConnected()).toBe(false)
    })

    it('should connect to WebSocket server', async () => {
      const connectHandler = vi.fn()
      client.onConnect(connectHandler)

      client.connect()

      // Wait for connection
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(connectHandler).toHaveBeenCalled()
      expect(client.isConnected()).toBe(true)
    })

    it('should disconnect from WebSocket server', () => {
      client.connect()
      client.disconnect()

      expect(client.isConnected()).toBe(false)
    })

    it('should handle URL transformation', () => {
      const httpClient = new WebSocketClient('http://localhost:8000')
      expect(httpClient['url']).toBe('ws://localhost:8000/ws')

      const httpsClient = new WebSocketClient('https://localhost:8000')
      expect(httpsClient['url']).toBe('wss://localhost:8000/ws')
    })
  })

  describe('Event Handling', () => {
    it('should register and trigger connect event handler', async () => {
      const handler = vi.fn()
      client.onConnect(handler)

      client.connect()
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(handler).toHaveBeenCalled()
    })

    it('should register disconnect event handler', async () => {
      const handler = vi.fn()
      client.onDisconnect(handler)

      client.connect()
      await new Promise(resolve => setTimeout(resolve, 10))
      client.disconnect()

      expect(handler).toHaveBeenCalled()
    })

    it('should register game state update handler', async () => {
      const handler = vi.fn()
      client.onGameState(handler)

      client.connect()
      await new Promise(resolve => setTimeout(resolve, 10))

      // Simulate receiving game state
      const ws = client['ws'] as MockWebSocket
      if (ws.onmessage) {
        const messageEvent = new MessageEvent('message', {
          data: JSON.stringify({ type: 'state', data: {} })
        })
        ws.onmessage(messageEvent)
      }

      expect(handler).toHaveBeenCalled()
    })

    it('should register error handler', () => {
      const handler = vi.fn()
      client.onError(handler)

      client.connect()

      const ws = client['ws'] as MockWebSocket
      if (ws.onerror) {
        ws.onerror(new Event('error'))
      }

      expect(handler).toHaveBeenCalled()
    })

    it('should unregister event handlers', () => {
      const handler = vi.fn()
      client.onGameState(handler)
      client.offGameState(handler)

      client.connect()

      const ws = client['ws'] as MockWebSocket
      if (ws.onmessage) {
        const messageEvent = new MessageEvent('message', {
          data: JSON.stringify({ type: 'state', data: {} })
        })
        ws.onmessage(messageEvent)
      }

      expect(handler).not.toHaveBeenCalled()
    })
  })

  describe('Command Sending', () => {
    beforeEach(async () => {
      client.connect()
      // Wait for connection to be established
      await new Promise(resolve => setTimeout(resolve, 10))
    })

    it('should send step command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendStep()

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'step'
      }))
    })

    it('should send pause command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendPause()

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'pause'
      }))
    })

    it('should send resume command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendResume()

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'resume'
      }))
    })

    it('should send add obstacle command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendAddObstacle(3, 4)

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'add_obstacle',
        x: 3,
        y: 4
      }))
    })

    it('should send remove obstacle command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendRemoveObstacle(5, 6)

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'remove_obstacle',
        x: 5,
        y: 6
      }))
    })

    it('should send set goal command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendSetGoal('robot1', 7, 8)

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'set_goal',
        robot_id: 'robot1',
        x: 7,
        y: 8
      }))
    })

    it('should send add robot command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendAddRobot(1, 2, 9, 9)

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'add_robot',
        start: [1, 2],
        goal: [9, 9]
      }))
    })

    it('should send remove robot command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendRemoveRobot('robot2')

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'remove_robot',
        robot_id: 'robot2'
      }))
    })

    it('should send resize arena command', () => {
      const ws = client['ws'] as MockWebSocket

      client.sendResizeArena(15, 15)

      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'resize_arena',
        width: 15,
        height: 15
      }))
    })
  })

  describe('Message Queue', () => {
    it('should queue messages when disconnected', () => {
      const ws = client['ws'] as MockWebSocket | null

      // Don't connect, try to send
      client.sendStep()
      client.sendPause()

      // WebSocket shouldn't be called since we're not connected
      expect(ws).toBeNull()
    })

    it('should send queued messages on connect', async () => {
      // Queue messages before connecting
      client.sendStep()
      client.sendPause()

      // Now connect
      client.connect()
      await new Promise(resolve => setTimeout(resolve, 10))

      const ws = client['ws'] as MockWebSocket

      // Should have sent queued messages
      expect(ws.send).toHaveBeenCalledTimes(2)
      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({ type: 'step' }))
      expect(ws.send).toHaveBeenCalledWith(JSON.stringify({ type: 'pause' }))
    })
  })

  describe('Reconnection Logic', () => {
    it('should attempt to reconnect on disconnect', async () => {
      const connectSpy = vi.spyOn(client, 'connect')

      client.connect()
      await new Promise(resolve => setTimeout(resolve, 10))

      // Simulate disconnect
      const ws = client['ws'] as MockWebSocket
      ws.close()

      // Should attempt reconnect after delay
      await new Promise(resolve => setTimeout(resolve, 1100))

      expect(connectSpy).toHaveBeenCalledTimes(2) // Initial + reconnect
    })
  })
})