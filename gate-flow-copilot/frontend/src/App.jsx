import { useEffect, useRef, useState } from 'react'
import VolunteerView from './components/VolunteerView.jsx'
import FanLookup from './components/FanLookup.jsx'
import TransportView from './components/TransportView.jsx'
import SustainabilityView from './components/SustainabilityView.jsx'
import NavigationView from './components/NavigationView.jsx'
import AccessibilityView from './components/AccessibilityView.jsx'

const TABS = [
    { id: 'volunteer', label: 'Volunteer View' },
    { id: 'fan', label: 'Fan Gate Lookup' },
    { id: 'navigation', label: 'Navigation' },
    { id: 'accessibility', label: 'Accessibility' },
    { id: 'transport', label: 'Transport Assistant' },
    { id: 'sustainability', label: 'Sustainability' },
]

export default function App() {
    const [activeTab, setActiveTab] = useState('volunteer')
    const [highContrast, setHighContrast] = useState(false)
    const tabRefs = useRef({})

    useEffect(() => {
        document.body.classList.toggle('high-contrast', highContrast)
    }, [highContrast])

    // Arrow-key navigation between tabs, per the WAI-ARIA tabs pattern,
    // so keyboard-only and screen-reader users aren't limited to Tab+Enter.
    function handleTabKeyDown(event, index) {
        let nextIndex = null
        if (event.key === 'ArrowRight') nextIndex = (index + 1) % TABS.length
        if (event.key === 'ArrowLeft') nextIndex = (index - 1 + TABS.length) % TABS.length
        if (event.key === 'Home') nextIndex = 0
        if (event.key === 'End') nextIndex = TABS.length - 1
        if (nextIndex !== null) {
            event.preventDefault()
            const nextTab = TABS[nextIndex]
            setActiveTab(nextTab.id)
            tabRefs.current[nextTab.id]?.focus()
        }
    }

    return (
        <main>
            <a className="skip-link" href="#main-panel">Skip to main content</a>

            <div className="hero">
                <div>
                    <h1 className="hero-title">Gate-Flow Co-Pilot</h1>
                    <div className="hero-sub">MetLife Stadium, East Rutherford, New Jersey</div>
                </div>
                <div className="hero-actions">
                    <button
                        type="button"
                        className="a11y-toggle"
                        aria-pressed={highContrast}
                        onClick={() => setHighContrast(v => !v)}
                    >
                        {highContrast ? 'Standard contrast' : 'High contrast'}
                    </button>
                    <div className="live-pill"><span className="live-dot" aria-hidden="true" />Live simulation</div>
                </div>
            </div>

            <div className="tabs" role="tablist" aria-label="Gate-Flow Co-Pilot views">
                {TABS.map((tab, index) => (
                    <button
                        key={tab.id}
                        ref={el => { tabRefs.current[tab.id] = el }}
                        id={`tab-${tab.id}`}
                        role="tab"
                        aria-selected={activeTab === tab.id}
                        aria-controls="main-panel"
                        tabIndex={activeTab === tab.id ? 0 : -1}
                        className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                        onKeyDown={e => handleTabKeyDown(e, index)}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            <div
                id="main-panel"
                role="tabpanel"
                aria-labelledby={`tab-${activeTab}`}
                tabIndex={0}
            >
                {activeTab === 'volunteer' && <VolunteerView />}
                {activeTab === 'fan' && <FanLookup />}
                {activeTab === 'navigation' && <NavigationView />}
                {activeTab === 'accessibility' && <AccessibilityView />}
                {activeTab === 'transport' && <TransportView />}
                {activeTab === 'sustainability' && <SustainabilityView />}
            </div>

            <footer>Simulated crowd data · built for PromptWars Challenge 4</footer>
        </main>
    )
}
