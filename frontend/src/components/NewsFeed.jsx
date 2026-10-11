import { API_URL } from '../api'
import { useEffect, useState } from 'react'
import axios from 'axios'

export default function NewsFeed({ symbol, market = 'us' }) {
  const [news, setNews] = useState([])

  useEffect(() => {
    const base = market === 'tw' ? `${API_URL}/tw/news` : `${API_URL}/news`
    axios.get(`${base}/${symbol}`)
      .then(r => setNews(r.data))
      .catch(() => setNews([]))
  }, [symbol, market])

  return (
    <div style={{ background: '#111', borderTop: '1px solid #222', padding: 16,
      gridColumn: '1 / -1', overflowY: 'auto', maxHeight: 200 }}>
      <div style={{ color: '#ff6600', fontWeight: 'bold', marginBottom: 10 }}>NEWS — {symbol}</div>
      {news.map((n, i) => (
        <div key={i} style={{ borderBottom: '1px solid #1a1a1a', padding: '8px 0' }}>
          <a href={n.url} target="_blank" rel="noreferrer"
            style={{ color: '#e0e0e0', textDecoration: 'none', fontSize: 13 }}>
            {n.title}
          </a>
          <div style={{ color: '#555', fontSize: 11, marginTop: 4 }}>{n.published}</div>
        </div>
      ))}
    </div>
  )
}
