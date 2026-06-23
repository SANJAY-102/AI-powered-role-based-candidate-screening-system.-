"""
RAG Question Generator

Calls OpenAI gpt-3.5-turbo to generate adaptive, RAG-grounded interview questions.
When OpenAI is not available, falls back to intelligent template-based question
generation from FAISS knowledge chunks.

Supports difficulty adaptation based on experience level and passes previous Q&A
for adaptive follow-up questioning.
"""

import json
import os
import re
import random

from dotenv import load_dotenv

load_dotenv()

_client = None
_openai_available = None


def _get_client():
    """Get the OpenAI client, or None if unavailable."""
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


# ---------------------------------------------------------------------------
# Fallback: template-based question generation from knowledge chunks
# ---------------------------------------------------------------------------

QUESTION_TEMPLATES = {
    "junior": [
        "Can you explain what {concept} is and why it is important in {domain}?",
        "What is the purpose of {concept}? Describe it in simple terms.",
        "How does {concept} work at a high level?",
        "What are the key characteristics of {concept}?",
        "Describe the difference between {concept} and {concept2}.",
        "What problem does {concept} solve?",
        "In the context of {domain}, what role does {concept} play?",
    ],
    "mid": [
        "Compare and contrast {concept} with {concept2}. When would you choose one over the other?",
        "Walk me through how {concept} works under the hood and discuss its trade-offs.",
        "How would you apply {concept} in a real-world {domain} project? What challenges might arise?",
        "What are the advantages and limitations of using {concept}?",
        "Explain the relationship between {concept} and {concept2} in practice.",
        "How does {concept} handle edge cases or failure modes?",
        "Describe a scenario where {concept} would be the wrong choice and explain why.",
    ],
    "senior": [
        "How would you design a production system using {concept}? Discuss scalability, monitoring, and failure recovery.",
        "Critique the use of {concept} versus {concept2} for a large-scale {domain} system. What architectural trade-offs exist?",
        "If you had to optimize {concept} for a system handling millions of requests, what changes would you make?",
        "Discuss the theoretical foundations of {concept} and how they inform practical implementation decisions.",
        "How has {concept} evolved over the past few years, and what are its current limitations in the context of {domain}?",
        "Design an experiment to evaluate whether {concept} or {concept2} would perform better for a given problem.",
    ],
}

# Concept extraction patterns — keywords that indicate technical concepts
CONCEPT_INDICATORS = [
    # ML/AI
    r"(?:linear|logistic|ridge|lasso)\s+regression",
    r"decision\s+trees?",
    r"random\s+forests?",
    r"gradient\s+(?:descent|boosting)",
    r"neural\s+networks?",
    r"backpropagation",
    r"convolutional\s+neural\s+networks?",
    r"recurrent\s+neural\s+networks?",
    r"(?:long\s+short[- ]term\s+memory|lstm)",
    r"(?:gated\s+recurrent\s+units?|gru)",
    r"transformers?",
    r"self[- ]attention",
    r"(?:relu|sigmoid|softmax|tanh)",
    r"batch\s+normalization",
    r"dropout",
    r"(?:adam|sgd|momentum)\s*(?:optimizer)?",
    r"cross[- ]validation",
    r"(?:precision|recall|f1[- ]score|accuracy|roc[- ]auc)",
    r"confusion\s+matrix",
    r"overfitting",
    r"underfitting",
    r"bias[- ]variance\s+trade[- ]?off",
    r"regularization",
    r"(?:k[- ]means|dbscan)\s*(?:clustering)?",
    r"(?:pca|principal\s+component\s+analysis)",
    r"t[- ]sne",
    r"(?:word2vec|glove|word\s+embeddings?)",
    r"(?:bert|gpt)\b",
    r"tf[- ]idf",
    r"bag\s+of\s+words",
    r"mean\s+squared\s+error",
    r"feature\s+(?:engineering|selection|importance)",
    r"ensemble\s+(?:methods?|learning)",
    r"hyperparameter\s+tuning",
    r"(?:gini\s+impurity|information\s+gain|entropy)",
    r"(?:bagging|boosting)",
    r"(?:cnn|rnn)s?\b",
    r"pooling\s+layers?",
    r"(?:resnet|alexnet|vgg)",
    r"learning\s+rate",
    r"activation\s+functions?",
    r"cost\s+function",
    r"loss\s+function",
]


def _extract_concepts(text: str) -> list[str]:
    """Extract technical concepts from a text chunk."""
    concepts = set()
    text_lower = text.lower()
    for pattern in CONCEPT_INDICATORS:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            concepts.add(m.strip())

    # Also extract capitalized multi-word terms (likely proper nouns / method names)
    caps = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text)
    for c in caps:
        if len(c) > 5:
            concepts.add(c)

    return list(concepts) if concepts else ["the core concepts discussed"]


