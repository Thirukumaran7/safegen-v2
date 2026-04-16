import { DECISION_COLORS, DECISION_ICONS } from "../utils/constants";

function Ring({score,color}){
  const r=34,c=2*Math.PI*r;
  return(
    <div style={{position:'relative',width:88,height:88,flexShrink:0}}>
      <svg width="88" height="88" viewBox="0 0 88 88">
        <circle cx="44" cy="44" r={r} fill="none" stroke="var(--border)" strokeWidth="7"/>
        <circle cx="44" cy="44" r={r} fill="none" stroke={color} strokeWidth="7"
          strokeDasharray={`${(score/10)*c} ${c}`} strokeLinecap="round"
          transform="rotate(-90 44 44)" style={{transition:'stroke-dasharray 0.8s ease'}}/>
      </svg>
      <div style={{position:'absolute',top:'50%',left:'50%',transform:'translate(-50%,-50%)',fontSize:18,fontWeight:900,color:'var(--text)'}}>{score}</div>
    </div>
  );
}

function Det({title,main,sub,score,bar,tc,extra}){
  return(
    <div style={{background:'var(--card2)',border:'1px solid var(--border)',borderRadius:10,padding:14}}>
      <div style={{fontSize:10,fontWeight:700,color:'var(--text2)',marginBottom:8,letterSpacing:'0.06em'}}>{title}</div>
      <div style={{fontSize:14,fontWeight:800,color:tc,marginBottom:2}}>{main}</div>
      {sub   && <div style={{fontSize:11,color:'var(--text2)',marginTop:1}}>{sub}</div>}
      {extra && <div style={{fontSize:11,color:'#ef4444',marginTop:3,fontWeight:700}}>{extra}</div>}
      <div style={{height:3,background:'var(--bg)',borderRadius:2,margin:'10px 0 4px'}}>
        <div style={{height:'100%',width:`${Math.min(score*10,100)}%`,background:bar,borderRadius:2,transition:'width 0.7s ease'}}/>
      </div>
      <div style={{fontSize:10,color:'var(--text2)'}}>Score: {score}/10</div>
    </div>
  );
}

