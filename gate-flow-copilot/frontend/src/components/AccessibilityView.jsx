import { useState } from 'react'
import { fetchAccessibilityAnswer } from '../api.js'

const QUICK_TOPICS = [
    'Do you have wheelchair accessible seating?',
    'Is there a quiet sensory room?',
    'Are service animals allowed?',
    'Where is accessible parking?',
]

export default function AccessibilityView() {
    const [question, setQuestion] = useState('')
    const [answer, setAnswer] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    async function ask(q) {
        const trimmed = q.trim()
        if (!trimmed) return
        setLoading(true)
        setError(null)
        try {
            setAnswer(await fetchAccessibilityAnswer(trimmed))
        } catch (err) {
            setError(err.message)
            setAnswer(null)
        } finally {
            setLoading(false)
        }
    }

    return (
        <section className="view">
            <div className="card">
                <h2>Accessibility assistant</h2>
                <p style={{ color: 'var(--muted)' }}>
                    Ask about mobility access, sensory support, hearing assistance,
                    service animals, companion seating, or accessible parking.
                </p>

                <div className="fan-form">
                    <label className="field-label" htmlFor="a11y-question">
                        Your question
                        <input
                            id="a11y-question"
                            type="text"
                            value={question}
                            onChange={e => setQuestion(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && ask(question)}
                            placeholder="e.g. Is there wheelchair access at Gate C?"
                            maxLength={300}
                        />
                    </label>
                    <button className="primary" onClick={() => ask(question)} disabled={loading || !question.trim()}>
                        {loading ? 'Asking…' : 'Ask'}
                    </button>
                </div>

                <div className="quick-topics" role="group" aria-label="Common accessibility questions">
                    {QUICK_TOPICS.map(topic => (
                        <button
                            key={topic}
                            type="button"
                            className="chip"
                            onClick={() => { setQuestion(topic); ask(topic) }}
                        >
                            {topic}
                        </button>
                    ))}
                </div>

                <div aria-live="polite">
                    {error && <div className="fan-result" style={{ color: 'var(--high)' }}>{error}</div>}
                    {answer && (
                        <div className="fan-result">
                            <div className="fan-reason">{answer.answer}</div>
                        </div>
                    )}
                </div>
            </div>
        </section>
    )
}
