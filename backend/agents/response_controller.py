"""
SafeGen AI v2 — Response Controller Agent
Agent 2: Generates calibrated response using Gemini API
System prompts enforce decision-appropriate responses
"""

import os
from dotenv import load_dotenv
load_dotenv()

try:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

GEMINI_MODEL = "gemini-2.0-flash-lite"

SYSTEM_PROMPTS = {
    "ALLOW": """You are a helpful university helpdesk assistant. The student's request has been reviewed and approved as safe.
Respond helpfully, clearly, and completely. Use the retrieved knowledge base context if provided to give accurate information.
If context is provided, base your answer on it. If not, answer from general knowledge.""",

    "RESTRICT": """You are a careful university helpdesk assistant. This request has been flagged as potentially risky.
You must respond at a HIGH LEVEL ONLY — no specific technical details, no step-by-step instructions, no actionable guidance on harmful topics.
Acknowledge the topic briefly and explain that detailed guidance cannot be provided for safety reasons.
Keep your response to 3-4 sentences maximum.""",

    "REDACT": """You are a careful university helpdesk assistant. Sensitive personal data was detected in this message and has been masked.
Address the general topic only — do not reference or repeat any personal data you may see in the message.
Remind the user not to share sensitive information such as passwords, API keys, or personal identifiers with AI systems.
Keep your response brief and general.""",

    "BLOCK": """You are a safety-focused university helpdesk assistant. This request has been blocked because it violates the safety policy.
Firmly but politely decline to help. Do not provide any information related to the request.
Explain briefly that this type of request cannot be assisted with through this system.
Keep your response to 2-3 sentences maximum. Do not suggest alternative ways to achieve the harmful goal.""",
}

FALLBACK_RESPONSES = {
    "ALLOW":    "Thank you for your query. I am happy to help with your question. Please feel free to provide more details if needed.",
    "RESTRICT": "I can only provide general information on this topic. Detailed guidance cannot be provided as this request has been flagged by the safety system. Please consult the appropriate college authority for specific assistance.",
    "REDACT":   "Sensitive data was detected in your message and has been masked. Please avoid sharing personal information such as passwords, API keys, or ID numbers with AI systems.",
    "BLOCK":    "This request has been blocked by the safety system as it violates usage policy. I am unable to assist with this type of request. Please contact the college administration if you have a legitimate need.",
}


def generate_response(
    display_text: str,
    decision:     str,
    policy:       str,
    role:         str,
    explanation:  list,
    rag_context:  str = "",
) -> dict:

    system_prompt = SYSTEM_PROMPTS.get(decision, SYSTEM_PROMPTS["RESTRICT"])

    # Build full prompt
    context_section = ""
    if rag_context and decision in ("ALLOW", "RESTRICT"):
        context_section = f"\n\nRelevant knowledge base context:\n{rag_context}\n"

    full_prompt = f"""{system_prompt}
{context_section}
User role: {role}
Policy level: {policy}
Safety decision: {decision}

User message: {display_text}

Respond appropriately based on the safety decision above."""

    if not GEMINI_AVAILABLE:
        return {
            "response": FALLBACK_RESPONSES.get(decision, "Unable to process this request."),
            "model":    "fallback",
            "success":  False,
            "error":    "Gemini API not available",
        }

    try:
        response = client.models.generate_content(
            model    = GEMINI_MODEL,
            contents = full_prompt,
        )
        return {
            "response": response.text,
            "model":    GEMINI_MODEL,
            "success":  True,
        }

    except Exception as e:
        print(f"Gemini error: {e}")
        return {
            "response": FALLBACK_RESPONSES.get(decision, "Unable to process this request."),
            "model":    "fallback",
            "success":  False,
            "error":    str(e),
        }