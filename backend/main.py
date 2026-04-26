"""
SafeGen AI — Main FastAPI Application (Extended with Ticketing)
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import os

from database.models import init_db, get_db, AnalysisLog, FeedbackLog
from agents.risk_analyzer import run_risk_analysis
from agents.response_controller import generate_response

load_dotenv()

app = FastAPI(title="SafeGen AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()
    try:
        from agents.rag_engine import build_rag_index
        build_rag_index()
    except Exception as e:
        print(f"RAG index warning: {e}")
    print("SafeGen AI started")


RoleType   = Literal["student", "general", "expert", "customer", "agent", "admin"]
PolicyType = Literal["strict", "moderate", "open"]

class AnalyzeRequest(BaseModel):
    text:    str
    policy:  PolicyType = "moderate"
    role:    RoleType   = "general"
    use_rag: bool       = True

class TicketAnalyzeRequest(BaseModel):
    ticket_description: str
    ticket_fields:      dict       = {}
    role:               RoleType   = "customer"
    policy:             PolicyType = "moderate"
    use_rag:            bool       = True

class ImageAnalyzeRequest(BaseModel):
    image_base64: str
    policy:       PolicyType = "moderate"
    role:         RoleType   = "general"

class DocumentAnalyzeRequest(BaseModel):
    content:   str
    filename:  Optional[str] = "document"
    policy:    PolicyType    = "moderate"
    role:      RoleType      = "general"

class FeedbackRequest(BaseModel):
    analysis_id:        int
    agreed:             bool
    suggested_decision: Optional[str] = None
    user_comment:       Optional[str] = None


def save_analysis(db, analysis, response_text, policy, role, input_type="text"):
    log = AnalysisLog(
        input_text         = analysis["original_text"][:2000],
        input_type         = input_type,
        role               = role,
        policy             = policy,
        final_score        = analysis["scoring"]["final_score"],
        malware_score      = analysis["malware"]["score"],
        pii_score          = analysis["sensitive"]["score"],
        intent_score       = analysis["intent"]["score"],
        decision           = analysis["decision"]["decision"],
        decision_reason    = analysis["decision"]["reason"],
        malware_type       = analysis["malware"]["malware_type"],
        severity           = analysis["malware"]["severity"],
        pii_types          = analysis["sensitive"]["types_found"],
        pii_count          = analysis["sensitive"]["pii_count"],
        intent_label       = str(analysis["intent"]["label"]),
        intent_confidence  = float(analysis["intent"]["confidence"]),
        injection_detected = analysis["intent"]["injection_detected"],
        rag_used           = analysis.get("rag_used", False),
        rag_sources        = analysis.get("rag_sources", []),
        safe_response      = response_text,
        explanation        = analysis["explanation"],
    )
    db.add(log); db.commit(); db.refresh(log)
    return log.id


def format_response(analysis, response_text, log_id, policy, role, input_type="text", filename=None):
    r = {
        "log_id":              log_id,
        "input_type":          input_type,
        "decision":            analysis["decision"]["decision"],
        "description":         analysis["decision"]["description"],
        "reason":              analysis["decision"]["reason"],
        "final_score":         analysis["scoring"]["final_score"],
        "scores":              {"malware": analysis["malware"]["score"], "sensitive": analysis["sensitive"]["score"], "intent": analysis["intent"]["score"]},
        "contributions":       analysis["scoring"]["contributions"],
        "score_contributions": analysis["scoring"]["contributions"],
        "malware_type":        analysis["malware"]["malware_type"],
        "malware_category":    analysis["malware"]["malware_category"],
        "severity":            analysis["malware"]["severity"],
        "malware_description": analysis["malware"]["description"],
        "flags":               analysis["malware"]["flags"],
        "pii_types":           analysis["sensitive"]["types_found"],
        "pii_count":           analysis["sensitive"]["pii_count"],
        "pii_detected":        analysis["sensitive"]["pii_count"] > 0,
        "anonymisation_score": analysis["sensitive"]["anonymisation_score"],
        "privacy_risk":        analysis["sensitive"]["privacy_risk"],
        "intent_label":        str(analysis["intent"]["label"]),
        "threat_category":     analysis["intent"]["threat_category"],
        "intent_confidence":   float(analysis["intent"]["confidence"]),
        "injection_detected":  analysis["intent"]["injection_detected"],
        "injection_patterns":  analysis["intent"]["injection_patterns"],
        "explanation":         analysis["explanation"],
        "response":            response_text,
        "display_text":        analysis["display_text"],
        "rag_used":            analysis.get("rag_used", False),
        "rag_sources":         analysis.get("rag_sources", []),
        "policy":              policy,
        "role":                role,
    }
    if filename:
        r["filename"] = filename
    return r


@app.post("/analyze")
async def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):
    analysis = run_risk_analysis(text=request.text, policy=request.policy, role=request.role, use_rag=request.use_rag)
    response = generate_response(
        display_text=analysis["display_text"], decision=analysis["decision"]["decision"],
        policy=request.policy, role=request.role, explanation=analysis["explanation"],
        rag_context=analysis.get("rag_context", ""),
    )
    log_id = save_analysis(db, analysis, response["response"], request.policy, request.role, "text")
    return format_response(analysis, response["response"], log_id, request.policy, request.role, "text")


@app.post("/analyze-ticket")
async def analyze_ticket(request: TicketAnalyzeRequest, db: Session = Depends(get_db)):
    full_text = request.ticket_description
    if request.ticket_fields:
        for k, v in request.ticket_fields.items():
            full_text += f"\n{k}: {v}"

    analysis = run_risk_analysis(
        text    = full_text,
        policy  = request.policy,
        role    = request.role,
        use_rag = request.use_rag,
    )

    role_access = {
        "customer": "Customer can only view their own ticket data. Sensitive fields are restricted.",
        "agent":    "Agent has access to ticket queue. PII fields visible for working tickets.",
        "admin":    "Admin has full access to all ticket data and fields.",
    }
    access_note = role_access.get(request.role, "")

    response = generate_response(
        display_text = analysis["display_text"],
        decision     = analysis["decision"]["decision"],
        policy       = request.policy,
        role         = request.role,
        explanation  = analysis["explanation"] + ([access_note] if access_note else []),
        rag_context  = analysis.get("rag_context", ""),
    )

    log_id = save_analysis(db, analysis, response["response"], request.policy, request.role, "ticket")
    result = format_response(analysis, response["response"], log_id, request.policy, request.role, "ticket")

    result["masked_ticket"]   = analysis["display_text"]
    result["original_ticket"] = request.ticket_description
    result["role_access"]     = access_note
    result["vin_detected"]    = "vehicle_vin" in analysis["sensitive"]["types_found"]
    result["ticket_fields"]   = request.ticket_fields

    return result


@app.post("/analyze-image")
async def analyze_image(request: ImageAnalyzeRequest, db: Session = Depends(get_db)):
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = """Analyze this image for safety concerns. Check for:
1. NSFW or adult content
2. Violent or graphic content
3. Visible personal information (faces, ID cards, documents, VIN plates)
4. Malware-related content (malicious code screenshots, phishing pages)
5. Hate speech or offensive symbols

