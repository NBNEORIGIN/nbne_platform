/* SORTED UX — Team Chat (single panel)
 * Auto-creates General channel, auto-adds all staff.
 * Message grouping, date separators, image/video previews, file attachments.
 */
'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { ensureGeneralChannel, getChannels, getMessages, sendMessage as apiSendMessage, getCurrentUser, getMediaUrl, isImageFile, isVideoFile } from '@/lib/api'

export default function AdminChatPage() {
  const [channel, setChannel] = useState<any>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const currentUser = getCurrentUser()
  const currentUserId = currentUser?.id

  const init = useCallback(async () => {
    setLoading(true)
    setError('')
    const ensureRes = await ensureGeneralChannel()
    const ensuredChannel = ensureRes.data
    const r = await getChannels()
    const chs = r.data || []
    if (chs.length > 0) {
      setChannel(chs[0])
    } else if (ensuredChannel?.id) {
      setChannel(ensuredChannel)
    } else {
      setError(r.error || ensureRes.error || 'Chat is being set up. Please try again in a moment.')
    }
    setLoading(false)
  }, [])

  useEffect(() => { init() }, [init])

  useEffect(() => {
    if (!channel) return
    getMessages(channel.id).then(r => setMessages(r.data || []))
  }, [channel?.id])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  useEffect(() => {
    if (!channel) return
    const interval = setInterval(() => {
      getMessages(channel.id).then(r => { if (r.data) setMessages(r.data) })
    }, 4000)
    return () => clearInterval(interval)
  }, [channel?.id])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if ((!input.trim() && files.length === 0) || !channel) return
    setSending(true)
    const res = await apiSendMessage(channel.id, input.trim(), files.length > 0 ? files : undefined)
    if (res.data) {
      setMessages(prev => [...prev, res.data])
    }
    setInput('')
    setFiles([])
    if (fileInputRef.current) fileInputRef.current.value = ''
    setSending(false)
    inputRef.current?.focus()
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) setFiles(Array.from(e.target.files))
  }

  function removeFile(idx: number) {
    setFiles(prev => prev.filter((_, i) => i !== idx))
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function fmtTime(iso: string) {
    return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }

  function fmtDate(iso: string) {
    const d = new Date(iso)
    const today = new Date()
    const yesterday = new Date(); yesterday.setDate(yesterday.getDate() - 1)
    if (d.toDateString() === today.toDateString()) return 'Today'
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday'
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  }

  function getDateKey(iso: string) { return new Date(iso).toDateString() }

  function renderAttachments(attachments: any[]) {
    if (!attachments || attachments.length === 0) return null
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
        {attachments.map((att: any) => {
          const url = getMediaUrl(att.url)
          const isImg = att.content_type?.startsWith('image/') || isImageFile(att.filename || '')
          const isVid = att.content_type?.startsWith('video/') || isVideoFile(att.filename || '')
          if (isImg) return <a key={att.id} href={url} target="_blank" rel="noopener"><img src={url} alt={att.filename} style={{ maxWidth: 220, maxHeight: 160, borderRadius: 'var(--radius)', objectFit: 'cover' }} /></a>
          if (isVid) return <video key={att.id} src={url} controls style={{ maxWidth: 260, maxHeight: 180, borderRadius: 'var(--radius)' }} />
          return <a key={att.id} href={url} target="_blank" rel="noopener" style={{ fontSize: '0.82rem', color: 'var(--color-primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 }}>📎 {att.filename}</a>
        })}
      </div>
    )
  }

  if (loading) return <div className="empty-state">Loading chat…</div>
  if (error) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div style={{ textAlign: 'center', maxWidth: 400 }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>💬</div>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Team Chat</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>{error}</div>
        <button onClick={() => init()} className="btn btn-primary">Retry</button>
      </div>
    </div>
  )

  let lastDateKey = ''

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 80px)', maxWidth: 800, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0, background: 'var(--color-bg-card, #fff)' }}>
        <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--color-primary-light, #e0e7ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>💬</div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '1rem' }}>Team Chat</div>
          <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>{channel?.member_count || 0} members</div>
        </div>
      </div>

      {/* Messages */}
      <div ref={messagesContainerRef} style={{ flex: 1, overflowY: 'auto', padding: '0.75rem 1rem', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', padding: '3rem 1rem', fontSize: '0.85rem' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>👋</div>
            <div style={{ fontWeight: 600 }}>Welcome to Team Chat</div>
            <div style={{ marginTop: 4 }}>Send the first message to get started.</div>
          </div>
        )}
        {messages.map((msg: any, i: number) => {
          const isYou = msg.sender_id === currentUserId
          const dateKey = getDateKey(msg.created_at)
          const showDate = dateKey !== lastDateKey
          lastDateKey = dateKey

          const prev = i > 0 ? messages[i - 1] : null
          const isGrouped = prev && prev.sender_id === msg.sender_id && !showDate &&
            (new Date(msg.created_at).getTime() - new Date(prev.created_at).getTime()) < 120000

          return (
            <div key={msg.id}>
              {showDate && (
                <div style={{ textAlign: 'center', padding: '0.5rem 0', fontSize: '0.65rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {fmtDate(msg.created_at)}
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: isYou ? 'flex-end' : 'flex-start', marginTop: isGrouped ? 1 : 8 }}>
                <div style={{ maxWidth: '80%', minWidth: 60 }}>
                  {!isYou && !isGrouped && (
                    <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--color-primary)', marginBottom: 2, paddingLeft: 10 }}>{msg.sender_name}</div>
                  )}
                  <div style={{
                    padding: '0.45rem 0.75rem',
                    borderRadius: isYou
                      ? (isGrouped ? '16px 16px 4px 16px' : '16px 16px 4px 16px')
                      : (isGrouped ? '16px 16px 16px 4px' : '16px 16px 16px 4px'),
                    background: isYou ? 'var(--color-primary)' : 'var(--color-bg-card, #f1f5f9)',
                    color: isYou ? '#fff' : 'var(--color-text)',
                    border: isYou ? 'none' : '1px solid var(--color-border)',
                    fontSize: '0.85rem',
                    lineHeight: 1.45,
                    wordBreak: 'break-word' as const,
                  }}>
                    {msg.body && <div>{msg.body}</div>}
                    {renderAttachments(msg.attachments)}
                    <div style={{ fontSize: '0.55rem', color: isYou ? 'rgba(255,255,255,0.55)' : 'var(--color-text-muted)', textAlign: 'right', marginTop: 2 }}>{fmtTime(msg.created_at)}</div>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* File preview */}
      {files.length > 0 && (
        <div style={{ padding: '0.4rem 1rem', borderTop: '1px solid var(--color-border)', display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', background: 'var(--color-bg)', flexShrink: 0 }}>
          {files.map((f, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'var(--color-bg-card, #fff)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '3px 8px', fontSize: '0.75rem' }}>
              {f.type.startsWith('image/') ? '🖼️' : f.type.startsWith('video/') ? '🎬' : '📎'} {f.name.length > 18 ? f.name.slice(0, 15) + '…' : f.name}
              <button type="button" onClick={() => removeFile(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-danger)', fontWeight: 700, fontSize: '0.9rem', lineHeight: 1, padding: 0, marginLeft: 2 }}>×</button>
            </div>
          ))}
        </div>
      )}

      {/* Input bar */}
      <form onSubmit={handleSend} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '0.6rem 1rem', borderTop: '1px solid var(--color-border)', background: 'var(--color-bg-card, #fff)', flexShrink: 0 }}>
        <input type="file" ref={fileInputRef} onChange={handleFileSelect} multiple accept="image/*,video/*,.pdf,.doc,.docx" style={{ display: 'none' }} />
        <button type="button" onClick={() => fileInputRef.current?.click()} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', padding: 4, color: 'var(--color-text-muted)', flexShrink: 0 }} title="Attach files">📎</button>
        <input
          ref={inputRef}
          className="form-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type a message…"
          autoFocus
          style={{ flex: 1, borderRadius: 20, fontSize: '0.9rem' }}
        />
        <button
          type="submit"
          disabled={sending || (!input.trim() && files.length === 0)}
          className="btn btn-primary"
          style={{ borderRadius: '50%', width: 38, height: 38, padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', flexShrink: 0, opacity: (sending || (!input.trim() && files.length === 0)) ? 0.4 : 1 }}
          title="Send"
        >
          {sending ? '…' : '➤'}
        </button>
      </form>
    </div>
  )
}
