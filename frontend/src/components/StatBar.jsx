export default function StatBar({ sessionCount }) {
  const stats = [
    { icon:'⚙️', value:'9',            label:'CONFIGURATIONS',  sub:'3 roles × 3 policies',  grad:'linear-gradient(135deg,#a855f722,#a855f711)', border:'#a855f740', vc:'#a855f7' },
    { icon:'🛡️', value:'30',           label:'INJECTION RULES', sub:'Pattern-based override', grad:'linear-gradient(135deg,#f59e0b22,#f59e0b11)', border:'#f59e0b40', vc:'#f59e0b' },
    { icon:'📚', value:'RAG',          label:'KNOWLEDGE BASE',  sub:'BM25 + FAISS retrieval', grad:'linear-gradient(135deg,#0ea5e922,#0ea5e911)', border:'#0ea5e940', vc:'#0ea5e9' },
    { icon:'📊', value:sessionCount||0, label:'SESSION SCANS',   sub:'This session',           grad:'linear-gradient(135deg,#22c55e22,#22c55e11)', border:'#22c55e40', vc:'#22c55e' },
  ];
  return (
    <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:10,marginBottom:16}}>
      {stats.map(s=>(
        <div key={s.label} style={{background:s.grad,border:`1px solid ${s.border}`,borderRadius:10,padding:'14px 12px',position:'relative',overflow:'hidden'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:6}}>
            <div style={{fontSize:11,fontWeight:700,color:'var(--text2)',letterSpacing:'0.06em'}}>{s.label}</div>
            <span style={{fontSize:16,opacity:0.7}}>{s.icon}</span>
          </div>
          <div style={{fontSize:28,fontWeight:900,color:s.vc,lineHeight:1}}>{s.value}</div>
          <div style={{fontSize:10,color:'var(--text2)',marginTop:4}}>{s.sub}</div>
        </div>
      ))}
    </div>
  );
}