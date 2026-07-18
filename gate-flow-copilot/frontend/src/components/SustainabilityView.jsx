import { useEffect, useState } from 'react'
import { fetchSustainability } from '../api.js'

export default function SustainabilityView() {
    const [data, setData] = useState(null)

    useEffect(() => {
        fetchSustainability('').then(setData)
    }, [])

    return (
        <section className="view">
            <div className="card">
                <h2>Sustainability tracker</h2>
                {data ? (
                    <>
                        <table>
                            <thead><tr><th>Zone</th><th>Bin</th><th>Fill</th></tr></thead>
                            <tbody>
                                {data.bins.map((b, i) => (
                                    <tr key={i}>
                                        <td>{b.zone}</td>
                                        <td>{b.type}</td>
                                        <td>
                                            <span className={`status-badge ${b.fill > 80 ? 'High' : b.fill > 50 ? 'Moderate' : 'Low'}`}>
                                                {b.fill.toFixed(0)}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        <div className="rec-text" style={{ marginTop: '1rem' }}>{data.tip}</div>
                    </>
                ) : (
                    <div style={{ color: 'var(--muted)' }}>Loading…</div>
                )}
            </div>
        </section>
    )
}