PERSONALITY_GUIDANCE = {
    "Professional Mentor": "Adopt a warm, encouraging, and mentoring tone. Frame your questions to draw out the candidate's strengths and support their learning journey while still validating technical capabilities.",
    "Rude Stress Interviewer": "Adopt a demanding, skeptical, and slightly intense tone. Frame questions aggressively, questioning common assumptions, asking for justification of design choices, and probing how they handle trade-offs and high-pressure production failures.",
    "Academic Professor": "Adopt a highly rigorous, formal, and academic tone. Focus heavily on theoretical concepts, mathematical principles, algorithmic efficiency, underlying assumptions, and precise scientific definitions."
}

FALLBACK_TEMPLATES_BY_PERSONALITY = {
    "Professional Mentor": {
        "junior": [
            "I'd love to hear your thoughts: can you explain what {concept} is and why it's so helpful in {domain}?",
            "Could you walk me through the basic purpose of {concept} in friendly terms?",
            "How does {concept} work at a high level? What do you like about it?",
            "What would you say are the most exciting characteristics of {concept}?"
        ],
        "mid": [
            "If you were helping a colleague, how would you describe the trade-offs of {concept} compared to {concept2}?",
            "Could you share a practical example of how you'd apply {concept} in a real-world {domain} scenario?",
            "What have you found to be the main advantages and learning curves when working with {concept}?"
        ],
        "senior": [
            "In your experience, how would we design a scalable production system using {concept}? What tips would you give the team?",
            "If we had to improve the performance of {concept} for a large service, what approach would you suggest we explore?"
        ]
    },
    "Rude Stress Interviewer": {
        "junior": [
            "Explain exactly what {concept} is, and don't give me a generic definition. Why does it matter in {domain}?",
            "What problem does {concept} actually solve, or is it just overhyped?",
            "Describe how {concept} works under the hood. Avoid the high-level fluff."
        ],
        "mid": [
            "Why would any competent engineer choose {concept} over {concept2}? Convince me with trade-offs.",
            "Tell me about a time you tried to use {concept} in {domain} and it failed catastrophically. What went wrong?",
            "What are the major limitations of {concept} that most tutorials conveniently ignore?"
        ],
        "senior": [
            "Design a system with {concept} that won't fall apart under load. How do you handle failure recovery when it crashes?",
            "Critique {concept} versus {concept2} for massive scale. What architectural compromises are you forced to make?"
        ]
    },
    "Academic Professor": {
        "junior": [
            "Formally define the concept of {concept} and outline its theoretical role within {domain}.",
            "What is the mathematical or conceptual purpose of {concept}?",
            "Outline the foundational mechanisms by which {concept} operates."
        ],
        "mid": [
            "Contrast the theoretical assumptions of {concept} with those of {concept2}. When is one mathematically preferred?",
            "Discuss the analytical formulation of {concept} and describe its computational complexity.",
            "Explain the systemic relationship between {concept} and {concept2} in statistical methodology."
        ],
        "senior": [
            "Provide a rigorous system design utilizing {concept}, specifying constraints on consistency, latency, and convergence.",
            "Deduce the optimization limits of {concept} when scale approaches infinity. What theoretical trade-offs govern this?"
        ]
    }
}


def _generate_fallback_questions(
    skills: list[str],
    role: str,
    retrieved_chunks: list[dict],
    previous_qa: list[dict] | None = None,
    count: int = 1,
    experience_level: str = "mid",
    personality: str = "Professional Mentor",
) -> list[dict]:
    """Generate questions from knowledge chunks using templates (no OpenAI needed)."""
    # Select templates based on personality and experience
    personality_templates = FALLBACK_TEMPLATES_BY_PERSONALITY.get(
        personality, FALLBACK_TEMPLATES_BY_PERSONALITY["Professional Mentor"]
    )
    templates = personality_templates.get(experience_level, personality_templates["mid"])

    # Gather previous questions to avoid duplicates
    asked = set()
    if previous_qa:
        for qa in previous_qa:
            asked.add(qa.get("question", "").lower().strip())

    # Domain from role
    domain = role if role else "software engineering"

    results = []
    # Shuffle chunks for variety across calls
    chunks = list(retrieved_chunks)
    random.shuffle(chunks)

    for chunk in chunks:
        if len(results) >= count:
            break

        chunk_text = chunk.get("text", "")
        concepts = _extract_concepts(chunk_text)

        if not concepts:
            continue

        random.shuffle(concepts)
        concept = concepts[0]
        concept2 = concepts[1] if len(concepts) > 1 else concepts[0]

        # Try templates until we find one we haven't asked
        random.shuffle(templates)
        for tmpl in templates:
            question = tmpl.format(
                concept=concept,
                concept2=concept2,
                domain=domain,
            )
            if question.lower().strip() not in asked:
                results.append({
                    "question": question,
                    "source_chunk": chunk_text[:100],
                })
                asked.add(question.lower().strip())
                break

    # If we still don't have enough, add generic questions
    if not results:
        results.append({
            "question": f"Based on your experience with {', '.join(skills[:3])}, explain a concept you find fundamental to the role of {role}.",
            "source_chunk": retrieved_chunks[0]["text"][:100] if retrieved_chunks else "",
        })

    return results[:count]


