const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

async function getJSON(path) {
    const res = await fetch(BASE + path)
    if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error || `Request failed: ${res.status}`)
    }
    return res.json()
}

export const fetchStatus = (minutes, seed) =>
    getJSON(`/status?minutes=${minutes}${seed !== '' ? `&seed=${seed}` : ''}`)

export const fetchSections = () => getJSON('/sections')

export const fetchFanGate = (section, minutes, seed) =>
    getJSON(
        `/fan-gate?section=${encodeURIComponent(section)}&minutes=${minutes}${seed !== '' ? `&seed=${seed}` : ''}`
    )

export const fetchTransport = (minutes, postMatch) =>
    getJSON(`/transport?minutes=${minutes}&post_match=${postMatch}`)

export const fetchSustainability = (seed) =>
    getJSON(`/sustainability${seed !== '' ? `?seed=${seed}` : ''}`)

export const fetchPois = (category) =>
    getJSON(`/pois${category ? `?category=${encodeURIComponent(category)}` : ''}`)

export const fetchNavigation = (start, destination) =>
    getJSON(`/navigate?start=${encodeURIComponent(start)}&destination=${encodeURIComponent(destination)}`)

export async function fetchAccessibilityAnswer(question) {
    const res = await fetch(BASE + '/accessibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
    })
    if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error || `Request failed: ${res.status}`)
    }
    return res.json()
}