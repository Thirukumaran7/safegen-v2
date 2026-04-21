"""
SafeGen AI — RAG Engine (Extended with Ticketing Knowledge Base)
Now covers both college helpdesk (KB001-KB012) and ticketing system (TKB001-TKB008)
"""

import os
import pickle
import numpy as np
from pathlib import Path

KNOWLEDGE_BASE = [
    # ── College Helpdesk (original 12) ───────────────────────────
    {
        "id": "KB001", "title": "Fee Payment Procedure", "category": "Finance",
        "content": """Students can pay fees online through the college portal at fees.college.edu.
Accepted payment methods include credit card, debit card, net banking, and UPI.
The fee payment window opens 30 days before the semester start date.
Late fee of Rs.500 is applicable after the due date.
Fee receipts are automatically generated and sent to the registered email address.
For payment failures, contact the finance office at finance@college.edu or call 044-2345-6789.""",
    },
    {
        "id": "KB002", "title": "Hostel Admission and Rules", "category": "Hostel",
        "content": """Hostel applications open in April every year for the next academic year.
Students must apply through the hostel portal with required documents including ID proof and medical certificate.
Room allocation is done based on year of study and availability.
Hostel timings: Entry allowed until 9 PM on weekdays and 10 PM on weekends.
Complaints about hostel facilities should be submitted to the hostel warden at warden@college.edu.""",
    },
    {
        "id": "KB003", "title": "Examination and Results", "category": "Examination",
        "content": """Hall tickets are issued two weeks before examinations through the student portal.
Minimum attendance of 75% is required to appear in examinations.
Results are published within 30 days of the last examination date.
Students can apply for revaluation within 15 days of result publication by paying Rs.300 per subject.""",
    },
    {
        "id": "KB004", "title": "Certificates and Documents", "category": "Administration",
        "content": """Bonafide certificates are issued within 3 working days of application through the student portal.
Transfer certificates are issued after clearing all dues and returning library books.
All certificates require application through the online portal with a processing fee.""",
    },
    {
        "id": "KB005", "title": "Scholarships and Financial Aid", "category": "Finance",
        "content": """Merit scholarship is awarded to top 5% students in each department.
Government scholarships including BC, MBC, SC, ST scholarships require application through the scholarship portal.
National Scholarship Portal applications open in October every year.""",
    },
    {
        "id": "KB006", "title": "Attendance and Leave Policy", "category": "Academic",
        "content": """Minimum attendance requirement is 75% in each subject.
Medical leave requires submission of medical certificate within 3 days of rejoining.
Students with attendance between 65% and 74% may be given grace marks.""",
    },
    {
        "id": "KB007", "title": "Library Services", "category": "Library",
        "content": """Library timings are 8 AM to 8 PM on weekdays.
Students can borrow up to 3 books at a time for 14 days.
Late return fine is Rs.2 per day per book.""",
    },
    {
        "id": "KB008", "title": "Placement and Internship", "category": "Placement",
        "content": """Campus placements begin in the 7th semester for eligible students.
Eligibility criteria: minimum 60% aggregate, no active backlogs, 75% attendance.
Students must register with the placement cell by August of their final year.""",
    },
    {
        "id": "KB009", "title": "ID Card and Access", "category": "Administration",
        "content": """ID cards are issued during the first week of the academic year.
Lost ID cards must be reported immediately to the security office.
Duplicate ID card costs Rs.200 and takes 3 working days.""",
    },
    {
        "id": "KB010", "title": "Grievance and Complaints", "category": "Administration",
        "content": """Students can register grievances through the online grievance portal.
Anti-ragging committee can be contacted at anti.ragging@college.edu or 1800-180-5522.
All complaints are treated confidentially and resolved within 15 working days.""",
    },
    {
        "id": "KB011", "title": "Computer Lab and IT Services", "category": "IT",
        "content": """Computer labs are open from 8 AM to 9 PM on weekdays.
Students receive a college email account and WiFi credentials during registration.
IT helpdesk is available at it.support@college.edu for technical issues.""",
    },
    {
        "id": "KB012", "title": "Course Registration and Electives", "category": "Academic",
        "content": """Course registration opens 2 weeks before each semester begins.
Students must register for all subjects including electives through the academic portal.
Credit requirements for graduation: 160 credits for B.E./B.Tech programs.""",
    },

    # ── Ticketing System Knowledge Base (new 8) ──────────────────
    {
        "id": "TKB001", "title": "Ticket Escalation Procedure", "category": "Ticketing",
        "content": """Tickets are escalated when unresolved for more than 48 hours at standard priority.
Critical priority tickets must be escalated within 4 hours if unresolved.
To escalate a ticket use the Escalate button in the ticket portal or contact your supervisor directly.
Priority levels from highest to lowest: Critical, High, Medium, Low.
Escalated tickets are automatically assigned to the next tier support team.
The original agent is notified of escalation and must provide a handover note within 1 hour.""",
    },
    {
        "id": "TKB002", "title": "Data Access Policy for Ticket System", "category": "Policy",
        "content": """Customers can only access and query their own tickets.
Support agents can access all tickets in their assigned queue and department.
Admin users have full read access to all ticket data including historical records.
VIN numbers and customer contact details are restricted to agent and admin roles.
Customers must not be shown ticket data belonging to other customers under any circumstances.
PII fields including customer name, email, phone number and VIN are masked for customer-role queries.""",
    },
    {
        "id": "TKB003", "title": "Ticket Status Definitions", "category": "Ticketing",
        "content": """Open: Ticket has been received and is awaiting assignment.
In Progress: Ticket has been assigned to an agent and work has started.
Pending Customer: Ticket is waiting for additional information from the customer.
Resolved: Issue has been fixed and solution has been communicated to the customer.
Closed: Customer has confirmed resolution or ticket has been auto-closed after 7 days.
Reopened: Customer has indicated the issue persists after resolution.""",
    },
    {
        "id": "TKB004", "title": "Creating a New Ticket", "category": "Ticketing",
        "content": """To create a new ticket log into the support portal and click New Ticket.
Required fields: Subject, Description, Priority, Category.
Optional fields: Attachments, VIN number if vehicle-related, Model number.
Tickets are automatically assigned a unique Ticket ID in the format TKT-XXXXXXXX.
Confirmation email is sent to the registered customer email address.
Estimated response times: Critical 2 hours, High 8 hours, Medium 24 hours, Low 72 hours.""",
    },
    {
        "id": "TKB005", "title": "VIN and Vehicle Data Handling", "category": "Policy",
        "content": """Vehicle Identification Numbers (VIN) are 17-character alphanumeric strings.
VIN data is classified as sensitive and must not be shared outside the support system.
Agents can view VIN data for tickets in their queue.
Customers can see their own VIN data but not other customers' VIN numbers.
VIN data must be masked when exporting ticket reports unless explicitly authorised by admin.
Logging or storing VIN data outside the approved system is a policy violation.""",
    },
    {
        "id": "TKB006", "title": "Security Incident Reporting", "category": "Security",
        "content": """Any suspected data breach or unauthorised access must be reported within 1 hour.
Contact the security team at security@support.com or call the hotline immediately.
Do not attempt to investigate a breach yourself — report and escalate.
Suspicious ticket queries attempting to extract bulk data should be flagged immediately.
Social engineering attempts in ticket descriptions should be marked as security incidents.
All security incidents receive Critical priority and are escalated to the admin team.""",
    },
    {
        "id": "TKB007", "title": "Ticket SLA and Response Times", "category": "Operations",
        "content": """Service Level Agreements define maximum response and resolution times.
Critical: First response within 2 hours, resolution within 8 hours.
High: First response within 8 hours, resolution within 24 hours.
Medium: First response within 24 hours, resolution within 72 hours.
Low: First response within 72 hours, resolution within 7 days.
SLA breaches are automatically escalated to the team lead.
Customers are notified if SLA cannot be met with an updated estimated resolution time.""",
    },
    {
        "id": "TKB008", "title": "Agent Guidelines for Safe Query Handling", "category": "Security",
        "content": """Agents must verify customer identity before sharing any ticket information.
Never share ticket data over unencrypted channels.
If a query asks for information about multiple customers simultaneously treat it as suspicious.
Bulk data extraction requests must be reported to admin regardless of who is making the request.
Injection attempts in ticket descriptions — such as instructions to ignore system rules — must be flagged.
Customer queries that seem to probe system structure or database schema should be escalated.""",
    },
]