Respond in this exact format:
SAFE: yes/no
ISSUES: list issues or 'none'
SEVERITY: Critical/High/Medium/Low/None
RECOMMENDATION: BLOCK/REDACT/RESTRICT/ALLOW
EXPLANATION: one sentence reason"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=[{"parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": request.image_base64}},
                {"text": prompt}
            ]}]
        )
        lines  = response.text.strip().split('\n')
        parsed = {}
        for line in lines:
            if ':' in line:
                k, v = line.split(':', 1)
                parsed[k.strip()] = v.strip()

        decision    = parsed.get("RECOMMENDATION", "RESTRICT")
        severity    = parsed.get("SEVERITY", "Medium")
        issues      = parsed.get("ISSUES", "Unknown")
        explanation = parsed.get("EXPLANATION", "Image analyzed by Gemini")
        score       = {"Critical": 9.0, "High": 7.0, "Medium": 5.0, "Low": 3.0, "None": 0.0}.get(severity, 5.0)

        return {
            "log_id": 0, "input_type": "image", "decision": decision,
            "description": {"ALLOW": "Safe image.", "RESTRICT": "Potentially sensitive image.", "REDACT": "Personal data detected.", "BLOCK": "Unsafe image."}.get(decision, "Analyzed."),
            "reason": f"Image analysis: {issues}", "final_score": score,
            "scores": {"malware": 0, "sensitive": 0, "intent": score},
            "contributions": {"malware": 0, "sensitive": 0, "intent": score},
            "score_contributions": {"malware": 0, "sensitive": 0, "intent": score},
            "malware_type": "None", "malware_category": "None", "severity": severity,
            "malware_description": "Image analysis", "flags": [],
            "pii_types": [], "pii_count": 0, "pii_detected": False,
            "anonymisation_score": 100, "privacy_risk": "None",
            "intent_label": "malicious" if decision == "BLOCK" else "suspicious" if decision in ("RESTRICT", "REDACT") else "benign",
            "threat_category": issues, "intent_confidence": 0.9,
            "injection_detected": False, "injection_patterns": [],
            "explanation": ["Image analyzed by Gemini", f"Issues: {issues}", f"Severity: {severity}"],
            "response": explanation, "display_text": "[Image Input]",
            "rag_used": False, "rag_sources": [], "policy": request.policy, "role": request.role,
        }
    except Exception as e:
        return {
            "log_id": 0, "input_type": "image", "decision": "RESTRICT",
            "description": "Image analysis failed.", "reason": f"Error: {str(e)}", "final_score": 5.0,
            "scores": {"malware": 0, "sensitive": 0, "intent": 5.0},
            "contributions": {"malware": 0, "sensitive": 0, "intent": 5.0},
            "score_contributions": {"malware": 0, "sensitive": 0, "intent": 5.0},
            "malware_type": "None", "malware_category": "None", "severity": "Unknown",
            "malware_description": "Error", "flags": [], "pii_types": [], "pii_count": 0,
            "pii_detected": False, "anonymisation_score": 100, "privacy_risk": "None",
            "intent_label": "suspicious", "threat_category": "Analysis Error",
            "intent_confidence": 0.5, "injection_detected": False, "injection_patterns": [],
            "explanation": ["Image analysis failed"], "response": "Unable to analyze image.",
            "display_text": "[Image Input]", "rag_used": False, "rag_sources": [],
            "policy": request.policy, "role": request.role,
        }


