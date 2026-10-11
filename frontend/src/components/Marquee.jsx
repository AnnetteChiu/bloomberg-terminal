import { API_URL } from '../api'
import { useEffect, useState, useRef } from 'react'
import axios from 'axios'

const SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX']

export default function Marquee({ market = 'us' }) {
  const [stocks, setStocks] = useState([])

  useEffect(() => {
    const fetch = async () => {
      try {
        const endpoint = market === 'tw' ? `${API_URL}/tw/marquee` : null
        if (endpoint) {
          const r = await axios.get(endpoint)
          setStocks(r.data)
        } else {
          const results = []
          for (const s of SYMBOLS) {
            try {
              const r = await axios.get(`${API_URL}/stocks/${s}`)
              results.push(r.data)
            } catch {}
          }
          setStocks(results)
        }
      } catch {}
    }
    fetch()
    const id = setInterval(fetch, 60000)
    return () => clearInterval(id)
  }, [market])

  const currency = market === 'tw' ? 'NT$' : '$'
  const items = [...stocks, ...stocks]

  return (
    <div style={{ background: '#0d0d0d', borderBottom: '1px solid #1a1a1a', overflow: 'hidden', height: 32 }}>
      <div className="marquee-track">
        {items.map((s, i) => (
          <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, marginRight: 40 }}>
            <span style={{ color: '#ff6600', fontWeight: 'bold', fontSize: 13 }}>{s.symbol?.replace('.TW','')}</span>
            <span style={{ color: '#e0e0e0', fontSize: 13 }}>{currency}{s.price?.toFixed(2)}</span>
            <span style={{ color: s.change >= 0 ? '#00ff88' : '#ff4444', fontSize: 12 }}>
              {s.change >= 0 ? '▲' : '▼'}{Math.abs(s.change_pct)?.toFixed(2)}%
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