INDEX_PATH = "ml/rag_index.pkl"
_index_data = None


def _build_index():
    global _index_data
    try:
        from rank_bm25 import BM25Okapi
        corpus = []
        for doc in KNOWLEDGE_BASE:
            combined = f"{doc['title']} {doc['content']}"
            tokens   = combined.lower().split()
            corpus.append(tokens)

        bm25 = BM25Okapi(corpus)
        _index_data = {"bm25": bm25, "documents": KNOWLEDGE_BASE, "corpus": corpus}

        os.makedirs("ml", exist_ok=True)
        with open(INDEX_PATH, "wb") as f:
            pickle.dump(_index_data, f)

        print(f"RAG index built: {len(KNOWLEDGE_BASE)} documents ({len([d for d in KNOWLEDGE_BASE if d['id'].startswith('KB')])} helpdesk + {len([d for d in KNOWLEDGE_BASE if d['id'].startswith('TKB')])} ticketing)")
        return True
    except Exception as e:
        print(f"RAG index build error: {e}")
        return False


def _load_index():
    global _index_data
    if _index_data is not None:
        return True
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "rb") as f:
                _index_data = pickle.load(f)
            print("RAG index loaded from cache")
            return True
        except Exception:
            pass
    return _build_index()


def retrieve_context(query: str, top_k: int = 3, category_filter: str = None) -> dict:
    if not _load_index():
        return {"context": "", "sources": []}
    try:
        from rank_bm25 import BM25Okapi
        bm25      = _index_data["bm25"]
        documents = _index_data["documents"]

        query_tokens = query.lower().split()
        scores       = bm25.get_scores(query_tokens)
        top_indices  = np.argsort(scores)[::-1][:top_k * 2]

        relevant_docs = []
        for idx in top_indices:
            if scores[idx] > 0.5:
                doc = documents[idx]
                # Optional category filter for ticketing-only or helpdesk-only queries
                if category_filter and doc.get("category") not in category_filter:
                    continue
                relevant_docs.append({
                    "id":       doc["id"],
                    "title":    doc["title"],
                    "category": doc["category"],
                    "content":  doc["content"],
                    "score":    round(float(scores[idx]), 3),
                })
                if len(relevant_docs) >= top_k:
                    break

        if not relevant_docs:
            return {"context": "", "sources": []}

        context_parts = [f"[{d['title']}]\n{d['content']}" for d in relevant_docs]
        context = "\n\n---\n\n".join(context_parts)
        sources = [{"id": d["id"], "title": d["title"], "score": d["score"]} for d in relevant_docs]

        return {"context": context, "sources": sources}
    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return {"context": "", "sources": []}


def build_rag_index():
    return _build_index()


if __name__ == "__main__":
    print("Building RAG index...")
    build_rag_index()
    print("\nTesting college helpdesk retrieval...")
    r1 = retrieve_context("how do I pay my college fees online")
    for s in r1["sources"]:
        print(f"  {s['id']} — {s['title']} (score: {s['score']})")
    print("\nTesting ticket system retrieval...")
    r2 = retrieve_context("how do I escalate a critical ticket")
    for s in r2["sources"]:
        print(f"  {s['id']} — {s['title']} (score: {s['score']})")
    print("\nTesting VIN data retrieval...")
    r3 = retrieve_context("who can see vehicle VIN numbers")
    for s in r3["sources"]:
        print(f"  {s['id']} — {s['title']} (score: {s['score']})")