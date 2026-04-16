"""
SafeGen AI v2 — RAG Engine
College/University Helpdesk Knowledge Base
Hybrid retrieval: FAISS (dense) + BM25 (sparse)
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path

# ── Knowledge Base Documents ──────────────────────────────────────

KNOWLEDGE_BASE = [
    {
        "id": "KB001",
        "title": "Fee Payment Procedure",
        "category": "Finance",
        "content": """Students can pay fees online through the college portal at fees.college.edu.
Accepted payment methods include credit card, debit card, net banking, and UPI.
The fee payment window opens 30 days before the semester start date.
Late fee of Rs.500 is applicable after the due date.
Students facing financial difficulties can apply for installment plans through the finance office.
Fee receipts are automatically generated and sent to the registered email address.
For payment failures, contact the finance office at finance@college.edu or call 044-2345-6789.""",
    },
    {
        "id": "KB002",
        "title": "Hostel Admission and Rules",
        "category": "Hostel",
        "content": """Hostel applications open in April every year for the next academic year.
Students must apply through the hostel portal with required documents including ID proof and medical certificate.
Room allocation is done based on year of study and availability.
Hostel timings: Entry allowed until 9 PM on weekdays and 10 PM on weekends.
Guests are allowed in the common area only between 10 AM and 6 PM.
Mess food is provided three times daily. Menu changes weekly.
Complaints about hostel facilities should be submitted to the hostel warden at warden@college.edu.
Room changes can be requested once per semester through the hostel office.""",
    },
    {
        "id": "KB003",
        "title": "Examination and Results",
        "category": "Examination",
        "content": """Hall tickets are issued two weeks before examinations through the student portal.
Students must carry their hall ticket and college ID card to the examination hall.
Minimum attendance of 75% is required to be eligible to appear in examinations.
Results are published within 30 days of the last examination date on the results portal.
Students can apply for revaluation within 15 days of result publication by paying Rs.300 per subject.
Grace marks of up to 5 marks per subject may be awarded to students with attendance between 65% and 74%.
Examination timetable is published on the college website 6 weeks before exams.""",
    },
    {
        "id": "KB004",
        "title": "Certificates and Documents",
        "category": "Administration",
        "content": """Bonafide certificates are issued within 3 working days of application through the student portal.
Transfer certificates are issued after clearing all dues and returning library books.
Migration certificates are issued for students moving to other universities.
Consolidated marksheets are available after course completion.
All certificates require application through the online portal with a processing fee.
Attested copies of documents can be obtained from the administrative office.
Original certificates are issued only after verification of dues clearance.
Emergency bonafide certificates can be issued on the same day with valid reason.""",
    },
    {
        "id": "KB005",
        "title": "Scholarships and Financial Aid",
        "category": "Finance",
        "content": """Merit scholarship is awarded to top 5% students in each department based on previous semester performance.
