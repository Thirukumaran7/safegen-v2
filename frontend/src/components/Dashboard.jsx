import { useEffect, useState } from "react";
import { fetchStats, fetchLogs } from "../utils/api";
import { DECISION_COLORS } from "../utils/constants";
export default function Dashboard(){
  const [stats,setStats]=useState(null);
  const [logs,setLogs]=useState([]);
  useEffect(()=>{fetchStats().then(r=>setStats(r.data)).catch(()=>{});fetchLogs(50).then(r=>setLogs(r.data)).catch(()=>{});},[]);
  const card={background:"#fff",border:"1px solid #e2e8f0",borderRadius:12,padding:16};
  const ct={fontSize:12,fontWeight:700,color:"#334155",marginBottom:14,textTransform:"uppercase",letterSpacing:"0.06em"};
  return(
    <div style={{padding:20,maxWidth:1400,margin:"0 auto"}}>
      <div style={{fontSize:22,fontWeight:800,color:"#0f172a",marginBottom:20}}>📊 Analytics Dashboard</div>
      {stats&&(
        <>
          <div style={{display:"flex",gap:12,marginBottom:20,flexWrap:"wrap"}}>
            {[{label:"Total Analyses",value:stats.total},{label:"Avg Risk Score",value:stats.avg_score},{label:"RAG Used",value:stats.rag_count},{label:"Agreement Rate",value:stats.agreement_rate+"%"},{label:"Feedback Given",value:stats.feedback_total}].map(s=>(
              <div key={s.label} style={{flex:1,minWidth:140,background:"#fff",border:"1px solid #e2e8f0",borderRadius:12,padding:"20px 16px",textAlign:"center"}}>
                <div style={{fontSize:32,fontWeight:800,color:"#0f172a"}}>{s.value}</div>
                <div style={{fontSize:12,color:"#64748b",marginTop:4}}>{s.label}</div>
              </div>
            ))}
          </div>
          {stats.decisions&&Object.keys(stats.decisions).length>0&&(
            <div style={{...card,marginBottom:20}}>
              <div style={ct}>Decision Distribution</div>
              <div style={{display:"flex",gap:12,flexWrap:"wrap"}}>
                {Object.entries(stats.decisions).map(([d,c])=>(
                  <div key={d} style={{border:`2px solid ${DECISION_COLORS[d]}`,borderRadius:10,padding:"16px 28px",textAlign:"center"}}>
                    <div style={{fontSize:32,fontWeight:800,color:DECISION_COLORS[d]}}>{c}</div>
                    <div style={{fontSize:13,color:"#64748b",marginTop:2}}>{d}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
      {logs.length>0?(
        <div style={card}>
          <div style={ct}>Analysis History ({logs.length} records)</div>
          <div style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr style={{background:"#f8fafc"}}>{["Time","Input","Role","Policy","Score","Decision","RAG"].map(h=>(<th key={h} style={{padding:"8px 12px",textAlign:"left",fontWeight:600,color:"#64748b",borderBottom:"1px solid #e2e8f0"}}>{h}</th>))}</tr></thead>
              <tbody>
                {logs.map((log,i)=>(
                  <tr key={i} style={{background:i%2===0?"#fff":"#f8fafc"}}>
                    <td style={{padding:"8px 12px",borderBottom:"1px solid #f1f5f9",color:"#334155"}}>{new Date(log.timestamp).toLocaleTimeString()}</td>
                    <td style={{padding:"8px 12px",borderBottom:"1px solid #f1f5f9",color:"#334155"}}>{log.input?.slice(0,40)}...</td>
                    <td style={{padding:"8px 12px",borderBottom:"1px solid #f1f5f9",color:"#334155"}}>{log.role}</td>
                    <td style={{padding:"8px 12px",borderBottom:"1px solid #f1f5f9",color:"#334155"}}>{log.policy}</td>
                    <td style={{padding:"8px 12px",borderBottom:"1px solid #f1f5f9",color:"#334155"}}>{log.score}</td>
                    <td style={{padding:"8px 12px",borderBottom:"1px solid #f1f5f9"}}><span style={{background:DECISION_COLORS[log.decision],color:"#fff",fontSize:10,fontWeight:700,padding:"2px 8px",borderRadius:4}}>{log.decision}</span></td>
                    <td style={{padding:"8px 12px",borderBottom:"1px solid #f1f5f9",color:"#334155"}}>{log.rag_used?"✓":"—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ):(
        <div style={{textAlign:"center",padding:60,color:"#94a3b8",fontSize:14}}>No analyses yet. Go to Analyze tab to get started.</div>
      )}
    </div>
  );
}
