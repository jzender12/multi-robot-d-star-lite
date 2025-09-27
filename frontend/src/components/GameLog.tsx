import React, { useRef, useEffect, useState } from 'react'
import type { LogMessage } from '../store/gameStore'

interface GameLogProps {
  messages: LogMessage[]
  maxHeight: number
  onClear?: () => void
}

export const GameLog: React.FC<GameLogProps> = ({ messages, maxHeight, onClear }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  // Auto-scroll to bottom when new messages arrive (if auto-scroll is enabled)
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, autoScroll])

  const handleScroll = () => {
    if (!containerRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 10

    setAutoScroll(isNearBottom)
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
      info: { backgroundColor: '#e3f2fd', color: '#1565c0' },
      success: { backgroundColor: '#e8f5e9', color: '#2e7d32' },
      warning: { backgroundColor: '#fff3e0', color: '#ef6c00' },
      error: { backgroundColor: '#ffebee', color: '#c62828' },
      collision: { backgroundColor: '#fce4ec', color: '#c2185b' }
    }

    return { ...baseStyle, ...colors[type] }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Game Log</h3>
        {onClear && messages.length > 0 && (
          <button style={styles.clearButton} onClick={onClear}>
            Clear
          </button>
        )}
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
        <div ref={bottomRef} />
      </div>

      {!autoScroll && (
        <div style={styles.scrollIndicator}>
          ↓ New messages below
        </div>
      )}
    </div>
  )
}

const styles = {
  container: {
    width: '200px',
    height: '100%',
    backgroundColor: '#f8f8f8',
    borderRight: '1px solid #ddd',
    display: 'flex',
    flexDirection: 'column' as const
  },
  header: {
    padding: '10px',
    borderBottom: '1px solid #ddd',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  title: {
    margin: 0,
    fontSize: '16px',
    fontWeight: 'bold' as const
  },
  clearButton: {
    padding: '4px 8px',
    fontSize: '12px',
    backgroundColor: '#fff',
    border: '1px solid #ccc',
    borderRadius: '3px',
    cursor: 'pointer'
  },
  logContainer: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '8px',
    fontFamily: 'monospace'
  },
  emptyState: {
    textAlign: 'center' as const,
    color: '#999',
    padding: '20px',
    fontSize: '14px'
  },
  timestamp: {
    fontSize: '11px',
    opacity: 0.7,
    flexShrink: 0
  },
  message: {
    flex: 1
  },
  scrollIndicator: {
    padding: '4px',
    textAlign: 'center' as const,
    backgroundColor: '#fff3cd',
    color: '#856404',
    fontSize: '12px',
    borderTop: '1px solid #ddd'
  }
}