Government scholarships including BC, MBC, SC, ST scholarships require application through the scholarship portal.
National Scholarship Portal applications open in October every year.
Post-matric scholarship applications must be submitted with income certificate and community certificate.
Educational loans are facilitated through partner banks. Contact the finance office for details.
Students can apply for fee waiver in case of genuine financial hardship with supporting documents.
Scholarship disbursement happens directly to the student's bank account within 60 days of approval.""",
    },
    {
        "id": "KB006",
        "title": "Attendance and Leave Policy",
        "category": "Academic",
        "content": """Minimum attendance requirement is 75% in each subject to appear in semester examinations.
Medical leave requires submission of medical certificate within 3 days of rejoining.
Students with attendance between 65% and 74% may be given grace marks at the discretion of the principal.
Attendance below 65% results in detention and the student must repeat the semester.
On-duty leave is granted for students participating in sports, cultural events, or industrial visits.
Leave application must be submitted in advance through the student portal or physically to the faculty advisor.
Biometric attendance is mandatory for all registered students.""",
    },
    {
        "id": "KB007",
        "title": "Library Services",
        "category": "Library",
        "content": """Library timings are 8 AM to 8 PM on weekdays and 9 AM to 5 PM on Saturdays.
Students can borrow up to 3 books at a time for a period of 14 days.
Books can be renewed online through the library portal if not reserved by another student.
Late return fine is Rs.2 per day per book.
Access to digital resources including IEEE Xplore, Springer, and JSTOR is available through the library portal.
Reference books and journals cannot be taken outside the library.
Interlibrary loan facility is available for research scholars.
Lost books must be replaced with a new copy of the same edition.""",
    },
    {
        "id": "KB008",
        "title": "Placement and Internship",
        "category": "Placement",
        "content": """Campus placements begin in the 7th semester for eligible students.
Eligibility criteria: minimum 60% aggregate, no active backlogs, 75% attendance.
Students must register with the placement cell by August of their final year.
Internships during semester break can be arranged through the placement cell or independently.
Internship completion certificate from the company is required for credit transfer.
Mock interviews and aptitude training are conducted throughout the academic year.
Students placed through campus drives are not eligible to attend further drives from other companies.
Contact placement cell at placement@college.edu for any queries.""",
    },
    {
        "id": "KB009",
        "title": "ID Card and Access",
        "category": "Administration",
        "content": """ID cards are issued during the first week of the academic year.
Lost ID cards must be reported immediately to the security office.
Duplicate ID card costs Rs.200 and takes 3 working days to process.
ID card is mandatory for entry into campus, library, labs, and examination halls.
ID card must be worn visibly while on campus at all times.
Damaged ID cards can be replaced at the administrative office with the old card.
Temporary gate passes are available for students who have forgotten their ID card.""",
    },
    {
        "id": "KB010",
        "title": "Grievance and Complaints",
        "category": "Administration",
        "content": """Students can register grievances through the online grievance portal at grievance.college.edu.
The grievance cell meets every Monday to review and address complaints.
Academic grievances should first be addressed to the faculty concerned, then the HOD, then the grievance cell.
Anti-ragging committee can be contacted at anti.ragging@college.edu or the national helpline 1800-180-5522.
Sexual harassment complaints should be addressed to the Internal Complaints Committee.
All complaints are treated confidentially and resolved within 15 working days.
Students can also drop written complaints in the grievance box located at the administrative block.""",
    },
    {
        "id": "KB011",
        "title": "Computer Lab and IT Services",
        "category": "IT",
        "content": """Computer labs are open from 8 AM to 9 PM on weekdays.
Students receive a college email account and WiFi credentials during registration.
College WiFi is available across campus including hostels.
Software installation requests must be submitted to the IT department.
Personal devices can be connected to college WiFi after MAC address registration.
Data usage is monitored and restricted to academic purposes only.
IT helpdesk is available at it.support@college.edu for technical issues.
Printing facility is available in the library and IT department at Rs.1 per page.""",
    },
    {
        "id": "KB012",
        "title": "Course Registration and Electives",
        "category": "Academic",
        "content": """Course registration opens 2 weeks before each semester begins.
Students must register for all subjects including electives through the academic portal.
Elective subjects are offered based on minimum enrollment of 20 students.
Change of elective is allowed within the first week of the semester.
Open electives allow students to take subjects from other departments.
Credit requirements for graduation: 160 credits for B.E./B.Tech programs.
Students can apply for additional courses beyond the required curriculum for extra credits.
Course registration issues should be reported to the academic section immediately.""",
    },
]

# ── RAG Engine ────────────────────────────────────────────────────

INDEX_PATH = "ml/rag_index.pkl"

_index_data = None


def _build_index():
    """Build BM25 index from knowledge base documents."""
    global _index_data

    try:
        from rank_bm25 import BM25Okapi

        corpus = []
        for doc in KNOWLEDGE_BASE:
            combined = f"{doc['title']} {doc['content']}"
            tokens   = combined.lower().split()
            corpus.append(tokens)

        bm25 = BM25Okapi(corpus)

        _index_data = {
            "bm25":      bm25,
            "documents": KNOWLEDGE_BASE,
            "corpus":    corpus,
        }

        # Save index
        os.makedirs("ml", exist_ok=True)
        with open(INDEX_PATH, "wb") as f:
            pickle.dump(_index_data, f)

        print(f"RAG index built: {len(KNOWLEDGE_BASE)} documents")
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


def retrieve_context(query: str, top_k: int = 3) -> dict:
    """
    Retrieve relevant documents for a query using BM25.
    Returns top_k most relevant documents.
    """
    if not _load_index():
        return {"context": "", "sources": []}

    try:
        from rank_bm25 import BM25Okapi

        bm25      = _index_data["bm25"]
        documents = _index_data["documents"]

        query_tokens = query.lower().split()
        scores       = bm25.get_scores(query_tokens)

        # Get top_k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Filter by minimum score threshold
        relevant_docs = []
        for idx in top_indices:
            if scores[idx] > 0.5:
                relevant_docs.append({
                    "id":       documents[idx]["id"],
                    "title":    documents[idx]["title"],
                    "category": documents[idx]["category"],
                    "content":  documents[idx]["content"],
                    "score":    round(float(scores[idx]), 3),
                })

        if not relevant_docs:
            return {"context": "", "sources": []}

        # Build context string
        context_parts = []
        for doc in relevant_docs:
            context_parts.append(f"[{doc['title']}]\n{doc['content']}")

        context = "\n\n---\n\n".join(context_parts)
        sources = [{"id": d["id"], "title": d["title"], "score": d["score"]} for d in relevant_docs]

        return {
            "context": context,
            "sources": sources,
        }

    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return {"context": "", "sources": []}


def build_rag_index():
    """Public function to rebuild the RAG index."""
    return _build_index()


if __name__ == "__main__":
    print("Building RAG index...")
    build_rag_index()
    print("\nTesting retrieval...")
    result = retrieve_context("how do I pay my college fees online")
    print(f"Sources found: {len(result['sources'])}")
    for src in result["sources"]:
        print(f"  - {src['title']} (score: {src['score']})")
    print("\nContext preview:")
    print(result["context"][:300])