"""
Resume Parser Service

Extracts text from a resume PDF using PyMuPDF, then calls OpenAI to
extract structured information (skills, technologies, experience level, domain).
Falls back to keyword-based extraction if OpenAI is unavailable.
"""

import json
import os
import re

import fitz  # PyMuPDF
from dotenv import load_dotenv

load_dotenv()

_client = None
_openai_available = None


def _get_client():
    """Get OpenAI client, or None if unavailable."""
    global _client, _openai_available
    if _openai_available is False:
        return None
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_key_here":
            _openai_available = False
            return None
        try:
            from openai import OpenAI
            _client = OpenAI(api_key=api_key)
            _openai_available = True
        except Exception:
            _openai_available = False
            return None
    return _client


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text content from PDF bytes using PyMuPDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def _keyword_extract(raw_text: str) -> dict:
    """
    Fallback: extract skills, technologies, experience level, and domain
    from resume text using keyword matching. No LLM required.
    """
    text_lower = raw_text.lower()

    # Skill categories
    skill_patterns = {
        "python": r"\bpython\b",
        "java": r"\bjava\b(?!\s*script)",
        "javascript": r"\bjavascript\b|\bjs\b",
        "typescript": r"\btypescript\b|\bts\b",
        "c++": r"\bc\+\+\b",
        "c#": r"\bc#\b",
        "go": r"\bgolang\b|\bgo\b",
        "rust": r"\brust\b",
        "sql": r"\bsql\b",
        "r": r"\br programming\b|\br language\b",
        "machine learning": r"\bmachine learning\b|\bml\b",
        "deep learning": r"\bdeep learning\b|\bdl\b",
        "data analysis": r"\bdata analysis\b|\bdata analytics\b",
        "computer vision": r"\bcomputer vision\b|\bcv\b",
        "nlp": r"\bnlp\b|\bnatural language processing\b",
        "statistics": r"\bstatistics\b|\bstatistical\b",
    }

    tech_patterns = {
        "tensorflow": r"\btensorflow\b",
        "pytorch": r"\bpytorch\b",
        "scikit-learn": r"\bscikit[- ]learn\b|\bsklearn\b",
        "pandas": r"\bpandas\b",
        "numpy": r"\bnumpy\b",
        "react": r"\breact\b",
        "node.js": r"\bnode\.?js\b",
        "docker": r"\bdocker\b",
        "kubernetes": r"\bkubernetes\b|\bk8s\b",
        "aws": r"\baws\b|\bamazon web services\b",
        "gcp": r"\bgcp\b|\bgoogle cloud\b",
        "azure": r"\bazure\b",
        "git": r"\bgit\b",
        "linux": r"\blinux\b",
        "flask": r"\bflask\b",
        "fastapi": r"\bfastapi\b",
        "django": r"\bdjango\b",
        "spark": r"\bspark\b|\bpyspark\b",
        "hadoop": r"\bhadoop\b",
        "mongodb": r"\bmongodb\b",
        "postgresql": r"\bpostgres(?:ql)?\b",
        "redis": r"\bredis\b",
        "kafka": r"\bkafka\b",
        "jenkins": r"\bjenkins\b",
        "ci/cd": r"\bci/?cd\b",
        "keras": r"\bkeras\b",
        "hugging face": r"\bhugging\s*face\b",
        "langchain": r"\blangchain\b",
        "openai": r"\bopenai\b",
    }

    domain_patterns = {
        "machine learning": r"\bmachine learning\b",
        "artificial intelligence": r"\bartificial intelligence\b|\bai\b",
        "data science": r"\bdata science\b",
        "web development": r"\bweb dev\b|\bfull[- ]stack\b|\bfrontend\b|\bbackend\b",
        "data engineering": r"\bdata engineering\b|\betl\b|\bdata pipeline\b",
        "devops": r"\bdevops\b|\bsite reliability\b|\bsre\b",
        "cloud computing": r"\bcloud\b",
        "mobile development": r"\bmobile\b|\bandroid\b|\bios\b|\bflutter\b",
        "software engineering": r"\bsoftware engineer\b",
    }

    skills = [name for name, pat in skill_patterns.items() if re.search(pat, text_lower)]
    technologies = [name for name, pat in tech_patterns.items() if re.search(pat, text_lower)]
    domains = [name for name, pat in domain_patterns.items() if re.search(pat, text_lower)]

    # Experience level heuristic
    experience_level = "mid"
    year_matches = re.findall(r"(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience)?", text_lower)
    if year_matches:
        max_years = max(int(y) for y in year_matches)
        if max_years <= 2:
            experience_level = "junior"
        elif max_years <= 5:
            experience_level = "mid"
        else:
            experience_level = "senior"
    elif any(w in text_lower for w in ["intern", "fresher", "entry level", "entry-level", "graduate"]):
        experience_level = "junior"
    elif any(w in text_lower for w in ["senior", "lead", "principal", "architect", "director", "manager"]):
        experience_level = "senior"

    return {
        "raw_text": raw_text,
        "skills": skills if skills else ["general programming"],
        "technologies": technologies,
        "experience_level": experience_level,
        "domain": domains if domains else ["software engineering"],
    }


def parse_resume_pdf(file_bytes: bytes) -> dict:
    """
    Parse a resume PDF and extract structured information.

    Args:
        file_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Dict with keys: raw_text, skills, technologies, experience_level, domain
    """
    # Step 1: Extract raw text
    raw_text = extract_text_from_pdf(file_bytes)

    if not raw_text:
        return {
            "raw_text": "",
            "skills": [],
            "technologies": [],
            "experience_level": "junior",
            "domain": [],
        }

    # Step 2: Try OpenAI for structured extraction
    client = _get_client()

    if client is None:
        # Fall back to keyword extraction
        return _keyword_extract(raw_text)

    prompt = f"""Analyze this resume and extract the following information. Return ONLY valid JSON with no extra text.

{{
    "skills": ["list of technical skills found"],
    "technologies": ["list of specific technologies, frameworks, tools mentioned"],
    "experience_level": "junior OR mid OR senior (based on years of experience and role seniority)",
    "domain": ["list of domains/areas of expertise, e.g., machine learning, web development, data engineering"]
}}

Resume text:
{raw_text[:4000]}"""  # Truncate to avoid token limits

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a resume parsing assistant. Extract structured information from resumes. Always return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )

        content = response.choices[0].message.content.strip()
        # Handle potential markdown code blocks
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        parsed = json.loads(content)

        return {
            "raw_text": raw_text,
            "skills": parsed.get("skills", []),
            "technologies": parsed.get("technologies", []),
            "experience_level": parsed.get("experience_level", "mid"),
            "domain": parsed.get("domain", []),
        }

    except Exception:
        # Fallback to keyword extraction
        return _keyword_extract(raw_text)