def generate_questions(
    skills: list[str],
    role: str,
    retrieved_chunks: list[dict],
    previous_qa: list[dict] | None = None,
    count: int = 1,
    experience_level: str = "mid",
    personality: str = "Professional Mentor",
) -> list[dict]:
    """
    Generate interview questions using OpenAI, grounded in retrieved knowledge chunks.
    Falls back to template-based generation if OpenAI is not available.

    Args:
        skills: Candidate's extracted skills from resume.
        role: Target role (e.g., "AI/ML Engineer").
        retrieved_chunks: Knowledge base chunks from FAISS retriever.
        previous_qa: Previous questions and answers for adaptive questioning.
        count: Number of questions to generate.
        experience_level: junior/mid/senior -- calibrates question difficulty.
        personality: Professional Mentor / Rude Stress Interviewer / Academic Professor.

    Returns:
        List of dicts: [{"question": "...", "source_chunk": "..."}]
    """
    client = _get_client()

    # Fallback to template-based generation
    if client is None:
        return _generate_fallback_questions(
            skills=skills,
            role=role,
            retrieved_chunks=retrieved_chunks,
            previous_qa=previous_qa,
            count=count,
            experience_level=experience_level,
            personality=personality,
        )

    # ---- OpenAI path ----
    # Build knowledge context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        context_parts.append(
            f"[Chunk {i} -- Source: {chunk.get('source', 'unknown')}]\n{chunk['text']}"
        )
    knowledge_context = "\n\n".join(context_parts)

    # Build previous Q&A context for adaptive questioning
    prev_qa_text = ""
    if previous_qa:
        qa_parts = []
        for qa in previous_qa:
            answer_text = qa.get("answer", "No answer provided")
            qa_parts.append(
                f"Q: {qa['question']}\nA: {answer_text}"
            )
        prev_qa_text = "\n\n".join(qa_parts)

    # Difficulty calibration
    difficulty_guidance = {
        "junior": "Ask foundational questions that test basic understanding of concepts. Use simpler terminology and focus on definitions, basic applications, and straightforward scenarios.",
        "mid": "Ask intermediate questions that test practical understanding and ability to apply concepts. Include some trade-off analysis and design considerations.",
        "senior": "Ask advanced questions that test deep understanding, system design thinking, and ability to critique approaches. Include questions about scalability, edge cases, and architectural decisions.",
    }
    difficulty_text = difficulty_guidance.get(experience_level, difficulty_guidance["mid"])

    personality_text = PERSONALITY_GUIDANCE.get(personality, PERSONALITY_GUIDANCE["Professional Mentor"])

    system_prompt = f"""You are a technical interviewer for a {role} position.
Your interviewing style matches this persona: {personality}.
Guidance for your persona: {personality_text}

Generate exactly {count} interview question(s) that:
1. Are grounded in the provided knowledge base context -- do NOT ask generic questions
2. Test genuine conceptual understanding, not just recall
3. Are specific and targeted -- reference particular concepts, algorithms, or techniques from the context
4. Are different from any previously asked questions

Difficulty level: {experience_level}
{difficulty_text}

CRITICAL RULES:
- Each question MUST be traceable to a specific chunk from the knowledge context
- Do NOT repeat or rephrase any previously asked questions
- If previous answers were shallow, probe deeper on that topic
- If previous answers were strong, move to a different topic area

Return ONLY a valid JSON array with no extra text:
[{{"question": "Your specific question here", "source_chunk": "First 80 characters of the chunk used..."}}]"""

    user_prompt_parts = [
        f"Candidate Skills: {', '.join(skills)}",
        f"Target Role: {role}",
        f"\n--- Knowledge Base Context ---\n{knowledge_context}",
    ]
    if prev_qa_text:
        user_prompt_parts.append(
            f"\n--- Previous Interview Q&A (for adaptive follow-up) ---\n{prev_qa_text}"
        )

    user_prompt = "\n\n".join(user_prompt_parts)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        content = response.choices[0].message.content.strip()
        # Parse JSON -- handle potential markdown code blocks
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        questions = json.loads(content)

        # Validate structure
        validated = []
        for q in questions:
            if isinstance(q, dict) and "question" in q:
                validated.append({
                    "question": q["question"],
                    "source_chunk": q.get("source_chunk", "")[:100],
                })
        return validated if validated else [{"question": "Could not generate a valid question. Please try again.", "source_chunk": ""}]

    except json.JSONDecodeError:
        # Fallback: try to extract question from plain text
        return [{"question": content if content else "Error generating question.", "source_chunk": ""}]
    except Exception:
        # On any OpenAI error, fall back to template-based generation
        return _generate_fallback_questions(
            skills=skills,
            role=role,
            retrieved_chunks=retrieved_chunks,
            previous_qa=previous_qa,
            count=count,
            experience_level=experience_level,
        )


