import { useState } from 'react'
import Ticker from './components/Ticker'
import Chart from './components/Chart'
import NewsFeed from './components/NewsFeed'
import Marquee from './components/Marquee'
import Portfolio from './components/Portfolio'
import AlgoTrader from './components/AlgoTrader'
import BuyScan from './components/BuyScan'
import HotStocks from './components/HotStocks'
import StockScreener from './components/StockScreener'
import './App.css'

const MARKETS = [
  { key: 'us', label: '🇺🇸 美股', default: 'AAPL', placeholder: '股票代號 (e.g. TSLA)' },
  { key: 'tw', label: '🇹🇼 台股', default: '2330', placeholder: '股票代號 (e.g. 2330)' },
]

export default function App() {
  const [market, setMarket] = useState('us')
  const [symbol, setSymbol] = useState('AAPL')
  const [compareSymbols, setCompareSymbols] = useState([])
  const [input, setInput] = useState('')
  const [compareInput, setCompareInput] = useState('')

  const switchMarket = (m) => {
    setMarket(m)
    setCompareSymbols([])
    setInput('')
    setCompareInput('')
    const mkt = MARKETS.find(x => x.key === m)
    setSymbol(mkt.default)
  }

  // 台股代號加 .TW 後綴
  const normalize = (s) => {
    if (market === 'tw') return s.replace(/\.TW$/i, '') + '.TW'
    return s.toUpperCase()
  }

  const search = () => {
    if (input.trim()) {
      setSymbol(normalize(input.trim().toUpperCase()))
      setCompareSymbols([])
      setInput('')
    }
  }

  const addCompare = () => {
    const s = normalize(compareInput.trim().toUpperCase())
    if (s && !compareSymbols.includes(s) && compareSymbols.length < 3) {
      setCompareSymbols(p => [...p, s])
      setCompareInput('')
    }
  }

  const allSymbols = [symbol, ...compareSymbols]
  const mktCfg = MARKETS.find(m => m.key === market)

  return (
    <div className="terminal">
      <header className="header">
        <span className="logo">◼ TERMINAL</span>

        {/* 市場切換 */}
        <div style={{ display: 'flex', gap: 4 }}>
          {MARKETS.map(m => (
            <button key={m.key} onClick={() => switchMarket(m.key)} style={{
              background: market === m.key ? '#ff6600' : '#1a1a1a',
              border: `1px solid ${market === m.key ? '#ff6600' : '#333'}`,
              color: market === m.key ? '#000' : '#888',
              padding: '4px 12px', cursor: 'pointer', fontFamily: 'inherit', fontSize: 12, fontWeight: 'bold',
            }}>{m.label}</button>
          ))}
        </div>

        <div className="search">
          <input value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
            placeholder={mktCfg.placeholder} />
          <button onClick={search}>GO</button>
        </div>
        <div className="search" style={{ marginLeft: 8 }}>
          <input value={compareInput} onChange={e => setCompareInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addCompare()}
            placeholder="對比代號" />
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

      <Marquee market={market} />

      <div className="main">
        <div className="sidebar">
          <Ticker symbol={symbol} market={market} />
          <Portfolio onSelect={setSymbol} activeSymbol={symbol} market={market} />
          <BuyScan onSelect={setSymbol} market={market} />
          <HotStocks onSelect={setSymbol} market={market} />
          <StockScreener onSelect={setSymbol} market={market} />
        </div>
        <div className="content">
          <Chart symbols={allSymbols} market={market} />
          <NewsFeed symbol={symbol} market={market} />
          <AlgoTrader />
        </div>
      </div>
    </div>
  )
}
