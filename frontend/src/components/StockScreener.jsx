import { API_URL } from '../api'
import { useState } from 'react'
import axios from 'axios'

const MODES = [
  { key: '52week',    label: '52週突破' },
  { key: 'divergence',label: 'RSI背離'  },
  { key: 'sector',    label: '板塊輪動' },
  { key: 'macd',      label: 'MACD交叉' },
  { key: 'bollinger', label: '布林通道' },
  { key: 'volume',    label: '量能暴增' },
  { key: 'drawdown',  label: '回撤反彈' },
]

const TAG = ({ color, bg, border, children }) => (
  <span style={{ background: bg, color, border: `1px solid ${border || color}`, padding: '1px 7px', fontSize: 10 }}>
    {children}
  </span>
)

const BUY_TAG  = ({ label }) => <TAG color="#00ff88" bg="#002211">{label || 'BUY'}</TAG>
const SELL_TAG = ({ label }) => <TAG color="#ff4444" bg="#220011">{label || 'SELL'}</TAG>
const WATCH_TAG = ({ label }) => <TAG color="#ffaa00" bg="#221100">{label || 'WATCH'}</TAG>

function SignalTag({ signal, label }) {
  if (signal === 'BUY')  return <BUY_TAG label={label} />
  if (signal === 'SELL') return <SELL_TAG label={label} />
  return <WATCH_TAG label={label} />
}

function Row({ onClick, children }) {
  return (
    <div onClick={onClick} style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '7px 4px', borderBottom: '1px solid #1a1a1a', cursor: onClick ? 'pointer' : 'default',
    }}>{children}</div>
  )
}

const Sym = ({ s }) => <span style={{ color: '#00aaff', fontWeight: 'bold', width: 55, fontSize: 13 }}>{s}</span>
const Price = ({ p }) => <span style={{ color: '#e0e0e0', fontSize: 12 }}>${p?.toFixed(2)}</span>
const Dim = ({ children }) => <span style={{ color: '#888', fontSize: 11 }}>{children}</span>

