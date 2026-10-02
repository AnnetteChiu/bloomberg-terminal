import { API_URL } from '../api'
import { useState, useEffect } from 'react'
import axios from 'axios'

export default function Portfolio({ onSelect, activeSymbol }) {
  const [holdings, setHoldings] = useState(
    () => JSON.parse(localStorage.getItem('portfolio') || '[]')
  )
  const [input, setInput] = useState({ symbol: '', shares: '', cost: '' })
  const [prices, setPrices] = useState({})

  useEffect(() => {
    localStorage.setItem('portfolio', JSON.stringify(holdings))
    holdings.forEach(h => {
      axios.get(`${API_URL}/stocks/${h.symbol}`)
        .then(r => setPrices(p => ({ ...p, [h.symbol]: r.data.price })))
        .catch(() => {})
    })
  }, [holdings])

  const add = () => {
    if (!input.symbol.trim()) return
    setHoldings(p => [...p, {
      symbol: input.symbol.trim().toUpperCase(),
      shares: parseFloat(input.shares) || 0,
      cost: parseFloat(input.cost) || 0,
    }])
    setInput({ symbol: '', shares: '', cost: '' })
  }

  const remove = (i) => setHoldings(p => p.filter((_, idx) => idx !== i))

  return (
    <div style={{ padding: 16 }}>
      <div style={{ color: '#ff6600', fontWeight: 'bold', marginBottom: 10, fontSize: 12 }}>PORTFOLIO</div>
      <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
        <input value={input.symbol} onChange={e => setInput(p => ({...p, symbol: e.target.value}))}
          onKeyDown={e => e.key === 'Enter' && add()}
          placeholder="代號" style={iStyle} />
        <input value={input.shares} onChange={e => setInput(p => ({...p, shares: e.target.value}))}
          placeholder="股數" type="number" style={{ ...iStyle, width: 60 }} />
        <input value={input.cost} onChange={e => setInput(p => ({...p, cost: e.target.value}))}
          placeholder="成本" type="number" style={{ ...iStyle, width: 70 }} />
        <button onClick={add} style={bStyle}>+</button>
      </div>
      {holdings.map((h, i) => {
        const price = prices[h.symbol]
        const pnl = price && h.cost ? (price - h.cost) * h.shares : null
        const active = activeSymbol === h.symbol
        return (
          <div key={i} onClick={() => onSelect(h.symbol)}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '6px 4px', borderBottom: '1px solid #1a1a1a', cursor: 'pointer',
              background: active ? '#1a1a1a' : 'transparent' }}>
            <span style={{ color: '#ff6600', width: 50, fontSize: 13 }}>{h.symbol}</span>
            <span style={{ color: '#888', fontSize: 11 }}>{h.shares}股</span>
            <span style={{ color: '#e0e0e0', fontSize: 13 }}>${price?.toFixed(2) ?? '...'}</span>
            <span style={{ color: pnl == null ? '#555' : pnl >= 0 ? '#00ff88' : '#ff4444', fontSize: 11 }}>
              {pnl != null ? `${pnl >= 0 ? '+' : ''}${pnl.toFixed(0)}` : '-'}
            </span>
            <button onClick={e => { e.stopPropagation(); remove(i) }}
              style={{ background: 'none', border: 'none', color: '#444', cursor: 'pointer', fontSize: 12 }}>✕</button>
          </div>
        )
      })}
    </div>
  )
}

const iStyle = { background: '#1a1a1a', border: '1px solid #333', color: '#e0e0e0', padding: '4px 6px', fontFamily: 'inherit', width: 70, fontSize: 12 }
const bStyle = { background: '#ff6600', border: 'none', color: '#000', padding: '4px 10px', fontWeight: 'bold', cursor: 'pointer' }
