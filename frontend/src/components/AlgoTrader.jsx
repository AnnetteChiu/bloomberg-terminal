import { API_URL } from '../api'
import { useState, useEffect } from 'react'
import axios from 'axios'

export default function AlgoTrader() {
  const [account, setAccount] = useState(null)
  const [logs, setLogs] = useState([])
  const [running, setRunning] = useState(false)
  const [symbol, setSymbol] = useState('AAPL')
  const [qty, setQty] = useState(1)

  useEffect(() => {
    const fetch = async () => {
      try {
        const [acc, log] = await Promise.all([
          axios.get(import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/algo/account'),
          axios.get(import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/algo/logs'),
        ])
        setAccount(acc.data)
        setLogs(log.data.logs)
        setRunning(log.data.running)
      } catch {}
    }
    fetch()
    const id = setInterval(fetch, 5000)
    return () => clearInterval(id)
  }, [])

  const start = async () => {
    await axios.post(`${API_URL}/algo/start?symbol=${symbol}&qty=${qty}`)
    setRunning(true)
  }

  const stop = async () => {
    await axios.post(import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/algo/stop')
    setRunning(false)
  }

  return (
    <div style={{ background: '#111', borderTop: '1px solid #222', padding: 16 }}>
      <div style={{ color: '#ff6600', fontWeight: 'bold', marginBottom: 12, fontSize: 12 }}>ALGO TRADING</div>

      {account && (
        <div style={{ display: 'flex', gap: 24, marginBottom: 12, fontSize: 13 }}>
          <span><span style={{ color: '#555' }}>Cash </span><span style={{ color: '#e0e0e0' }}>${parseFloat(account.cash).toLocaleString()}</span></span>
          <span><span style={{ color: '#555' }}>Portfolio </span><span style={{ color: '#e0e0e0' }}>${parseFloat(account.portfolio).toLocaleString()}</span></span>
          <span><span style={{ color: '#555' }}>P&L </span><span style={{ color: account.pnl >= 0 ? '#00ff88' : '#ff4444' }}>{account.pnl >= 0 ? '+' : ''}{parseFloat(account.pnl).toFixed(2)}</span></span>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
        <input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())}
          style={{ background: '#1a1a1a', border: '1px solid #333', color: '#e0e0e0', padding: '4px 8px', width: 80, fontFamily: 'inherit', fontSize: 12 }} />
        <input value={qty} onChange={e => setQty(parseInt(e.target.value) || 1)} type="number" min="1"
          style={{ background: '#1a1a1a', border: '1px solid #333', color: '#e0e0e0', padding: '4px 8px', width: 60, fontFamily: 'inherit', fontSize: 12 }} />
        {!running
          ? <button onClick={start} style={{ background: '#00ff88', border: 'none', color: '#000', padding: '4px 16px', fontWeight: 'bold', cursor: 'pointer', fontFamily: 'inherit' }}>START</button>
          : <button onClick={stop} style={{ background: '#ff4444', border: 'none', color: '#fff', padding: '4px 16px', fontWeight: 'bold', cursor: 'pointer', fontFamily: 'inherit' }}>STOP</button>
        }
        <span style={{ fontSize: 11, color: running ? '#00ff88' : '#555' }}>
          {running ? '● 運行中' : '○ 停止'}
        </span>
      </div>

      <div style={{ maxHeight: 150, overflowY: 'auto', fontSize: 11, fontFamily: 'monospace' }}>
        {logs.map((l, i) => (
          <div key={i} style={{ padding: '2px 0', borderBottom: '1px solid #1a1a1a',
            color: l.msg.includes('BUY') ? '#00ff88' : l.msg.includes('SELL') ? '#ff4444' : l.msg.includes('ERROR') ? '#ff6600' : '#666' }}>
            <span style={{ color: '#444', marginRight: 8 }}>{l.time}</span>{l.msg}
          </div>
        ))}
      </div>
    </div>
  )
}
