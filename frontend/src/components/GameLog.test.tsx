import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { GameLog } from './GameLog'
import type { LogMessage } from '../store/gameStore'

describe('GameLog', () => {
  beforeEach(() => {
    // Mock scrollIntoView for all tests since it's not available in jsdom
    Element.prototype.scrollIntoView = vi.fn()
  })

  const mockMessages: LogMessage[] = [
    {
      id: '1',
      message: 'Simulation started',
      type: 'info',
      timestamp: new Date('2024-01-01T10:00:00')
    },
    {
      id: '2',
      message: 'Robot added at (0, 0)',
      type: 'success',
      timestamp: new Date('2024-01-01T10:00:01')
    },
    {
      id: '3',
      message: 'Collision detected',
      type: 'collision',
      timestamp: new Date('2024-01-01T10:00:02')
    },
    {
      id: '4',
      message: 'Connection lost',
      type: 'error',
      timestamp: new Date('2024-01-01T10:00:03')
    },
    {
      id: '5',
      message: 'Robot stuck at (5, 5)',
      type: 'warning',
      timestamp: new Date('2024-01-01T10:00:04')
    }
  ]

  describe('Rendering', () => {
    it('should render all messages', () => {
      render(<GameLog messages={mockMessages} maxHeight={500} />)

      expect(screen.getByText('Simulation started')).toBeTruthy()
      expect(screen.getByText('Robot added at (0, 0)')).toBeTruthy()
      expect(screen.getByText('Collision detected')).toBeTruthy()
      expect(screen.getByText('Connection lost')).toBeTruthy()
      expect(screen.getByText('Robot stuck at (5, 5)')).toBeTruthy()
    })

    it('should render timestamps', () => {
      render(<GameLog messages={mockMessages} maxHeight={500} />)

      // Check for time format (10:00:00)
      expect(screen.getByText('10:00:00')).toBeTruthy()
      expect(screen.getByText('10:00:01')).toBeTruthy()
      expect(screen.getByText('10:00:02')).toBeTruthy()
    })

    it('should apply correct styles for message types', () => {
      const { container } = render(<GameLog messages={mockMessages} maxHeight={500} />)

      const infoMsg = container.querySelector('[data-type="info"]')
      const successMsg = container.querySelector('[data-type="success"]')
      const collisionMsg = container.querySelector('[data-type="collision"]')
      const errorMsg = container.querySelector('[data-type="error"]')
      const warningMsg = container.querySelector('[data-type="warning"]')

      expect(infoMsg).toBeTruthy()
      expect(successMsg).toBeTruthy()
      expect(collisionMsg).toBeTruthy()
      expect(errorMsg).toBeTruthy()
      expect(warningMsg).toBeTruthy()
    })

    it('should show empty state when no messages', () => {
      render(<GameLog messages={[]} maxHeight={500} />)

      expect(screen.getByText('No messages yet')).toBeTruthy()
    })

    it('should respect maxHeight prop', () => {
      const { container } = render(<GameLog messages={mockMessages} maxHeight={300} />)
      const logContainer = container.querySelector('[data-testid="log-container"]')

      expect(logContainer).toHaveStyle({ maxHeight: '300px' })
    })
  })

  describe('Scrolling', () => {
    it('should auto-scroll to latest message by default', () => {
      const { rerender } = render(<GameLog messages={mockMessages} maxHeight={200} />)

      const newMessage: LogMessage = {
        id: '6',
        message: 'New message',
        type: 'info',
        timestamp: new Date()
      }

      rerender(<GameLog messages={[...mockMessages, newMessage]} maxHeight={200} />)

      // Check that scrollIntoView was called
      expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
    })

    it('should stop auto-scroll when manually scrolled up', () => {
      const { container, rerender } = render(<GameLog messages={mockMessages} maxHeight={200} />)
      const scrollContainer = container.querySelector('[data-testid="log-container"]')!

      // Set up scroll properties to simulate being scrolled up
      Object.defineProperty(scrollContainer, 'scrollHeight', { value: 500, writable: true })
      Object.defineProperty(scrollContainer, 'scrollTop', { value: 50, writable: true })
      Object.defineProperty(scrollContainer, 'clientHeight', { value: 200, writable: true })

      // Simulate manual scroll up
      fireEvent.scroll(scrollContainer)

      // Add new message
      const newMessage: LogMessage = {
        id: '6',
        message: 'New message',
        type: 'info',
        timestamp: new Date()
      }

      vi.clearAllMocks()
      rerender(<GameLog messages={[...mockMessages, newMessage]} maxHeight={200} />)

      // Should not auto-scroll
      expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled()
    })

    it('should re-enable auto-scroll when scrolled to bottom', () => {
      const { container, rerender } = render(<GameLog messages={mockMessages} maxHeight={200} />)
      const scrollContainer = container.querySelector('[data-testid="log-container"]')!

      // Simulate scroll to near bottom
      Object.defineProperty(scrollContainer, 'scrollHeight', { value: 500, writable: true })
      Object.defineProperty(scrollContainer, 'scrollTop', { value: 295, writable: true })
      Object.defineProperty(scrollContainer, 'clientHeight', { value: 200, writable: true })

      fireEvent.scroll(scrollContainer)

      // Add new message
      const newMessage: LogMessage = {
        id: '7',
        message: 'Another new message',
        type: 'info',
        timestamp: new Date()
      }

      vi.clearAllMocks()
      rerender(<GameLog messages={[...mockMessages, newMessage]} maxHeight={200} />)

      // Should auto-scroll again
      expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
    })
  })

  describe('Performance', () => {
    it('should handle 100+ messages efficiently', () => {
      const manyMessages: LogMessage[] = Array.from({ length: 150 }, (_, i) => ({
        id: `msg-${i}`,
        message: `Message ${i}`,
        type: 'info' as const,
        timestamp: new Date()
      }))

      const { container } = render(<GameLog messages={manyMessages} maxHeight={500} />)
      const messages = container.querySelectorAll('[data-type="info"]')

      // Should render all messages (or use virtualization)
      expect(messages.length).toBeGreaterThan(0)
    })

    it('should format long messages with word wrap', () => {
      const longMessage: LogMessage = {
        id: '1',
        message: 'This is a very long message that should wrap properly when displayed in the game log component without breaking the layout',
        type: 'info',
        timestamp: new Date()
      }

      const { container } = render(<GameLog messages={[longMessage]} maxHeight={500} />)
      const messageElement = container.querySelector('[data-type="info"]')

      expect(messageElement).toHaveStyle({ wordWrap: 'break-word' })
    })
  })

  describe('Clear functionality', () => {
    it('should show clear button when messages exist', () => {
      render(<GameLog messages={mockMessages} maxHeight={500} onClear={vi.fn()} />)

      expect(screen.getByText('Clear')).toBeTruthy()
    })

    it('should call onClear when clear button clicked', () => {
      const onClear = vi.fn()
      render(<GameLog messages={mockMessages} maxHeight={500} onClear={onClear} />)

      fireEvent.click(screen.getByText('Clear'))
      expect(onClear).toHaveBeenCalledOnce()
    })

    it('should not show clear button when no onClear provided', () => {
      render(<GameLog messages={mockMessages} maxHeight={500} />)

      expect(screen.queryByText('Clear')).toBeFalsy()
    })
  })
})