import { useState } from 'react'
import Ticker from './components/Ticker'
import Chart from './components/Chart'
import NewsFeed from './components/NewsFeed'
import Marquee from './components/Marquee'
import Portfolio from './components/Portfolio'
import AlgoTrader from './components/AlgoTrader'
import BuyScan from './components/BuyScan'
import HotStocks from './components/HotStocks'
import './App.css'

export default function App() {
  const [symbol, setSymbol] = useState('AAPL')
  const [compareSymbols, setCompareSymbols] = useState([])
  const [input, setInput] = useState('')
  const [compareInput, setCompareInput] = useState('')

  const search = () => {
    if (input.trim()) {
      setSymbol(input.trim().toUpperCase())
      setCompareSymbols([])
      setInput('')
    }
  }

  const addCompare = () => {
    const s = compareInput.trim().toUpperCase()
    if (s && !compareSymbols.includes(s) && compareSymbols.length < 3) {
      setCompareSymbols(p => [...p, s])
      setCompareInput('')
    }
  }

  const allSymbols = [symbol, ...compareSymbols]

  return (
    <div className="terminal">
      <header className="header">
        <span className="logo">◼ TERMINAL</span>
        <div className="search">
          <input value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
            placeholder="股票代號 (e.g. TSLA)" />
          <button onClick={search}>GO</button>
        </div>
        <div className="search" style={{ marginLeft: 16 }}>
          <input value={compareInput} onChange={e => setCompareInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addCompare()}
            placeholder="對比 (e.g. MSFT)" />
          <button onClick={addCompare} style={{ background: '#333', color: '#e0e0e0' }}>+對比</button>
          {compareSymbols.map(s => (
            <span key={s} style={{ background: '#222', color: '#00aaff', padding: '4px 8px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
              {s}
              <span onClick={() => setCompareSymbols(p => p.filter(x => x !== s))}
                style={{ cursor: 'pointer', color: '#555' }}>✕</span>
            </span>
          ))}
        </div>
      </header>
      <Marquee />
      <div className="main">
        <div className="sidebar">
          <Ticker symbol={symbol} />
          <Portfolio onSelect={setSymbol} activeSymbol={symbol} />
          <BuyScan onSelect={setSymbol} />
          <HotStocks onSelect={setSymbol} />
        </div>
        <div className="content">
          <Chart symbols={allSymbols} />
          <NewsFeed symbol={symbol} />
          <AlgoTrader />
        </div>
      </div>
    </div>
  )
}
