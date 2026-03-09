import { useState } from "react"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

function App() {
    const [symbol, setSymbol] = useState('')
    const [alphaKey, setAlpha] = useState('')
    const [data, setData] = useState(null)
    const fetchStock = async () => {
                            const response = await fetch(`http://127.0.0.1:5000/api/stock?symbol=${symbol}&api_key=${alphaKey}`)
                            const json = await response.json()
                            console.log(json)
                            setData(json)
}
    return(<div>
        <input type='text' placeholder='Stock Ticker' value={symbol} onChange = {(e) => setSymbol(e.target.value)}/>
        <input type='text' placeholder='API key' value={alphaKey} onChange = {(e) => setAlpha(e.target.value)}/>
        <button onClick={() => {
    console.log('button clicked')
    fetchStock()
}}>Analyse</button>
        {data && (
            <div>
                <h1>Results for {symbol}</h1>
                    <p>Close: ${data.metrics.close.toFixed(2)}</p>
                    <p>RSI: {data.metrics.rsi.toFixed(2)}</p>
                    <p>MACD: {data.metrics.macd.toFixed(2)}</p>
                    <p>Signal: {data.metrics.signal.toFixed(2)}</p>
                    <p>VWAP: {data.metrics.vwap.toFixed(2)}</p>
                    <p>Sharpe Ratio: {data.metrics.sharpe.toFixed(2)}</p>
                    <p>ATR: {data.metrics.atr.toFixed(2)}</p>
                    <p>Volume: {data.metrics.volume.toLocaleString()}</p>
                <div>
                <ResponsiveContainer width='100%' height={300}>
                    <LineChart data={data.prices}>
                        <XAxis dataKey='Date' hide={true}/>
                        <YAxis domain={['auto', 'auto']}/>
                        <Tooltip/>
                        <Line type="monotone" dataKey="Close" stroke="gold" dot={false}/>
                        <Line type="monotone" dataKey="SMA_50" stroke="orange" dot={false}/>
                        <Line type="monotone" dataKey="VWAP" stroke="cyan" dot={false}/>
                    </LineChart>
                </ResponsiveContainer>


                </div>
            </div>
        )

        }

        </div>)
}
export default App