export default function StockScreener({ onSelect, market = 'us' }) {
  const [mode, setMode] = useState('macd')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [scanned, setScanned] = useState(false)

  const scan = async () => {
    setLoading(true)
    setResults([])
    try {
      const base = market === 'tw' ? `${API_URL}/tw/scan` : `${API_URL}/scan`
      const r = await axios.get(`${base}/${mode}`)
      setResults(r.data)
      setScanned(true)
    } catch {}
    setLoading(false)
  }

  return (
    <div style={{ background: '#0d0d0d', borderTop: '1px solid #222', padding: 16 }}>
      {/* 標題列 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
        <div style={{ color: '#00aaff', fontWeight: 'bold', fontSize: 12 }}>🔍 選股篩選</div>
        <button onClick={scan} disabled={loading} style={{
          background: loading ? '#222' : '#00aaff', border: 'none',
          color: loading ? '#555' : '#000',
          padding: '3px 12px', cursor: loading ? 'default' : 'pointer',
          fontFamily: 'inherit', fontSize: 12, marginLeft: 'auto',
        }}>
          {loading ? '掃描中...' : '掃描'}
        </button>
      </div>

      {/* 模式選擇 */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
        {MODES.map(m => (
          <button key={m.key} onClick={() => { setMode(m.key); setScanned(false); setResults([]) }}
            style={{
              background: mode === m.key ? '#00aaff' : '#1a1a1a',
              border: `1px solid ${mode === m.key ? '#00aaff' : '#333'}`,
              color: mode === m.key ? '#000' : '#888',
              padding: '2px 8px', cursor: 'pointer', fontFamily: 'inherit', fontSize: 10,
            }}>
            {m.label}
          </button>
        ))}
      </div>

      {scanned && results.length === 0 && (
        <div style={{ color: '#555', fontSize: 12 }}>無符合條件</div>
      )}

      {/* 52週突破 */}
      {mode === '52week' && results.map((s, i) => (
        <Row key={i} onClick={() => onSelect(s.symbol)}>
          <Sym s={s.symbol} />
          <Price p={s.price} />
          <span style={{ color: s.type === '突破新高' ? '#00ff88' : '#ffaa00', fontSize: 11 }}>{s.type}</span>
          <Dim>距高{s.pct_from_high?.toFixed(1)}%</Dim>
        </Row>
      ))}

      {/* RSI背離 */}
      {mode === 'divergence' && results.map((s, i) => (
        <Row key={i} onClick={() => onSelect(s.symbol)}>
          <Sym s={s.symbol} />
          <Price p={s.price} />
          <span style={{ color: s.signal === 'BUY' ? '#00ff88' : '#ff4444', fontSize: 11 }}>{s.type}</span>
          <Dim>RSI {s.rsi}</Dim>
          <SignalTag signal={s.signal} />
        </Row>
      ))}

      {/* 板塊輪動 */}
      {mode === 'sector' && results.map((s, i) => (
        <div key={i} style={{ padding: '8px 4px', borderBottom: '1px solid #1a1a1a' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#00aaff', fontWeight: 'bold', fontSize: 13 }}>
              {['🥇','🥈','🥉'][i] || '  '} {s.sector}
            </span>
            <span style={{ color: s.avg_1w >= 0 ? '#00ff88' : '#ff4444', fontSize: 12 }}>
              週{s.avg_1w >= 0 ? '+' : ''}{s.avg_1w}%
            </span>
            <span style={{ color: s.avg_1m >= 0 ? '#00aa55' : '#aa3333', fontSize: 11 }}>
              月{s.avg_1m >= 0 ? '+' : ''}{s.avg_1m}%
            </span>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            {s.top?.map((t, j) => (
              <span key={j} onClick={() => onSelect(t.symbol)} style={{ color: '#888', fontSize: 10, cursor: 'pointer' }}>
                {t.symbol} <span style={{ color: t.change_1w >= 0 ? '#00aa55' : '#aa3333' }}>
                  {t.change_1w >= 0 ? '+' : ''}{t.change_1w}%
                </span>
              </span>
            ))}
          </div>
        </div>
      ))}

      {/* MACD交叉 */}
      {mode === 'macd' && results.map((s, i) => (
        <Row key={i} onClick={() => onSelect(s.symbol)}>
          <Sym s={s.symbol} />
          <Price p={s.price} />
          <span style={{ color: s.cross === '金叉' ? '#00ff88' : '#ff4444', fontSize: 11 }}>{s.cross}</span>
          <Dim>MACD {s.macd > 0 ? '+' : ''}{s.macd}</Dim>
          <SignalTag signal={s.signal} />
        </Row>
      ))}

      {/* 布林通道 */}
      {mode === 'bollinger' && results.map((s, i) => (
        <Row key={i} onClick={() => onSelect(s.symbol)}>
          <Sym s={s.symbol} />
          <Price p={s.price} />
          <span style={{
            color: s.signal === 'BUY' ? '#00ff88' : s.signal === 'SELL' ? '#ff4444' : '#ffaa00',
            fontSize: 11,
          }}>{s.status}</span>
          <Dim>帶寬{s.bandwidth}%</Dim>
          <SignalTag signal={s.signal} />
        </Row>
      ))}

      {/* 量能暴增 */}
      {mode === 'volume' && results.map((s, i) => (
        <Row key={i} onClick={() => onSelect(s.symbol)}>
          <Sym s={s.symbol} />
          <Price p={s.price} />
          <span style={{ color: s.change_pct >= 0 ? '#00ff88' : '#ff4444', fontSize: 11 }}>
            {s.change_pct >= 0 ? '+' : ''}{s.change_pct}%
          </span>
          <Dim>量比{s.vol_ratio}x</Dim>
          <SignalTag signal={s.signal} />
        </Row>
      ))}

      {/* 回撤反彈 */}
      {mode === 'drawdown' && results.map((s, i) => (
        <Row key={i} onClick={() => onSelect(s.symbol)}>
          <Sym s={s.symbol} />
          <Price p={s.price} />
          <span style={{ color: '#ffaa00', fontSize: 11 }}>回撤{s.from_peak?.toFixed(1)}%</span>
          <Dim>RSI {s.rsi}</Dim>
          <Dim>潛力+{s.recovery_potential?.toFixed(1)}%</Dim>
        </Row>
      ))}
    </div>
  )
}
