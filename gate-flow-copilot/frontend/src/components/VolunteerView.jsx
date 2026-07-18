import { useEffect, useState } from 'react'
import { fetchStatus } from '../api.js'
import GateRing from './GateRing.jsx'

export default function VolunteerView() {
    const [minutes, setMinutes] = useState(30)
    const [seed, setSeed] = useState('')
    const [data, setData] = useState(null)
    const [activeLang, setActiveLang] = useState('English')
    const [error, setError] = useState(null)

    async function load() {
        try {
            const result = await fetchStatus(minutes, seed)
            setData(result)
            setError(null)
            if (!Object.keys(result.translations).includes(activeLang)) {
                setActiveLang(Object.keys(result.translations)[0])
            }
        } catch (err) {
            setError(err.message)
        }
    }

    useEffect(() => {
        load()
        const id = setInterval(load, 6000)
        return () => clearInterval(id)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [minutes, seed])

    return (
        <section className="view">
            <div className="controls">
                <label>
                    Minutes to kickoff
                    <input type="range" min="0" max="120" value={minutes} onChange={e => setMinutes(Number(e.target.value))} />
                    <input
                        type="number" min="0" max="240" value={minutes}
                        onChange={e => setMinutes(Math.max(0, Math.min(240, Number(e.target.value))))}
                    />
                </label>
                <label>
                    Seed
                    <input type="number" placeholder="random" value={seed} onChange={e => setSeed(e.target.value)} />
                </label>
            </div>

            {error && <div className="card" style={{ color: 'var(--high)' }}>{error}</div>}

            {data && (
                <>
                    <GateRing gates={data.gates} />
                    <div className="ring-caption">
                        Live gate congestion around the stadium bowl · {data.minutes_to_kickoff} min to kickoff
                    </div>

                    <div className="card">
                        <h2>Gate detail</h2>
                        <table>
                            <thead><tr><th>Gate</th><th>Zone</th><th>Density</th><th>Status</th></tr></thead>
                            <tbody>
                                {data.gates.map(g => (
                                    <tr key={g.name}>
                                        <td>{g.name}</td>
                                        <td style={{ color: 'var(--muted)' }}>{g.zone}</td>
                                        <td>{g.density.toFixed(1)}%</td>
                                        <td>
                                            <span className={`status-badge ${g.status}`}>{g.status}</span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="card">
                        <h2>AI recommendation</h2>
                        <div className="lang-tabs">
                            {Object.keys(data.translations).map(lang => (
                                <div
                                    key={lang}
                                    className={`lang-tab ${lang === activeLang ? 'active' : ''}`}
                                    onClick={() => setActiveLang(lang)}
                                >
                                    {lang}
                                </div>
                            ))}
                        </div>
                        <div className="rec-text">{data.translations[activeLang]}</div>
                    </div>
                </>
            )}
        </section>
    )
}