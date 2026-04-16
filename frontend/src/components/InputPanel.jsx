import { useState, useRef } from "react";
import { DEMO_INPUTS } from "../utils/constants";
import { BACKEND } from "../utils/constants";
import axios from "axios";

const DEMO_COLORS = {
  'Fees Query':  { bg:'#22c55e22', border:'#22c55e50', dot:'#22c55e' },
  'Hack Portal': { bg:'#ef444422', border:'#ef444450', dot:'#ef4444' },
  'Injection':   { bg:'#f59e0b22', border:'#f59e0b50', dot:'#f59e0b' },
  'API Key':     { bg:'#3b82f622', border:'#3b82f650', dot:'#3b82f6' },
  'Ragging':     { bg:'#ef444422', border:'#ef444450', dot:'#ef4444' },
  'Benign':      { bg:'#22c55e22', border:'#22c55e50', dot:'#22c55e' },
};
const DC = { ALLOW:'#22c55e', RESTRICT:'#f59e0b', REDACT:'#3b82f6', BLOCK:'#ef4444' };

export default function InputPanel({text,setText,policy,setPolicy,role,setRole,useRag,setUseRag,onAnalyze,loading,history,onResult,onError}){
  const [inputType, setInputType] = useState("text");
  const [imagePreview, setImagePreview] = useState(null);
  const [imageB64, setImageB64] = useState(null);
  const [docContent, setDocContent] = useState("");
  const [docName, setDocName]    = useState("");
  const [docLoading, setDocLoading] = useState(false);
  const fileRef  = useRef(null);
  const docRef   = useRef(null);

  const handleImage = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target.result;
      setImagePreview(dataUrl);
      setImageB64(dataUrl.split(",")[1]);
    };
    reader.readAsDataURL(file);
  };

  const handleDoc = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setDocName(file.name);
    setDocLoading(true);
    try {
      const text = await file.text();
      setDocContent(text);
    } catch {
      onError?.("Could not read file. Please upload a .txt file.");
    } finally {
      setDocLoading(false);
    }
  };

  const analyzeImage = async () => {
    if (!imageB64) return;
    onError?.("");
    onResult?.(null);
    try {
      const res = await axios.post(`${BACKEND}/analyze-image`, {
        image_base64: imageB64, policy, role,
      });
      onResult?.(res.data);
    } catch(e) {
      onError?.("Image analysis error: " + (e.response?.data?.detail || e.message));
    }
  };

  const analyzeDoc = async () => {
    if (!docContent) return;
    onError?.("");
    onResult?.(null);
    try {
      const res = await axios.post(`${BACKEND}/analyze-document`, {
        content: docContent, filename: docName, policy, role,
      });
      onResult?.(res.data);
    } catch(e) {
      onError?.("Document analysis error: " + (e.response?.data?.detail || e.message));
    }
  };

  return(
    <div style={{display:'flex',flexDirection:'column',gap:14}}>
      <div style={{background:'var(--card)',border:'1px solid var(--border)',borderRadius:12,padding:16}}>

        {/* Input type tabs */}
        <div style={{display:'flex',gap:4,marginBottom:14,background:'var(--bg2)',borderRadius:8,padding:3}}>
          {[['📝','Text','text'],['🖼️','Image','image'],['📄','Doc','doc']].map(([ic,lb,id])=>(
            <button key={id} onClick={()=>setInputType(id)} style={{flex:1,background:inputType===id?'var(--card)':'transparent',border:'none',color:inputType===id?'var(--text)':'var(--text2)',padding:'6px 0',borderRadius:6,fontSize:12,fontWeight:inputType===id?700:400,transition:'all 0.15s'}}>
              {ic} {lb}
            </button>
          ))}
        </div>

        {/* TEXT INPUT */}
        {inputType==="text" && (
          <>
            <div style={{fontSize:10,fontWeight:700,color:'var(--text2)',letterSpacing:'0.06em',marginBottom:8}}>QUICK DEMO</div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:6,marginBottom:12}}>
              {DEMO_INPUTS.map(d=>{
                const c=DEMO_COLORS[d.label]||DEMO_COLORS['Benign'];
                return(
                  <button key={d.label} onClick={()=>setText(d.text)} style={{background:c.bg,border:`1px solid ${c.border}`,borderRadius:7,padding:'7px 10px',fontSize:11,color:'var(--text)',display:'flex',alignItems:'center',gap:6,fontWeight:500,textAlign:'left'}}>
                    <div style={{width:6,height:6,borderRadius:'50%',background:c.dot,flexShrink:0}}/>
                    {d.label}
                  </button>
                );
              })}
            </div>
            <textarea style={{width:'100%',background:'var(--bg2)',border:'1px solid var(--border)',borderRadius:8,padding:12,fontSize:13,resize:'vertical',color:'var(--text)',outline:'none',boxSizing:'border-box',lineHeight:1.6}} value={text} onChange={e=>setText(e.target.value)} placeholder="Enter prompt or text to analyze..." rows={5}/>
            <div style={{fontSize:10,color:'var(--text2)',textAlign:'right',marginTop:3}}>{text.length} chars</div>
          </>
        )}

        {/* IMAGE INPUT */}
        {inputType==="image" && (
          <div style={{display:'flex',flexDirection:'column',gap:12}}>
            <div style={{border:`2px dashed var(--border)`,borderRadius:10,padding:20,textAlign:'center',cursor:'pointer',background:'var(--bg2)'}} onClick={()=>fileRef.current?.click()}>
              {imagePreview ? (
                <img src={imagePreview} alt="preview" style={{maxHeight:180,maxWidth:'100%',borderRadius:8,objectFit:'contain'}}/>
              ) : (
                <>
                  <div style={{fontSize:32,marginBottom:8}}>🖼️</div>
                  <div style={{fontSize:13,color:'var(--text2)'}}>Click to upload image</div>
                  <div style={{fontSize:11,color:'var(--text2)',marginTop:4}}>JPG, PNG, GIF supported</div>
                </>
              )}
              <input ref={fileRef} type="file" accept="image/*" onChange={handleImage} style={{display:'none'}}/>
            </div>
            {imagePreview && (
              <button onClick={()=>{setImagePreview(null);setImageB64(null);}} style={{background:'#ef444422',border:'1px solid #ef444440',color:'#ef4444',borderRadius:6,padding:'5px 12px',fontSize:11}}>
                ✕ Remove image
              </button>
            )}
          </div>
        )}

        {/* DOCUMENT INPUT */}
        {inputType==="doc" && (
          <div style={{display:'flex',flexDirection:'column',gap:12}}>
            <div style={{border:`2px dashed var(--border)`,borderRadius:10,padding:20,textAlign:'center',cursor:'pointer',background:'var(--bg2)'}} onClick={()=>docRef.current?.click()}>
              {docName ? (
                <>
                  <div style={{fontSize:28,marginBottom:6}}>📄</div>
                  <div style={{fontSize:13,color:'var(--text)',fontWeight:600}}>{docName}</div>
                  <div style={{fontSize:11,color:'var(--text2)',marginTop:4}}>{docContent.length} characters loaded</div>
                </>
              ) : (
                <>
                  <div style={{fontSize:32,marginBottom:8}}>📄</div>
                  <div style={{fontSize:13,color:'var(--text2)'}}>Click to upload document</div>
                  <div style={{fontSize:11,color:'var(--text2)',marginTop:4}}>.txt files supported</div>
                </>
              )}
              <input ref={docRef} type="file" accept=".txt,.md,.csv" onChange={handleDoc} style={{display:'none'}}/>
            </div>
            {docLoading && <div style={{fontSize:12,color:'var(--text2)',textAlign:'center'}}>⏳ Reading file...</div>}
            {docName && (
              <button onClick={()=>{setDocName("");setDocContent("");}} style={{background:'#ef444422',border:'1px solid #ef444440',color:'#ef4444',borderRadius:6,padding:'5px 12px',fontSize:11}}>
                ✕ Remove document
              </button>
            )}
          </div>
        )}

        {/* Policy and Role */}
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,margin:'12px 0'}}>
          {[
            {label:'POLICY',val:policy,set:setPolicy,opts:[['strict','🔒 Strict'],['moderate','⚖️ Moderate'],['open','🔓 Open']]},
            {label:'USER ROLE',val:role,set:setRole,opts:[['student','🎓 Student'],['general','👤 General'],['expert','🔬 Expert']]},
          ].map(({label,val,set,opts})=>(
            <div key={label}>
              <div style={{fontSize:10,fontWeight:700,color:'var(--text2)',letterSpacing:'0.06em',marginBottom:5}}>{label}</div>
              <select value={val} onChange={e=>set(e.target.value)} style={{width:'100%',background:'var(--bg2)',border:'1px solid var(--border)',borderRadius:7,padding:'8px 10px',fontSize:12,color:'var(--text)',outline:'none',cursor:'pointer'}}>
                {opts.map(([v,l])=>(<option key={v} value={v}>{l}</option>))}
              </select>
            </div>
          ))}
        </div>

        {/* RAG toggle — only for text */}
        {inputType==="text" && (
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'8px 12px',background:'var(--bg2)',border:'1px solid var(--border)',borderRadius:8,marginBottom:12}}>
            <span style={{fontSize:12,color:'var(--text)'}}>📚 RAG Knowledge Base</span>
            <button onClick={()=>setUseRag(!useRag)} style={{background:useRag?'#22c55e':'var(--card)',border:`1px solid ${useRag?'#22c55e':'var(--border)'}`,borderRadius:20,padding:'3px 12px',fontSize:11,fontWeight:700,color:useRag?'#fff':'var(--text2)',transition:'all 0.2s'}}>
              {useRag?'ON':'OFF'}
            </button>
          </div>
        )}

        {/* Analyze button */}
        {inputType==="text" && (
          <button onClick={onAnalyze} disabled={loading||!text.trim()} style={{width:'100%',background:loading||!text.trim()?'var(--border)':'linear-gradient(135deg,#3b82f6,#0ea5e9)',color:'#fff',border:'none',borderRadius:8,padding:12,fontSize:14,fontWeight:700,transition:'all 0.2s',boxShadow:loading||!text.trim()?'none':'0 4px 16px rgba(59,130,246,0.4)'}}>
            {loading?'⏳ Analyzing...':'⚡ Analyze Input'}
          </button>
        )}
        {inputType==="image" && (
          <button onClick={analyzeImage} disabled={!imageB64} style={{width:'100%',background:!imageB64?'var(--border)':'linear-gradient(135deg,#a855f7,#7c3aed)',color:'#fff',border:'none',borderRadius:8,padding:12,fontSize:14,fontWeight:700,boxShadow:!imageB64?'none':'0 4px 16px rgba(168,85,247,0.4)'}}>
            🖼️ Analyze Image
          </button>
        )}
        {inputType==="doc" && (
          <button onClick={analyzeDoc} disabled={!docContent||docLoading} style={{width:'100%',background:!docContent?'var(--border)':'linear-gradient(135deg,#f59e0b,#d97706)',color:'#fff',border:'none',borderRadius:8,padding:12,fontSize:14,fontWeight:700,boxShadow:!docContent?'none':'0 4px 16px rgba(245,158,11,0.4)'}}>
            📄 Analyze Document
          </button>
        )}
      </div>

      {/* History */}
      {history.length>0&&(
        <div style={{background:'var(--card)',border:'1px solid var(--border)',borderRadius:12,padding:14}}>
          <div style={{fontSize:10,fontWeight:700,color:'var(--text2)',letterSpacing:'0.06em',marginBottom:10}}>SESSION HISTORY</div>
          {history.map((h,i)=>(
            <div key={i} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'6px 0',borderBottom:'1px solid var(--border)'}}>
              <span style={{fontSize:11,color:'var(--text2)',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',maxWidth:'68%'}}>{h.display_text?.slice(0,38)}...</span>
              <span style={{background:DC[h.decision]+'22',color:DC[h.decision],border:`1px solid ${DC[h.decision]}50`,fontSize:10,fontWeight:700,padding:'2px 8px',borderRadius:4,flexShrink:0}}>{h.decision}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}