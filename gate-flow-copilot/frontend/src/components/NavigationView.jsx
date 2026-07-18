import { useEffect, useState } from 'react'
import { fetchNavigation, fetchPois, fetchSections } from '../api.js'

export default function NavigationView() {
    const [sections, setSections] = useState([])
    const [pois, setPois] = useState([])
    const [start, setStart] = useState('Gate A')
    const [destination, setDestination] = useState('')
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        Promise.all([fetchSections(), fetchPois()]).then(([sectionList, poiList]) => {
            setSections(sectionList)
            setPois(poiList)
            setDestination(sectionList[0] || poiList[0]?.name || '')
        })
    }, [])

    async function handleFindRoute() {
        if (!destination) return
        setLoading(true)
        setError(null)
        try {
            setResult(await fetchNavigation(start, destination))
        } catch (err) {
            setError(err.message)
            setResult(null)
        } finally {
            setLoading(false)
        }
    }

    return (
        <section className="view">
            <div className="card">
                <h2>Get directions</h2>
                <div className="fan-form">
                    <label className="field-label" htmlFor="nav-start">
                        Starting point
                        <input
                            id="nav-start"
                            type="text"
                            value={start}
                            onChange={e => setStart(e.target.value)}
                            placeholder="e.g. Gate A"
                        />
                    </label>

                    <label className="field-label" htmlFor="nav-destination">
                        Destination
                        <select
                            id="nav-destination"
                            value={destination}
                            onChange={e => setDestination(e.target.value)}
                        >
                            <optgroup label="Seating sections">
                                {sections.map(s => <option key={s} value={s}>{s}</option>)}
                            </optgroup>
                            <optgroup label="Points of interest">
                                {pois.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                            </optgroup>
                        </select>
                    </label>

                    <button
                        className="primary"
                        onClick={handleFindRoute}
                        disabled={loading || !destination}
                    >
                        {loading ? 'Finding route…' : 'Get directions'}
                    </button>
                </div>

                <div aria-live="polite">
                    {error && <div className="fan-result" style={{ color: 'var(--high)' }}>{error}</div>}
                    {result && (
                        <div className="fan-result">
                            <div className="fan-gate-name">{result.destination}</div>
                            <div className="fan-reason">{result.directions}</div>
                        </div>
                    )}
                </div>
            </div>

            <div className="card">
                <h2>Points of interest</h2>
                <table>
                    <thead><tr><th>Name</th><th>Category</th><th>Nearest gate</th></tr></thead>
                    <tbody>
                        {pois.map(p => (
                            <tr key={p.name}>
                                <td>{p.name}</td>
                                <td style={{ color: 'var(--muted)' }}>{p.category}</td>
                                <td>{p.nearest_gate}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </section>
    )
}
