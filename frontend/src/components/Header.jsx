export default function Header({ view, setView, live, dark, setDark }) {
  const navItems = [
    { id: 'analyze',   icon: '⚡', label: 'Analyze' },
    { id: 'compare',   icon: '⚖️', label: 'Compare' },
    { id: 'dashboard', icon: '📊', label: 'Dashboard' },
  ];
  return (
    <header style={{background:'var(--card)',borderBottom:'1px solid var(--border)',padding:'0 20px',height:58,display:'flex',alignItems:'center',justifyContent:'space-between',position:'sticky',top:0,zIndex:100,backdropFilter:'blur(12px)'}}>
      <div style={{display:'flex',alignItems:'center',gap:10}}>
        <div style={{width:34,height:34,borderRadius:8,background:'linear-gradient(135deg,#3b82f6,#0ea5e9)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:18}}>🛡</div>
        <div>
          <div style={{color:'var(--text)',fontWeight:800,fontSize:16,lineHeight:1.1}}>SafeGen AI</div>
          <div style={{color:'var(--text2)',fontSize:10,letterSpacing:'0.05em'}}>ADAPTIVE GUARDRAIL SYSTEM</div>
        </div>
      </div>

      <nav style={{display:'flex',gap:4}}>
        {navItems.map(({id,icon,label})=>(
          <button key={id} onClick={()=>setView(id)} style={{
            background: view===id ? 'linear-gradient(135deg,#3b82f6,#0ea5e9)' : 'transparent',
            border: view===id ? 'none' : '1px solid var(--border)',
            color: view===id ? '#fff' : 'var(--text2)',
            padding:'6px 14px', borderRadius:7, fontSize:12, fontWeight:600,
            display:'flex', alignItems:'center', gap:5,
            boxShadow: view===id ? '0 2px 12px rgba(59,130,246,0.4)' : 'none',
            transition:'all 0.2s',
          }}>
            <span>{icon}</span>
            <span className="nav-label">{label}</span>
          </button>
        ))}
      </nav>

      <div style={{display:'flex',alignItems:'center',gap:10}}>
        <div style={{display:'flex',alignItems:'center',gap:6,background:'var(--bg2)',border:'1px solid var(--border)',borderRadius:20,padding:'4px 10px'}}>
          <div style={{width:7,height:7,borderRadius:'50%',background:live?'#22c55e':'#f59e0b',animation: live?'none':'pulse 1.5s infinite'}}/>
          <span style={{color:live?'#22c55e':'#f59e0b',fontSize:10,fontWeight:700,letterSpacing:'0.05em'}}>{live?'LIVE':'WAKING UP'}</span>
        </div>
        <button onClick={()=>setDark(!dark)} style={{background:'var(--bg2)',border:'1px solid var(--border)',color:'var(--text)',width:34,height:34,borderRadius:8,fontSize:16,display:'flex',alignItems:'center',justifyContent:'center'}}>
          {dark?'☀️':'🌙'}
        </button>
      </div>
    </header>
  );
}