import { API_URL } from '../api'
import { useState } from 'react'
import axios from 'axios'

export default function BuyScan({ onSelect }) {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [scanned, setScanned] = useState(false)

  const scan = async () => {
    setLoading(true)
    try {
      const r = await axios.get('${API_URL}/scan/buy')
      setResults(r.data)
      setScanned(true)
    } catch {}
    setLoading(false)
  }

  return (
    <div style={{ background: '#111', borderTop: '1px solid #222', padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <div style={{ color: '#ff6600', fontWeight: 'bold', fontSize: 12 }}>今日建議買入</div>
        <button onClick={scan} disabled={loading} style={{
          background: loading ? '#222' : '#ff6600', border: 'none', color: loading ? '#555' : '#000',
          padding: '3px 12px', cursor: loading ? 'default' : 'pointer', fontFamily: 'inherit', fontSize: 12
        }}>
          {loading ? '掃描中...' : '掃描'}
        </button>
      </div>
      {scanned && results.length === 0 && (
        <div style={{ color: '#555', fontSize: 12 }}>今日無建議買入股票</div>
      )}
      {results.map((s, i) => (
        <div key={i} onClick={() => onSelect(s.symbol)}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '8px 4px', borderBottom: '1px solid #1a1a1a', cursor: 'pointer' }}>
          <span style={{ color: '#ff6600', fontWeight: 'bold', width: 55, fontSize: 13 }}>{s.symbol}</span>
          <span style={{ color: '#e0e0e0', fontSize: 13 }}>${s.price?.toFixed(2)}</span>
          <span style={{ color: '#00ff88', fontSize: 11 }}>RSI {s.rsi}</span>
          <span style={{ background: '#002211', color: '#00ff88', padding: '2px 8px', fontSize: 11, border: '1px solid #00ff88' }}>BUY</span>
        </div>
      ))}
    </div>
  )
}
