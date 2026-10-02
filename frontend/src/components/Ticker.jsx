import { API_URL } from '../api'
import { useEffect, useState } from 'react'
import axios from 'axios'

const SIGNAL_COLOR = { BUY: '#00ff88', SELL: '#ff4444', HOLD: '#ffaa00', WAIT: '#555', ERROR: '#555' }
const SIGNAL_BG = { BUY: '#002211', SELL: '#220011', HOLD: '#221100', WAIT: '#111', ERROR: '#111' }

export default function Ticker({ symbol }) {
  const [data, setData] = useState(null)
  const [signal, setSignal] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setSignal(null)
    Promise.all([
      axios.get(`${API_URL}/stocks/${symbol}`),
      axios.get(`${API_URL}/stocks/${symbol}/signal`),
    ])
      .then(([q, s]) => { setData(q.data); setSignal(s.data) })
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [symbol])

  return (
    <div style={{ background: '#111', padding: 20, borderRight: '1px solid #222' }}>
      {loading ? (
        <div style={{ color: '#555' }}>載入中...</div>
      ) : !data ? (
        <div style={{ color: '#ff4444' }}>找不到 {symbol}</div>
      ) : (
        <>
          <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff6600' }}>{data.symbol}</div>
          <div style={{ fontSize: 36, fontWeight: 'bold', marginTop: 8 }}>${data.price?.toFixed(2)}</div>
          <div style={{ color: data.change >= 0 ? '#00ff88' : '#ff4444', fontSize: 18, marginTop: 4 }}>
            {data.change >= 0 ? '▲' : '▼'} {Math.abs(data.change)?.toFixed(2)} ({data.change_pct?.toFixed(2)}%)
          </div>

          {signal && (
            <div style={{ marginTop: 16, background: SIGNAL_BG[signal.signal], border: `1px solid ${SIGNAL_COLOR[signal.signal]}`, padding: 12, borderRadius: 2 }}>
              <div style={{ color: SIGNAL_COLOR[signal.signal], fontWeight: 'bold', fontSize: 20, letterSpacing: 2 }}>
                {signal.signal === 'BUY' ? '▲ 建議買入' : signal.signal === 'SELL' ? '▼ 建議賣出' : '● 持有觀望'}
              </div>
              <div style={{ marginTop: 8, fontSize: 11, color: '#888' }}>
                <div>MA5: {signal.ma5} / MA20: {signal.ma20}</div>
                <div>RSI: {signal.rsi}</div>
                <div style={{ marginTop: 6 }}>
                  {signal.reasons?.map((r, i) => (
                    <div key={i} style={{ color: r.includes('✓') ? '#00aa55' : r.includes('✗') ? '#aa3333' : '#666' }}>{r}</div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
