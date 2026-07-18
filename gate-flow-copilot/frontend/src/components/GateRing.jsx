import { useState } from 'react'

const STATUS_COLOR = { High: 'var(--high)', Moderate: 'var(--moderate)', Low: 'var(--low)' }

export default function GateRing({ gates }) {
    const cx = 180, cy = 180, ringR = 120, dotR = 26
    const n = gates.length
    const [hoveredGate, setHoveredGate] = useState(null)

    return (
        <div className="ring-wrap">
            <svg width="360" height="360" viewBox="0 0 360 360">
                <defs>
                    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="6" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>

                {/* Outer Ring path representing stadium bowl outer perimeter */}
                <circle cx={cx} cy={cy} r={ringR} fill="none" stroke="var(--border)" strokeWidth="14" />
                
                {/* Stadium Center pitch / arena boundary */}
                <circle cx={cx} cy={cy} r="70" fill="var(--panel-raised)" stroke="var(--border)" />
                
                {/* Dynamic center text showing details on hover */}
                {hoveredGate ? (
                    <>
                        <text x={cx} y={cy - 12} textAnchor="middle" className="gate-label" style={{ fontSize: 13, fontWeight: 700, fill: STATUS_COLOR[hoveredGate.status] }}>
                            {hoveredGate.name.toUpperCase()}
                        </text>
                        <text x={cx} y={cy + 8} textAnchor="middle" className="gate-pct" style={{ fontSize: 16, fontWeight: 700, fill: 'var(--text)' }}>
                            {hoveredGate.density.toFixed(1)}%
                        </text>
                        <text x={cx} y={cy + 24} textAnchor="middle" className="gate-pct" style={{ fontSize: 9, fill: 'var(--muted)', letterSpacing: '0.05em' }}>
                            {hoveredGate.status.toUpperCase()}
                        </text>
                    </>
                ) : (
                    <>
                        <text x={cx} y={cy - 5} textAnchor="middle" className="gate-label" style={{ fontSize: 11, fontWeight: 600, fill: 'var(--muted)', letterSpacing: '0.1em' }}>
                            METLIFE
                        </text>
                        <text x={cx} y={cy + 12} textAnchor="middle" className="gate-pct" style={{ fontSize: 12, fill: 'var(--text)' }}>
                            PITCH
                        </text>
                    </>
                )}

                {/* Connecting lines from gates to stadium pitch */}
                {gates.map((g, i) => {
                    const angle = (i / n) * 2 * Math.PI - Math.PI / 2
                    const rx = cx + (ringR - 7) * Math.cos(angle)
                    const ry = cy + (ringR - 7) * Math.sin(angle)
                    const px = cx + 70 * Math.cos(angle)
                    const py = cy + 70 * Math.sin(angle)
                    const isHovered = hoveredGate?.name === g.name
                    return (
                        <line 
                            key={`line-${g.name}`}
                            x1={rx} y1={ry} x2={px} y2={py}
                            stroke={isHovered ? STATUS_COLOR[g.status] : 'var(--border)'}
                            strokeWidth={isHovered ? '2' : '1'}
                            strokeDasharray="4,4"
                            style={{ transition: 'all 0.3s ease' }}
                        />
                    )
                })}

                {/* Gate nodes */}
                {gates.map((g, i) => {
                    const angle = (i / n) * 2 * Math.PI - Math.PI / 2
                    const gx = cx + ringR * Math.cos(angle)
                    const gy = cy + ringR * Math.sin(angle)
                    const color = STATUS_COLOR[g.status] || 'var(--muted)'
                    const isHovered = hoveredGate?.name === g.name
                    
                    return (
                        <g 
                            key={g.name} 
                            className="gate-dot"
                            onMouseEnter={() => setHoveredGate(g)}
                            onMouseLeave={() => setHoveredGate(null)}
                        >
                            <circle
                                cx={gx} cy={gy} r={isHovered ? dotR + 5 : dotR}
                                fill={color} 
                                fillOpacity={isHovered ? 0.28 : 0.18} 
                                stroke={color} 
                                strokeWidth={isHovered ? 3 : 2}
                                filter={isHovered ? "url(#glow)" : ""}
                                style={{ transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)' }}
                            />
                            <text x={gx} y={gy - 3} textAnchor="middle" className="gate-label" style={{ fontWeight: 700, pointerEvents: 'none' }}>
                                {g.name.replace('Gate ', '')}
                            </text>
                            <text x={gx} y={gy + 10} textAnchor="middle" className="gate-pct" style={{ pointerEvents: 'none' }}>
                                {g.density.toFixed(0)}%
                            </text>
                        </g>
                    )
                })}
            </svg>
        </div>
    )
}