export default function ResultPanel({result,loading,onFeedback}){
  const DC = DECISION_COLORS;
  if(loading) return(
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',minHeight:400,background:'var(--card)',border:'1px solid var(--border)',borderRadius:12,gap:12}}>
      <div style={{width:44,height:44,border:'3px solid var(--border)',borderTop:'3px solid #3b82f6',borderRadius:'50%',animation:'spin 0.8s linear infinite'}}/>
      <div style={{fontSize:15,fontWeight:700,color:'var(--text)'}}>Analyzing...</div>
      <div style={{fontSize:12,color:'var(--text2)'}}>Running DistilBERT + RAG pipeline</div>
    </div>
  );
  if(!result) return(
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',minHeight:400,background:'var(--card)',border:'1px solid var(--border)',borderRadius:12,gap:10}}>
      <div style={{width:60,height:60,borderRadius:16,background:'linear-gradient(135deg,#3b82f622,#0ea5e922)',border:'1px solid #3b82f640',display:'flex',alignItems:'center',justifyContent:'center',fontSize:28}}>🛡</div>
      <div style={{fontSize:15,fontWeight:700,color:'var(--text)'}}>Awaiting Input</div>
      <div style={{fontSize:12,color:'var(--text2)'}}>Results and analysis will appear here</div>
    </div>
  );

  const dc = DC[result.decision];
  return(
    <div style={{display:'flex',flexDirection:'column',gap:12,animation:'fadeSlide 0.3s ease'}}>

      {/* Decision banner */}
      <div style={{background:`linear-gradient(135deg,${dc}22,${dc}11)`,border:`1px solid ${dc}50`,borderRadius:12,padding:16,display:'flex',alignItems:'center',gap:14,flexWrap:'wrap'}}>
        <div style={{width:56,height:56,borderRadius:12,background:`linear-gradient(135deg,${dc},${dc}aa)`,display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontSize:26,fontWeight:900,flexShrink:0,boxShadow:`0 4px 16px ${dc}44`}}>
          {DECISION_ICONS[result.decision]}
        </div>
        <div style={{flex:1,minWidth:120}}>
          <div style={{fontSize:26,fontWeight:900,color:dc,lineHeight:1,letterSpacing:'-0.02em'}}>{result.decision}</div>
          <div style={{fontSize:13,color:'var(--text2)',marginTop:3}}>{result.description}</div>
          <div style={{fontSize:11,color:'var(--text2)',marginTop:5,display:'flex',gap:8,flexWrap:'wrap'}}>
            <span style={{background:'var(--bg2)',border:'1px solid var(--border)',padding:'2px 8px',borderRadius:4}}>{result.role}</span>
            <span style={{background:'var(--bg2)',border:'1px solid var(--border)',padding:'2px 8px',borderRadius:4}}>{result.policy}</span>
            {result.rag_used && <span style={{background:'#0ea5e922',border:'1px solid #0ea5e940',color:'#0ea5e9',padding:'2px 8px',borderRadius:4}}>📚 RAG</span>}
            {result.injection_detected && <span style={{background:'#ef444422',border:'1px solid #ef444440',color:'#ef4444',padding:'2px 8px',borderRadius:4}}>🚨 Injection</span>}
          </div>
        </div>
        <Ring score={result.final_score} color={dc}/>
      </div>

      {/* Detectors */}
      <div className="det-grid" style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:10}}>
        <Det title="🦠 MALWARE DETECTION" main={result.malware_type!=='None'?result.malware_type:'✓ No Malware'} sub={result.malware_type!=='None'?`${result.malware_category} · ${result.severity}`:''} score={result.scores.malware} bar="#ef4444" tc={result.malware_type!=='None'?'#ef4444':'#22c55e'}/>
        <Det title="🔐 SENSITIVE DATA" main={result.pii_detected?`${result.pii_count} PII Found`:'✓ No PII Found'} sub={result.pii_detected?result.pii_types?.slice(0,2).join(', '):''} score={result.scores.sensitive} bar="#3b82f6" tc={result.pii_detected?'#3b82f6':'#22c55e'} extra={result.pii_detected?`Anon: ${result.anonymisation_score}%`:''}/>
        <Det title="🎯 INTENT ANALYSIS" main={result.threat_category} sub={`Confidence: ${Math.round(result.intent_confidence*100)}%`} score={result.scores.intent} bar="#f59e0b" tc={dc} extra={result.injection_detected?'⚠ Injection Detected':''}/>
      </div>

      {/* RAG sources */}
      {result.rag_used&&result.rag_sources?.length>0&&(
        <div style={{background:'var(--card)',border:'1px solid #0ea5e930',borderRadius:12,padding:14}}>
          <div style={{fontSize:10,fontWeight:700,color:'#0ea5e9',letterSpacing:'0.06em',marginBottom:10}}>📚 RAG — KNOWLEDGE BASE SOURCES</div>
          {result.rag_sources.map((s,i)=>(
            <div key={i} style={{display:'flex',alignItems:'center',gap:10,padding:'6px 0',borderBottom:'1px solid var(--border)',flexWrap:'wrap'}}>
              <span style={{background:'#0ea5e922',color:'#0ea5e9',border:'1px solid #0ea5e940',padding:'2px 8px',borderRadius:4,fontSize:10,fontWeight:700,flexShrink:0}}>{s.id}</span>
              <span style={{flex:1,fontSize:12,color:'var(--text)',fontWeight:600,minWidth:80}}>{s.title}</span>
              <span style={{fontSize:10,color:'var(--text2)'}}>BM25: {s.score}</span>
            </div>
          ))}
        </div>
      )}

      {/* Decision reasoning */}
      <div style={{background:'var(--card)',border:'1px solid var(--border)',borderRadius:12,padding:14}}>
        <div style={{fontSize:10,fontWeight:700,color:'var(--text2)',letterSpacing:'0.06em',marginBottom:10}}>DECISION REASONING</div>
        {result.explanation?.map((line,i)=>(
          <div key={i} style={{fontSize:12,color:'var(--text2)',padding:'3px 0',lineHeight:1.6}}>▸ {line}</div>
        ))}
        <div style={{marginTop:10,padding:'8px 12px',background:'var(--bg2)',borderRadius:6,fontSize:12,color:'var(--text2)',borderLeft:`3px solid ${dc}`}}>
          <strong style={{color:'var(--text)'}}>Reason: </strong>{result.reason}
        </div>
      </div>

      {/* AI Response */}
      <div style={{background:'var(--card)',border:'1px solid var(--border)',borderRadius:12,padding:14}}>
        <div style={{fontSize:10,fontWeight:700,color:'var(--text2)',letterSpacing:'0.06em',marginBottom:10}}>AI RESPONSE</div>
        <div style={{fontSize:13,color:'var(--text)',lineHeight:1.8,whiteSpace:'pre-wrap'}}>{result.response}</div>
      </div>

      {/* Feedback */}
      <div style={{display:'flex',gap:8,justifyContent:'flex-end',alignItems:'center'}}>
        <span style={{fontSize:11,color:'var(--text2)'}}>Correct decision?</span>
        <button onClick={()=>onFeedback(result.log_id,true)} style={{background:'#22c55e22',border:'1px solid #22c55e40',color:'#22c55e',borderRadius:6,padding:'6px 14px',fontSize:12,fontWeight:600}}>👍 Yes</button>
        <button onClick={()=>onFeedback(result.log_id,false)} style={{background:'#ef444422',border:'1px solid #ef444440',color:'#ef4444',borderRadius:6,padding:'6px 14px',fontSize:12,fontWeight:600}}>👎 No</button>
      </div>
    </div>
  );
}