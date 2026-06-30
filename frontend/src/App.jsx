import { useState, useEffect } from 'react'
import { registerUser, loginUser, ingestUrl, queryKnowledgeBase, getMySources, synthesizeAcrossSources } from './api'
import './index.css'

export default function App() {
  const [token, setToken] = useState(null)
  const [email, setEmail] = useState('')

  if (!token) {
    return <AuthScreen onAuthed={(tok, em) => { setToken(tok); setEmail(em) }} />
  }

  return <Workspace token={token} email={email} onLogout={() => setToken(null)} />
}

function AuthScreen({ onAuthed }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = mode === 'login'
        ? await loginUser(email, password)
        : await registerUser(email, password)
      onAuthed(result.access_token, email)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <span className="dot dot-a" />
            <span className="dot dot-b" />
            <span className="dot dot-c" />
          </div>
          <h1>Klaris</h1>
          <p className="tagline">Ask questions across GitHub, YouTube, and the web — at once.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="At least 6 characters" minLength={6} />
          </label>

          {error && <p className="error-text">{error}</p>}

          <button type="submit" disabled={loading}>
            {loading ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}
          </button>
        </form>

        <button className="link-button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>
          {mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Log in'}
        </button>
      </div>
    </div>
  )
}

function Workspace({ token, email, onLogout }) {
  const [url, setUrl] = useState('')
  const [ingestStatus, setIngestStatus] = useState(null)
  const [ingesting, setIngesting] = useState(false)

  const [sources, setSources] = useState([])
  const [selectedSources, setSelectedSources] = useState([])

  // 'ask' = normal /query (blended search), 'synthesize' = /synthesize (per-source compare)
  const [askMode, setAskMode] = useState('ask')

  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [asking, setAsking] = useState(false)

  async function refreshSources() {
    try {
      const result = await getMySources(token)
      setSources(result)
    } catch (err) {
      // Silent fail here is fine -- sources list is a nice-to-have, not critical
      console.error(err)
    }
  }

  useEffect(() => { refreshSources() }, [])

  async function handleIngest(e) {
    e.preventDefault()
    if (!url.trim()) return
    setIngesting(true)
    setIngestStatus(null)
    try {
      const result = await ingestUrl(token, url)
      setIngestStatus({ ok: true, message: result.message })
      setUrl('')
      await refreshSources() // NEW: refresh the source list so it shows up for synthesis
    } catch (err) {
      setIngestStatus({ ok: false, message: err.message })
    } finally {
      setIngesting(false)
    }
  }

  function toggleSourceSelection(sourceUrl) {
    setSelectedSources((prev) =>
      prev.includes(sourceUrl) ? prev.filter((u) => u !== sourceUrl) : [...prev, sourceUrl]
    )
  }

  async function handleAsk(e) {
    e.preventDefault()
    if (!question.trim()) return
    const q = question
    setQuestion('')
    setMessages((m) => [...m, { role: 'user', text: q, mode: askMode }])
    setAsking(true)
    try {
      if (askMode === 'synthesize') {
        const result = await synthesizeAcrossSources(token, q, selectedSources)
        setMessages((m) => [...m, { role: 'assistant', text: result.answer, sources: result.sources_compared, mode: 'synthesize' }])
      } else {
        const result = await queryKnowledgeBase(token, q)
        setMessages((m) => [...m, { role: 'assistant', text: result.answer, sources: result.sources, mode: 'ask' }])
      }
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', text: err.message }])
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="workspace">
      <header className="topbar">
        <div className="brand-mini">
          <span className="dot dot-a" /><span className="dot dot-b" /><span className="dot dot-c" />
          <strong>Klaris</strong>
        </div>
        <div className="topbar-right">
          <span className="user-email">{email}</span>
          <button className="link-button" onClick={onLogout}>Log out</button>
        </div>
      </header>

      <main className="main-grid">
        <section className="panel ingest-panel">
          <h2>Add a source</h2>
          <p className="panel-hint">Paste a GitHub repo, YouTube video, or any web article.</p>
          <form onSubmit={handleIngest}>
            <input type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://github.com/owner/repo" required />
            <button type="submit" disabled={ingesting}>
              {ingesting ? 'Ingesting… (this can take 30–60s)' : 'Ingest'}
            </button>
          </form>
          {ingestStatus && (
            <p className={ingestStatus.ok ? 'status-ok' : 'error-text'}>{ingestStatus.message}</p>
          )}

          {/* NEW in Phase 4: list of ingested sources, selectable for synthesis */}
          <div className="sources-list">
            <h3>Your sources ({sources.length})</h3>
            {sources.length === 0 && <p className="empty-state-small">Nothing ingested yet.</p>}
            {sources.map((s) => (
              <label key={s.source_url} className="source-row">
                <input
                  type="checkbox"
                  checked={selectedSources.includes(s.source_url)}
                  onChange={() => toggleSourceSelection(s.source_url)}
                  disabled={askMode !== 'synthesize'}
                />
                <span className={`type-badge type-${s.source_type}`}>{s.source_type}</span>
                <span className="source-url-text" title={s.source_url}>{s.source_url}</span>
                <span className="chunk-count">{s.chunk_count}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="panel chat-panel">
          <div className="chat-header-row">
            <h2>Ask Klaris</h2>
            <div className="mode-toggle">
              <button className={askMode === 'ask' ? 'mode-btn active' : 'mode-btn'} onClick={() => setAskMode('ask')}>
                Ask
              </button>
              <button className={askMode === 'synthesize' ? 'mode-btn active' : 'mode-btn'} onClick={() => setAskMode('synthesize')}>
                Compare sources
              </button>
            </div>
          </div>
          {askMode === 'synthesize' && (
            <p className="panel-hint">
              {selectedSources.length === 0
                ? 'No sources checked — comparing across ALL ingested sources.'
                : `Comparing ${selectedSources.length} selected source(s) only.`}
            </p>
          )}

          <div className="chat-log">
            {messages.length === 0 && (
              <p className="empty-state">Ingest a source on the left, then ask a question about it here.</p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`message message-${m.role}`}>
                {m.mode === 'synthesize' && m.role !== 'user' && <span className="synth-badge">Cross-source synthesis</span>}
                <p>{m.text}</p>
                {m.sources && m.sources.length > 0 && (
                  <div className="sources">
                    {m.sources.map((s, j) => (
                      <a key={j} href={s.source_url} target="_blank" rel="noreferrer" className="source-chip">
                        {s.source_type} · {new URL(s.source_url.startsWith('http') ? s.source_url : 'https://' + s.source_url).hostname}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {asking && <p className="thinking">Klaris is thinking…</p>}
          </div>
          <form onSubmit={handleAsk} className="chat-input">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={askMode === 'synthesize' ? 'Ask something that spans multiple sources…' : 'Ask a question about your ingested sources…'}
              required
            />
            <button type="submit" disabled={asking}>Ask</button>
          </form>
        </section>
      </main>
    </div>
  )
}
