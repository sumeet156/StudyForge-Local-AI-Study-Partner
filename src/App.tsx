import { type FormEvent, useEffect, useState } from 'react'

type StudyResponse = {
  explanation: string
  example: string
  question: string
  answer: string
  sources: string[]
}

type ServiceStatus = {
  available: boolean
  model: string
}

function isStudyResponse(value: unknown): value is StudyResponse {
  if (typeof value !== 'object' || value === null) return false
  const response = value as Record<string, unknown>
  return (
    typeof response.explanation === 'string' &&
    typeof response.example === 'string' &&
    typeof response.question === 'string' &&
    typeof response.answer === 'string' &&
    Array.isArray(response.sources) &&
    response.sources.every((source) => typeof source === 'string')
  )
}

function getErrorDetail(value: unknown): string | undefined {
  if (typeof value !== 'object' || value === null || !('detail' in value)) return undefined
  return typeof value.detail === 'string' ? value.detail : undefined
}

const sampleNotes =
  'Photosynthesis is the process by which green plants convert light energy into chemical energy. Chlorophyll in the chloroplasts absorbs sunlight. During the light-dependent reactions, water molecules are split, releasing oxygen and producing ATP and NADPH. In the Calvin cycle, carbon dioxide is fixed into glucose using ATP and NADPH. The overall equation is 6CO2 + 6H2O + light energy → C6H12O6 + 6O2.'

function App() {
  const [notes, setNotes] = useState('')
  const [topic, setTopic] = useState('')
  const [result, setResult] = useState<StudyResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [answerVisible, setAnswerVisible] = useState(false)
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null)

  useEffect(() => {
    let active = true
    fetch('/api/health')
      .then(async (response) => {
        if (!response.ok) throw new Error('StudyForge API is not responding.')
        return (await response.json()) as ServiceStatus
      })
      .then((status) => {
        if (active) setServiceStatus(status)
      })
      .catch(() => {
        if (active) setServiceStatus({ available: false, model: '' })
      })

    return () => {
      active = false
    }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setResult(null)
    setAnswerVisible(false)
    setLoading(true)

    try {
      const response = await fetch('/api/study', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes, topic }),
      })
      const data: unknown = await response.json()

      if (!response.ok) {
        throw new Error(getErrorDetail(data) ?? 'StudyForge could not make a study guide.')
      }

      if (!isStudyResponse(data)) {
        throw new Error('StudyForge received an incomplete study guide. Please try again.')
      }

      setResult(data)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Something went wrong. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  const isReady = serviceStatus?.available === true

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="StudyForge home">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M16 4.5 27 10.7v10.6L16 27.5 5 21.3V10.7L16 4.5Z" />
              <path d="m11 17 3.2 3.2L21.5 13" />
            </svg>
          </span>
          <span>studyforge</span>
        </a>
        <div className={`privacy-badge ${isReady ? 'is-ready' : ''}`}>
          <span className="status-dot" />
          {serviceStatus === null
            ? 'Checking local AI'
            : isReady
              ? 'Private · running locally'
              : 'Local AI not connected'}
        </div>
      </header>

      <main className="main-content">
        <section className="intro">
          <div className="eyebrow">
            <span className="sparkle" aria-hidden="true">✳</span>
            A study partner that starts with your notes
          </div>
          <h1>Let’s make the<br /><span>confusing part click.</span></h1>
          <p className="intro-copy">
            Bring the notes. Tell StudyForge what feels fuzzy. We’ll work through it together.
          </p>
        </section>

        <div className="workspace">
          <form className="study-form" onSubmit={handleSubmit}>
            <div className="form-heading">
              <div>
                <span className="step-label">YOUR STUDY SPACE</span>
                <h2>What are you working on?</h2>
              </div>
              <span className="local-tag"><span aria-hidden="true">◉</span> stays on this device</span>
            </div>

            <label className="field-label" htmlFor="topic">The bit you want to understand</label>
            <input
              id="topic"
              className="topic-input"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="e.g. How does the Calvin cycle make glucose?"
              maxLength={200}
              required
            />

            <div className="notes-label-row">
              <label className="field-label" htmlFor="notes">Your notes</label>
              <button className="text-button" type="button" onClick={() => setNotes(sampleNotes)}>
                Try sample notes <span aria-hidden="true">↗</span>
              </button>
            </div>
            <textarea
              id="notes"
              className="notes-input"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Paste your class notes here. StudyForge will use these as its source."
              maxLength={30000}
              required
              rows={8}
            />
            <div className="form-footer">
              <span className="character-count">{notes.length.toLocaleString()} / 30,000</span>
              <button className="submit-button" type="submit" disabled={loading || !notes.trim() || !topic.trim()}>
                {loading ? (
                  <>
                    <span className="spinner" aria-hidden="true" /> Thinking it through
                  </>
                ) : (
                  <>
                    Help me understand <span aria-hidden="true">↗</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {error && (
            <div className="error-panel" role="alert">
              <span aria-hidden="true">!</span>
              <div>
                <strong>We couldn’t make your study guide.</strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          {result && (
            <section className="guide-card" aria-live="polite">
              <div className="guide-header">
                <div className="guide-icon" aria-hidden="true">✳</div>
                <div>
                  <span className="step-label">YOUR STUDY GUIDE</span>
                  <h2>Let’s break it down.</h2>
                </div>
                <span className="grounded-label"><span aria-hidden="true">✓</span> Based on your notes</span>
              </div>
              <div className="guide-section">
                <span className="section-number">01</span>
                <div>
                  <h3>The simple version</h3>
                  <p>{result.explanation}</p>
                </div>
              </div>
              <div className="guide-section example-section">
                <span className="section-number">02</span>
                <div>
                  <h3>Picture it this way</h3>
                  <p>{result.example}</p>
                </div>
              </div>
              <div className="quiz-section">
                <div className="quiz-heading">
                  <span className="quiz-icon" aria-hidden="true">?</span>
                  <div>
                    <span className="step-label">QUICK CHECK</span>
                    <h3>Your turn to try</h3>
                  </div>
                </div>
                <p className="quiz-question">{result.question}</p>
                {answerVisible ? (
                  <p className="quiz-answer"><strong>One possible answer:</strong> {result.answer}</p>
                ) : (
                  <button className="text-button reveal-button" onClick={() => setAnswerVisible(true)}>
                    Reveal a sample answer <span aria-hidden="true">↓</span>
                  </button>
                )}
              </div>
              <details className="sources">
                <summary>See the notes behind this guide ({result.sources.length})</summary>
                <ol>
                  {result.sources.map((source, index) => <li key={`${index}-${source}`}>{source}</li>)}
                </ol>
              </details>
            </section>
          )}
        </div>
        <p className="reassurance">
          <span aria-hidden="true">✳</span> No accounts. No cloud AI. Just you and your notes.
        </p>
      </main>
      <footer className="footer">
        <span>Made for the moments when class moved a little too fast.</span>
        <span className="footer-model">
          {isReady ? `Local model · ${serviceStatus.model}` : 'Open-source AI · your device'}
        </span>
      </footer>
    </div>
  )
}

export default App
