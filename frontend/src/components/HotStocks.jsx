import { API_URL } from '../api'
import { useState } from 'react'
import axios from 'axios'

export default function HotStocks({ onSelect }) {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [scanned, setScanned] = useState(false)

  const scan = async () => {
    setLoading(true)
    try {
      const r = await axios.get('${API_URL}/scan/hot')
      setResults(r.data)
      setScanned(true)
    } catch {}
    setLoading(false)
  }

  return (
    <div style={{ background: '#111', borderTop: '1px solid #222', padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <div style={{ color: '#ff6600', fontWeight: 'bold', fontSize: 12 }}>🔥 市場熱門</div>
        <button onClick={scan} disabled={loading} style={{
          background: loading ? '#222' : '#333', border: '1px solid #555',
          color: loading ? '#555' : '#e0e0e0',
          padding: '3px 12px', cursor: loading ? 'default' : 'pointer', fontFamily: 'inherit', fontSize: 12
        }}>
          {loading ? '分析中...' : '分析'}
        </button>
      </div>

      {scanned && results.length === 0 && (
        <div style={{ color: '#555', fontSize: 12 }}>無資料</div>
      )}

      {results.map((s, i) => (
        <div key={i} onClick={() => onSelect(s.symbol)}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '7px 4px', borderBottom: '1px solid #1a1a1a', cursor: 'pointer' }}>
          <span style={{ color: i < 3 ? '#ff6600' : '#aaa', fontWeight: 'bold', width: 50, fontSize: 13 }}>
            {i < 3 ? '🔥' : `#${i+1}`} {s.symbol}
          </span>
          <span style={{ color: '#e0e0e0', fontSize: 12 }}>${s.price?.toFixed(2)}</span>
          <span style={{ color: s.price_change >= 0 ? '#00ff88' : '#ff4444', fontSize: 11 }}>
            {s.price_change >= 0 ? '+' : ''}{s.price_change}%
          </span>
          <span style={{ color: '#888', fontSize: 11 }}>量比{s.vol_ratio}x</span>
          <span style={{ color: '#ff6600', fontSize: 11 }}>分{s.score}</span>
        </div>
      ))}
    </div>
  )
}