def score_answer(
    question: str,
    answer: str,
    source_chunk: str,
    role: str,
) -> dict:
    """
    Score a candidate's answer against the source chunk.
    Falls back to keyword-matching heuristic if OpenAI is unavailable.

    Returns:
        Dict with score (1-5) and brief feedback.
    """
    client = _get_client()

    if client is None:
        return _score_answer_fallback(question, answer, source_chunk)

    system_prompt = f"""You are evaluating a {role} candidate's interview answer.
Score the answer from 1-5 based on:
1 = Completely wrong or irrelevant
2 = Shows minimal understanding, mostly incorrect
3 = Partially correct, missing key concepts
4 = Good understanding, covers main points
5 = Excellent, demonstrates deep understanding

Return ONLY valid JSON: {{"score": <1-5>, "feedback": "Brief explanation"}}"""

    user_prompt = f"""Question: {question}

Reference knowledge (source chunk):
{source_chunk}

Candidate's answer:
{answer}"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        result = json.loads(content)
        return {
            "score": max(1, min(5, int(result.get("score", 3)))),
            "feedback": result.get("feedback", ""),
        }
    except Exception:
        return _score_answer_fallback(question, answer, source_chunk)


def _score_answer_fallback(question: str, answer: str, source_chunk: str) -> dict:
    """
    Heuristic-based answer scoring using keyword overlap with the source chunk.
    No LLM required.
    """
    if not answer or not answer.strip():
        return {"score": 1, "feedback": "No answer was provided."}

    answer_lower = answer.lower()
    answer_words = set(re.findall(r"\b[a-z]{3,}\b", answer_lower))
    chunk_lower = source_chunk.lower() if source_chunk else ""
    chunk_words = set(re.findall(r"\b[a-z]{3,}\b", chunk_lower))
    question_lower = question.lower()
    question_words = set(re.findall(r"\b[a-z]{3,}\b", question_lower))

    # Remove common stop words
    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can", "has",
        "her", "was", "one", "our", "out", "how", "its", "may", "use", "way",
        "about", "above", "after", "again", "been", "before", "being", "below",
        "between", "both", "could", "does", "doing", "down", "during", "each",
        "from", "further", "have", "having", "here", "into", "just", "more",
        "most", "other", "over", "same", "should", "some", "such", "than",
        "that", "their", "them", "then", "there", "these", "they", "this",
        "those", "through", "under", "very", "what", "when", "where", "which",
        "while", "with", "would", "your",
    }
    answer_words -= stop_words
    chunk_words -= stop_words
    question_words -= stop_words

    if not chunk_words:
        # No source chunk to compare against
        word_count = len(answer.split())
        if word_count < 10:
            return {"score": 2, "feedback": "Answer is too brief to evaluate thoroughly."}
        elif word_count < 30:
            return {"score": 3, "feedback": "Answer has some content. More detail would strengthen it."}
        else:
            return {"score": 4, "feedback": "Answer shows reasonable depth."}

    # Calculate keyword overlap
    relevant_chunk_words = chunk_words - question_words  # concepts beyond the question itself
    if not relevant_chunk_words:
        relevant_chunk_words = chunk_words

    overlap = answer_words & relevant_chunk_words
    overlap_ratio = len(overlap) / max(len(relevant_chunk_words), 1)

    # Length factor
    word_count = len(answer.split())
    length_bonus = min(word_count / 50, 1.0)  # cap at 50 words

    # Combined score
    raw_score = (overlap_ratio * 3.5) + (length_bonus * 1.5)
    score = max(1, min(5, round(raw_score + 0.5)))

    feedback_map = {
        1: "The answer does not address key concepts from the knowledge base.",
        2: "The answer touches on the topic but misses important details.",
        3: "The answer covers some relevant points but could go deeper.",
        4: "Good answer that covers the main concepts well.",
        5: "Excellent answer demonstrating strong understanding of the material.",
    }

    return {
        "score": score,
        "feedback": feedback_map.get(score, "Answer evaluated."),
    }
