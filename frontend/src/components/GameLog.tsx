import React, { useRef, useEffect, useState } from 'react'
import type { LogMessage } from '../store/gameStore'

interface GameLogProps {
  messages: LogMessage[]
  maxHeight: number
  onClear?: () => void
}

export const GameLog: React.FC<GameLogProps> = ({ messages, maxHeight, onClear }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  // Auto-scroll to bottom when new messages arrive (if enabled)
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages, autoScroll])

  const handleScroll = () => {
    if (!containerRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 10

    // Only disable autoscroll if user scrolled up (not at bottom)
    if (!isAtBottom) {
      setAutoScroll(false)
    }
  }

  const enableAutoScroll = () => {
    setAutoScroll(true)
    // Immediately scroll to bottom
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }

  const formatTime = (date: Date) => {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    return `${hours}:${minutes}:${seconds}`
  }

  const getMessageStyle = (type: LogMessage['type']) => {
    const baseStyle = {
      padding: '4px 8px',
      marginBottom: '2px',
      borderRadius: '3px',
      fontSize: '13px',
      wordWrap: 'break-word' as const,
      display: 'flex',
      gap: '8px'
    }

    const colors = {
      info: { backgroundColor: 'transparent', color: '#9ca3af' },
      success: { backgroundColor: 'transparent', color: '#7c3aed' },
      warning: { backgroundColor: 'transparent', color: '#f59e0b' },
      error: { backgroundColor: 'transparent', color: '#dc2626' },
      collision: { backgroundColor: 'transparent', color: '#ea580c' }
    }

    return { ...baseStyle, ...colors[type] }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Game Log</h3>
        <div style={styles.buttons}>
          {!autoScroll && (
            <button style={styles.clearButton} onClick={enableAutoScroll}>
              Auto ↓
            </button>
          )}
          {onClear && messages.length > 0 && (
            <button style={styles.clearButton} onClick={onClear}>
              Clear
            </button>
          )}
        </div>
      </div>

      <div
        ref={containerRef}
        data-testid="log-container"
        style={{ ...styles.logContainer, maxHeight }}
        onScroll={handleScroll}
      >
        {messages.length === 0 ? (
          <div style={styles.emptyState}>No messages yet</div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              data-type={msg.type}
              style={getMessageStyle(msg.type)}
            >
              <span style={styles.timestamp}>{formatTime(msg.timestamp)}</span>
              <span style={styles.message}>{msg.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

const styles = {
  container: {
    width: '100%',
    height: '100%',
    backgroundColor: '#0f0f14',
    borderRight: '1px solid #1a1a1f',
    display: 'flex',
    flexDirection: 'column' as const
  },
  header: {
    padding: '10px',
    borderBottom: '1px solid #1a1a1f',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  title: {
    margin: 0,
    fontSize: '14px',
    fontWeight: 'normal' as const,
    color: '#e4e4e7'
  },
  buttons: {
    display: 'flex',
    gap: '5px'
  },
  clearButton: {
    padding: '4px 8px',
    fontSize: '11px',
    backgroundColor: '#1a1a1f',
    border: '1px solid #2a2a35',
    borderRadius: '3px',
    cursor: 'pointer',
    color: '#9ca3af',
    transition: 'all 0.15s'
  },
  logContainer: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '8px',
    fontFamily: 'monospace'
  },
  emptyState: {
    textAlign: 'center' as const,
    color: '#6b7280',
    padding: '20px',
    fontSize: '12px'
  },
  timestamp: {
    fontSize: '10px',
    opacity: 0.5,
    flexShrink: 0,
    color: '#6b7280'
  },
  message: {
    flex: 1
  }
}