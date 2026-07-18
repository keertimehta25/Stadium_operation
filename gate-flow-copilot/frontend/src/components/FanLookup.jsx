import { useEffect, useState } from 'react'
import { fetchFanGate, fetchSections } from '../api.js'

export default function FanLookup() {
    const [sections, setSections] = useState([])
    const [section, setSection] = useState('')
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        fetchSections().then(list => {
            setSections(list)
            setSection(list[0] || '')
        })
    }, [])

    async function handleLookup() {
        if (!section) return
        setLoading(true)
        try {
            setResult(await fetchFanGate(section, 30, ''))
        } catch (err) {
            setResult({ error: err.message })
        } finally {
            setLoading(false)
        }
    }

    return (
        <section className="view">
            <div className="card">
                <h2>Find your gate</h2>
                <div className="fan-form">
                    <select value={section} onChange={e => setSection(e.target.value)}>
                        {sections.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <button className="primary" onClick={handleLookup} disabled={loading || !section}>
                        {loading ? 'Checking…' : 'Find my gate'}
                    </button>
                </div>

                {result && (
                    <div className="fan-result">
                        {result.error ? (
                            <div style={{ color: 'var(--high)' }}>{result.error}</div>
                        ) : (
                            <>
                                <div className="fan-gate-name">{result.gate}</div>
                                <div className="fan-wait">{result.zone} · {result.wait_estimate}</div>
                                <div className="fan-reason">{result.reason}</div>
                            </>
                        )}
                    </div>
                )}
            </div>
        </section>
    )
}