import { useEffect, useState } from 'react'
import axios from 'axios'

export default function ForexBar() {
  const [rates, setRates] = useState([])

  useEffect(() => {
    axios.get('http://localhost:8000/forex/').then(r => setRates(r.data)).catch(() => {})
  }, [])

  return (
    <div style={{ background: '#0d0d0d', borderBottom: '1px solid #222', padding: '5px 20px', display: 'flex', gap: 24 }}>
      {rates.map(r => (
        <span key={r.pair} style={{ fontSize: 12 }}>
          <span style={{ color: '#555' }}>{r.pair} </span>
          <span style={{ color: '#e0e0e0' }}>{r.rate.toFixed(4)}</span>
        </span>
      ))}
      {rates.length === 0 && <span style={{ color: '#333', fontSize: 12 }}>FX 載入中...</span>}
    </div>
  )
}
