import { API_URL } from '../api'
import { useEffect, useRef, useState } from 'react'
import { createChart, CandlestickSeries, LineSeries } from 'lightweight-charts'
import axios from 'axios'

export default function Chart({ symbols = ['AAPL'] }) {
  const candleRef = useRef()
  const rsiRef = useRef()
  const chartRef = useRef()
  const rsiChartRef = useRef()
  const seriesMap = useRef({})
  const [period, setPeriod] = useState('1mo')
  const [showMA, setShowMA] = useState(true)

  useEffect(() => {
    if (!candleRef.current || !rsiRef.current) return
    if (chartRef.current) chartRef.current.remove()
    if (rsiChartRef.current) rsiChartRef.current.remove()

    const chart = createChart(candleRef.current, {
      layout: { background: { color: '#111' }, textColor: '#e0e0e0' },
      grid: { vertLines: { color: '#222' }, horzLines: { color: '#222' } },
      width: candleRef.current.clientWidth || 600,
      height: 340,
    })
    chartRef.current = chart

    const rsiChart = createChart(rsiRef.current, {
      layout: { background: { color: '#111' }, textColor: '#666' },
      grid: { vertLines: { color: '#1a1a1a' }, horzLines: { color: '#1a1a1a' } },
      width: rsiRef.current.clientWidth || 600,
      height: 100,
      rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } },
    })
    rsiChartRef.current = rsiChart

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: candleRef.current.clientWidth })
      rsiChart.applyOptions({ width: rsiRef.current.clientWidth })
    })
    ro.observe(candleRef.current)

    return () => { ro.disconnect(); chart.remove(); rsiChart.remove() }
  }, [])

  useEffect(() => {
    if (!chartRef.current || !rsiChartRef.current) return
    // 清除舊 series
    Object.values(seriesMap.current).forEach(s => {
      try { chartRef.current.removeSeries(s) } catch {}
    })
    seriesMap.current = {}

    const colors = ['#ff6600', '#00aaff', '#ff00ff', '#ffff00']

    symbols.forEach((symbol, idx) => {
      const color = colors[idx % colors.length]

      if (idx === 0) {
        // 主股票用 K 線
        const candle = chartRef.current.addSeries(CandlestickSeries, {
          upColor: '#00ff88', downColor: '#ff4444',
          borderUpColor: '#00ff88', borderDownColor: '#ff4444',
          wickUpColor: '#00ff88', wickDownColor: '#ff4444',
        })
        seriesMap.current[`candle_${symbol}`] = candle

        axios.get(`${API_URL}/stocks/${symbol}/history?period=${period}`)
          .then(r => candle.setData(r.data.map(d => ({
            time: d.time, open: d.open, high: d.high, low: d.low, close: d.close
          }))))

        if (showMA) {
          const ma5 = chartRef.current.addSeries(LineSeries, { color: '#ffaa00', lineWidth: 1, priceLineVisible: false })
          const ma20 = chartRef.current.addSeries(LineSeries, { color: '#00aaff', lineWidth: 1, priceLineVisible: false })
          const rsiLine = rsiChartRef.current.addSeries(LineSeries, { color: '#ff6600', lineWidth: 1, priceLineVisible: false })
          seriesMap.current['ma5'] = ma5
          seriesMap.current['ma20'] = ma20
          seriesMap.current['rsi'] = rsiLine

          axios.get(`${API_URL}/stocks/${symbol}/indicators?period=${period}`)
            .then(r => {
              ma5.setData(r.data.filter(d => d.ma5).map(d => ({ time: d.time, value: d.ma5 })))
              ma20.setData(r.data.filter(d => d.ma20).map(d => ({ time: d.time, value: d.ma20 })))
              rsiLine.setData(r.data.filter(d => d.rsi).map(d => ({ time: d.time, value: d.rsi })))
            })
        }
      } else {
        // 對比股票用折線
        const line = chartRef.current.addSeries(LineSeries, { color, lineWidth: 2, priceLineVisible: false })
        seriesMap.current[`line_${symbol}`] = line
        axios.get(`${API_URL}/stocks/${symbol}/history?period=${period}`)
          .then(r => line.setData(r.data.map(d => ({ time: d.time, value: d.close }))))
      }
    })
  }, [symbols, period, showMA])

  return (
    <div style={{ background: '#111', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '8px 16px', borderBottom: '1px solid #222', display: 'flex', gap: 8, alignItems: 'center' }}>
        {['5d','1mo','3mo','6mo','1y'].map(p => (
          <button key={p} onClick={() => setPeriod(p)} style={{
            background: period === p ? '#ff6600' : '#1a1a1a', border: 'none',
            color: period === p ? '#000' : '#888', padding: '4px 12px', cursor: 'pointer', fontFamily: 'inherit'
          }}>{p}</button>
        ))}
        <button onClick={() => setShowMA(v => !v)} style={{
          background: showMA ? '#333' : '#1a1a1a', border: '1px solid #444',
          color: showMA ? '#ffaa00' : '#555', padding: '4px 12px', cursor: 'pointer', fontFamily: 'inherit', marginLeft: 8
        }}>MA</button>
        <span style={{ color: '#555', fontSize: 11, marginLeft: 8 }}>
          {symbols.length > 1 && symbols.slice(1).map((s,i) => (
            <span key={s} style={{ color: ['#00aaff','#ff00ff','#ffff00'][i], marginRight: 8 }}>— {s}</span>
          ))}
        </span>
      </div>
      <div ref={candleRef} style={{ width: '100%' }} />
      <div ref={rsiRef} style={{ width: '100%', borderTop: '1px solid #1a1a1a' }} />
    </div>
  )
}
