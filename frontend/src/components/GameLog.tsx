import React, { useRef, useEffect, useState } from 'react'
import type { LogMessage } from '../store/gameStore'
import styles from './GameLog.module.css'

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

  const getMessageClassName = (type: LogMessage['type']) => {
    const classMap = {
      info: styles.logInfo,
      success: styles.logSuccess,
      warning: styles.logWarning,
      error: styles.logError,
      collision: styles.logCollision
    }
    return `${styles.logEntry} ${classMap[type]}`
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Game Log</h3>
        <div className={styles.buttons}>
          {!autoScroll && (
            <button className={styles.clearButton} onClick={enableAutoScroll}>
              Auto ↓
            </button>
          )}
          {onClear && messages.length > 0 && (
            <button className={styles.clearButton} onClick={onClear}>
              Clear
            </button>
          )}
        </div>
      </div>

      <div
        ref={containerRef}
        data-testid="log-container"
        className={styles.logContainer}
        style={{ maxHeight }}
        onScroll={handleScroll}
      >
        {messages.length === 0 ? (
          <div className={styles.emptyState}>No messages yet</div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              data-type={msg.type}
              className={getMessageClassName(msg.type)}
            >
              <span className={styles.timestamp}>{formatTime(msg.timestamp)}</span>
              <span className={styles.message}>{msg.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}