import { useState } from 'react'
import { fetchTransport } from '../api.js'

export default function TransportView() {
    const [minutes, setMinutes] = useState(30)
    const [postMatch, setPostMatch] = useState(false)
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    async function handleCheck() {
        setLoading(true)
        try {
            setResult(await fetchTransport(minutes, postMatch))
        } finally {
            setLoading(false)
        }
    }

    return (
        <section className="view">
            <div className="card">
                <h2>Transportation assistant</h2>
                <div className="controls">
                    <label>
                        <input type="checkbox" checked={postMatch} onChange={e => setPostMatch(e.target.checked)} />
                        Leaving after the match
                    </label>
                    {!postMatch && (
                        <label>
                            Minutes to kickoff
                            <input type="number" min="0" max="240" value={minutes} onChange={e => setMinutes(Number(e.target.value))} />
                        </label>
                    )}
                    <button className="primary" onClick={handleCheck} disabled={loading}>
                        {loading ? 'Checking…' : 'Get recommendation'}
                    </button>
                </div>

                {result && (
                    <div className="fan-result">
                        <div className="fan-gate-name">{result.mode}</div>
                        <div className="fan-wait">{result.wait_estimate}</div>
                        <div className="fan-reason">{result.note}</div>
                    </div>
                )}
            </div>
        </section>
    )
}