@app.post("/analyze-document")
async def analyze_document(request: DocumentAnalyzeRequest, db: Session = Depends(get_db)):
    analysis = run_risk_analysis(text=request.content, policy=request.policy, role=request.role, use_rag=False)
    response = generate_response(
        display_text=analysis["display_text"], decision=analysis["decision"]["decision"],
        policy=request.policy, role=request.role, explanation=analysis["explanation"], rag_context="",
    )
    log_id = save_analysis(db, analysis, response["response"], request.policy, request.role, "document")
    result = format_response(analysis, response["response"], log_id, request.policy, request.role, "document", request.filename)
    result["word_count"] = len(request.content.split())
    result["char_count"] = len(request.content)
    return result


@app.post("/feedback")
async def feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    fb = FeedbackLog(
        analysis_id=request.analysis_id, agreed=request.agreed,
        suggested_decision=request.suggested_decision, user_comment=request.user_comment,
    )
    db.add(fb); db.commit()
    return {"success": True, "message": "Feedback recorded"}


@app.get("/logs")
async def get_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AnalysisLog).order_by(AnalysisLog.timestamp.desc()).limit(limit).all()
    return [{"id": l.id, "timestamp": l.timestamp.isoformat(), "input": l.input_text[:100],
             "role": l.role, "policy": l.policy, "score": l.final_score,
             "decision": l.decision, "malware": l.malware_type, "rag_used": l.rag_used} for l in logs]


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.query(func.count(AnalysisLog.id)).scalar()
    if total == 0:
        return {"total": 0, "decisions": {}, "avg_score": 0, "rag_count": 0, "feedback_total": 0, "feedback_agreed": 0, "agreement_rate": 0}
    decisions  = db.query(AnalysisLog.decision, func.count(AnalysisLog.id)).group_by(AnalysisLog.decision).all()
    avg_score  = db.query(func.avg(AnalysisLog.final_score)).scalar()
    rag_count  = db.query(func.count(AnalysisLog.id)).filter(AnalysisLog.rag_used == True).scalar()
    fb_total   = db.query(func.count(FeedbackLog.id)).scalar()
    fb_agreed  = db.query(func.count(FeedbackLog.id)).filter(FeedbackLog.agreed == True).scalar()
    return {
        "total": total, "decisions": {d: c for d, c in decisions},
        "avg_score": round(float(avg_score or 0), 2), "rag_count": rag_count,
        "feedback_total": fb_total, "feedback_agreed": fb_agreed,
        "agreement_rate": round((fb_agreed / fb_total * 100) if fb_total > 0 else 0, 1),
    }


@app.get("/calibrate")
async def calibrate_endpoint(
    role: str = "general",
    policy: str = "moderate",
    db: Session = Depends(get_db)
):
    from calibrate_thresholds import calibrate
    return calibrate(db, role, policy)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "model": "distilbert-base-uncased", "message": "SafeGen AI is running"}