import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Play, 
  Square, 
  Settings, 
  LayoutDashboard, 
  History, 
  Camera,
  Cpu,
  BarChart3
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip 
} from 'recharts';

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [streamData, setStreamData] = useState(null);
  const [stats, setStats] = useState({ total: 0, defects: 0, fps: 0, latency: '0ms' });
  const [history, setHistory] = useState([]);
  const [chartData, setChartData] = useState([]);
  const ws = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    // Check initial status
    fetch('http://localhost:8000/status')
      .then(res => res.json())
      .then(data => setIsRunning(data.status === 'online'));
  }, []);

  useEffect(() => {
    if (isRunning) {
      ws.current = new WebSocket('ws://localhost:8000/ws');
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setStreamData(data);
        setStats(data.stats);
        
        if (data.status === 'REJECT') {
          setHistory(prev => [
            { 
              time: new Date().toLocaleTimeString(), 
              type: data.detections[0].class, 
              conf: (data.detections[0].confidence * 100).toFixed(1) + '%' 
            }, 
            ...prev
          ].slice(0, 10));
        }

        // Update Chart Data
        setChartData(prev => {
           const newData = [...prev, { time: new Date().toLocaleTimeString().slice(-5), value: data.stats.total % 100 }];
           return newData.slice(-10);
        });
      };
    } else {
      if (ws.current) ws.current.close();
    }
    return () => ws.current?.close();
  }, [isRunning]);

  const toggleSystem = async () => {
    const action = isRunning ? 'stop' : 'start';
    const res = await fetch(`http://localhost:8000/control/${action}`, { method: 'POST' });
    if (res.ok) setIsRunning(!isRunning);
  };

  return (
    <div className="dashboard-container">
      <header>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '8px', background: 'var(--accent-secondary)', borderRadius: '6px' }}>
            <Camera size={24} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: '800' }}>HIKVISION <span style={{ color: 'var(--accent-primary)' }}>SMART VISION</span></h1>
            <p style={{ fontSize: '10px', color: 'var(--text-secondary)', letterSpacing: '1px' }}>V.2.4.0 INDUSTRIAL DEFECT DETECTION</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '20px' }}>
          <div className="glass-pill"><Cpu size={14} style={{ marginRight: '6px' }} /> NVIDIA TENSORRT ENABLED</div>
          <div className="glass-pill"><Activity size={14} style={{ marginRight: '6px' }} /> LATENCY: {stats.latency}</div>
        </div>
      </header>

      <aside className="sidebar">
        <div className="card" onClick={() => {}} style={{ cursor: 'pointer', borderColor: 'var(--accent-primary)' }}>
          <div className="card-title">System Control</div>
          <button className={`btn ${isRunning ? 'btn-primary' : 'btn-primary'}`} style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', backgroundColor: isRunning ? 'var(--danger)' : 'var(--success)' }} onClick={toggleSystem}>
            {isRunning ? <Square size={16} fill="white" /> : <Play size={16} fill="white" />}
            {isRunning ? 'HALT SYSTEM' : 'ENGAGE PIPELINE'}
          </button>
        </div>

        <div className="card">
          <div className="card-title">Detection Parameters</div>
          <div style={{ margin: '12px 0' }}>
            <label style={{ fontSize: '11px', display: 'block', marginBottom: '8px' }}>CONFIDENCE THRESHOLD (0.65)</label>
            <input type="range" style={{ width: '100%' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
            <span>Auto-Reject</span>
            <input type="checkbox" defaultChecked />
          </div>
        </div>

        <div style={{ marginTop: 'auto' }}>
          <div className="card" style={{ background: 'transparent', border: 'none' }}>
             <div className="card-title">System Status</div>
             <div style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
               <span className="status-indicator"></span> 
               SECURE CONNECTION: 8000
             </div>
          </div>
        </div>
      </aside>

      <main className="main-view">
        <div className={`feed-container ${streamData?.status === 'REJECT' ? 'reject-pulse' : ''}`}>
          {streamData ? (
            <img 
              src={`data:image/jpeg;base64,${streamData.image}`} 
              alt="Feed" 
              style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
            />
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#050505', color: '#333' }}>
              <Camera size={64} opacity={0.1} />
            </div>
          )}
          <div className="feed-overlay">
            CAM_01_REAR_LINE | {stats.fps} FPS | {isRunning ? 'RECORDING' : 'IDLE'}
          </div>
          {streamData?.status === 'REJECT' && (
            <div style={{ position: 'absolute', bottom: '20px', right: '20px', background: 'var(--danger)', padding: '12px 24px', borderRadius: '4px', fontWeight: '800', fontSize: '24px' }}>
              REJECT
            </div>
          )}
        </div>

        <div style={{ height: '220px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--grid-line)', padding: '16px' }}>
          <div className="card-title">Production Metrics (Hourly)</div>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.3)" fontSize={10} />
              <Tooltip 
                contentStyle={{ background: '#14161f', border: '1px solid #333' }}
                itemStyle={{ color: '#00f2ff' }}
               />
              <Area type="monotone" dataKey="value" stroke="var(--accent-primary)" fillOpacity={1} fill="url(#colorVal)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </main>

      <aside className="right-panel">
        <div className="card">
          <div className="card-title">Inspection Stats</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <p style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>TOTAL ITEMS</p>
              <p className="stat-value">{stats.total}</p>
            </div>
            <div>
              <p style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>DEFECTS</p>
              <p className="stat-value" style={{ color: 'var(--danger)' }}>{stats.defects}</p>
            </div>
          </div>
          <div style={{ marginTop: '12px' }}>
             <p style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>REJECT RATE</p>
             <div style={{ height: '4px', background: '#333', borderRadius: '2px', marginTop: '6px' }}>
               <div style={{ width: `${(stats.defects/Math.max(1, stats.total))*100}%`, height: '100%', background: 'var(--danger)', borderRadius: '2px' }}></div>
             </div>
          </div>
        </div>

        <div className="card" style={{ flex: 1, overflowY: 'auto' }}>
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={14} /> DEFECT HISTORY
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '12px' }}>
            {history.map((h, i) => (
              <div key={i} style={{ padding: '8px', background: 'rgba(255, 77, 77, 0.05)', borderRadius: '4px', borderLeft: '3px solid var(--danger)', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: '700' }}>{h.type}</span>
                  <span style={{ opacity: 0.5 }}>{h.time}</span>
                </div>
                <div style={{ fontSize: '10px', opacity: 0.7 }}>CONFIDENCE: {h.conf}</div>
              </div>
            ))}
            {history.length === 0 && <div style={{ textAlign: 'center', opacity: 0.3, marginTop: '20px' }}>No defects logged</div>}
          </div>
        </div>
      </aside>
    </div>
  );
}

export default App;
