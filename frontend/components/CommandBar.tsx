'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { executeCommand, getCommandSuggestions } from '@/lib/api'

export default function CommandBar() {
  const router = useRouter()
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [banner, setBanner] = useState<{ message: string; success: boolean } | null>(null)
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIdx, setSelectedIdx] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const wrapRef = useRef<HTMLDivElement>(null)

  // Dismiss banner after 3s
  useEffect(() => {
    if (!banner) return
    const t = setTimeout(() => setBanner(null), 3000)
    return () => clearTimeout(t)
  }, [banner])

  // Close suggestions on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Fetch suggestions as user types
  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 1) {
      const r = await getCommandSuggestions()
      setSuggestions(r.data || [])
      return
    }
    const r = await getCommandSuggestions(q)
    setSuggestions(r.data || [])
  }, [])

  useEffect(() => {
    if (showSuggestions) {
      fetchSuggestions(text)
      setSelectedIdx(-1)
    }
  }, [text, showSuggestions, fetchSuggestions])

  async function handleSubmit(commandText?: string) {
    const cmd = (commandText || text).trim()
    if (!cmd) return
    setLoading(true)
    setShowSuggestions(false)

    const r = await executeCommand(cmd)
    const data = r.data

    if (data?.success) {
      setBanner({ message: data.message, success: true })
      setText('')
      // Navigate if the command specifies a page
      if (data.navigate) {
        // If it's an API URL (export), open in new tab
        if (data.navigate.startsWith('/api/')) {
          window.open(data.navigate, '_blank')
        } else {
          router.push(data.navigate)
        }
      }
    } else {
      const msg = data?.message || 'Something went wrong'
      const sugg = data?.suggestions
      setBanner({
        message: sugg ? `${msg}. Try: "${sugg[0]}"` : msg,
        success: false,
      })
    }
    setLoading(false)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') {
      if (selectedIdx >= 0 && selectedIdx < suggestions.length) {
        const s = suggestions[selectedIdx]
        setText(s.text)
        handleSubmit(s.text)
      } else {
        handleSubmit()
      }
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIdx(i => Math.min(i + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIdx(i => Math.max(i - 1, -1))
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
    }
  }

  return (
    <div ref={wrapRef} style={{ position: 'relative', width: '100%', maxWidth: 600, margin: '0 auto' }}>
      {/* Input bar */}
      <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            ref={inputRef}
            type="text"
            value={text}
            onChange={e => setText(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={handleKeyDown}
            placeholder='Type anything… e.g. "Jordan is sick", "Show VIP clients"'
            style={{
              width: '100%',
              padding: '0.45rem 0.75rem',
              border: '1px solid var(--color-border)',
              borderRadius: 8,
              fontSize: '0.85rem',
              background: 'var(--color-bg-alt, #f9fafb)',
              outline: 'none',
              transition: 'border-color 0.15s',
            }}
          />
        </div>
        <button
          onClick={() => handleSubmit()}
          disabled={loading || !text.trim()}
          style={{
            padding: '0.45rem 0.9rem',
            borderRadius: 8,
            border: 'none',
            background: 'var(--color-primary, #2563eb)',
            color: '#fff',
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: loading || !text.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !text.trim() ? 0.5 : 1,
            whiteSpace: 'nowrap',
          }}
        >
          {loading ? '…' : 'Go'}
        </button>
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, marginTop: 4,
          background: '#fff', border: '1px solid var(--color-border)', borderRadius: 8,
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 100, maxHeight: 260, overflowY: 'auto',
        }}>
          {suggestions.map((s, i) => (
            <div
              key={i}
              onClick={() => { setText(s.text); handleSubmit(s.text) }}
              onMouseEnter={() => setSelectedIdx(i)}
              style={{
                padding: '0.4rem 0.75rem',
                cursor: 'pointer',
                fontSize: '0.82rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: i === selectedIdx ? '#f0f9ff' : 'transparent',
              }}
            >
              <span>{s.text}</span>
              <span style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', background: '#f3f4f6', padding: '1px 6px', borderRadius: 4 }}>{s.category}</span>
            </div>
          ))}
        </div>
      )}

      {/* Response banner */}
      {banner && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, marginTop: 4,
          padding: '0.5rem 0.75rem', borderRadius: 8, fontSize: '0.82rem', fontWeight: 500,
          background: banner.success ? '#dcfce7' : '#fee2e2',
          color: banner.success ? '#15803d' : '#991b1b',
          border: `1px solid ${banner.success ? '#86efac' : '#fca5a5'}`,
          zIndex: 101,
        }}>
          {banner.message}
        </div>
      )}
    </div>
  )
}
