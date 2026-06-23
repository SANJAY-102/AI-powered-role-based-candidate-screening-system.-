import { useState, useEffect, useRef } from 'react'
import api from '../api/client'

const LOADING_STEPS = [
  { text: 'Constructing retrieval query...', icon: '🔍' },
  { text: 'Scanning FAISS vector index...', icon: '📚' },
  { text: 'Retrieving semantic chunks...', icon: '⚡' },
  { text: 'Calibrating difficulty...', icon: '🎯' },
  { text: 'Generating question via GPT...', icon: '✨' },
]

// ─── Typewriter ──────────────────────────────────────────────────────────────
function Typewriter({ text, speed = 14, onComplete }) {
  const [displayed, setDisplayed] = useState('')
  const idx = useRef(0)
  const timer = useRef(null)

  useEffect(() => {
    setDisplayed('')
    idx.current = 0
    if (timer.current) clearInterval(timer.current)
    if (!text) return
    timer.current = setInterval(() => {
      if (idx.current < text.length) {
        setDisplayed(prev => prev + text.charAt(idx.current))
        idx.current++
      } else {
        clearInterval(timer.current)
        onComplete?.()
      }
    }, speed)
    return () => { if (timer.current) clearInterval(timer.current) }
  }, [text, speed])

  return <span className="cursor-blink">{displayed}</span>
}

// ─── Icons ───────────────────────────────────────────────────────────────────
const MicIcon = ({ active }) => (
  <svg className="w-4 h-4" fill={active ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
  </svg>
)

const SpeakerIcon = ({ muted }) => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    {muted ? (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15zm10-10l4 4m0-4l-4 4" />
    ) : (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
    )}
  </svg>
)

const SendIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
  </svg>
)

// ─── Score Toast ─────────────────────────────────────────────────────────────
function ScoreToast({ score, feedback }) {
  const config = {
    5: { color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'Excellent!' },
    4: { color: 'text-teal-700', bg: 'bg-teal-50', border: 'border-teal-200', label: 'Good' },
    3: { color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', label: 'Fair' },
    2: { color: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-200', label: 'Basic' },
    1: { color: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200', label: 'Needs Work' },
  }[score] || { color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200', label: 'Scored' }

  return (
    <div className={`toast border ${config.border} animate-slide-down`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 w-11 h-11 rounded-xl ${config.bg} border ${config.border} flex flex-col items-center justify-center`}>
          <span className={`text-lg font-black font-display ${config.color}`}>{score}</span>
          <span className="text-[9px] text-gray-400 font-semibold">/5</span>
        </div>
        <div className="flex-1 min-w-0 pt-0.5">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold font-display ${config.color}`}>{config.label}</span>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed line-clamp-3">{feedback}</p>
        </div>
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function InterviewScreen({ sessionId, role, skills, setScreen, enableTTS, enableSTT }) {
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [questionNumber, setQuestionNumber] = useState(0)
  const [totalQuestions, setTotalQuestions] = useState(5)
  const [loading, setLoading] = useState(true)
  const [loadingStepIdx, setLoadingStepIdx] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [lastScore, setLastScore] = useState(null)
  const [showScore, setShowScore] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [typewriterDone, setTypewriterDone] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef(null)
  const textareaRef = useRef(null)

  // Loading step cycler
  useEffect(() => {
    let interval
    if (loading) {
      setLoadingStepIdx(0)
      interval = setInterval(() => {
        setLoadingStepIdx(prev => (prev + 1) % LOADING_STEPS.length)
      }, 900)
    }
    return () => clearInterval(interval)
  }, [loading])

  // STT Setup
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SR && enableSTT) {
      const rec = new SR()
      rec.continuous = true; rec.interimResults = true; rec.lang = 'en-US'
      rec.onresult = event => {
        let final = ''
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) final += event.results[i][0].transcript + ' '
        }
        if (final) setAnswer(prev => prev + final)
      }
      rec.onerror = () => setIsListening(false)
      rec.onend = () => setIsListening(false)
      recognitionRef.current = rec
    }
    return () => recognitionRef.current?.abort()
  }, [enableSTT])

  const toggleListening = () => {
    if (!recognitionRef.current) { setError('Speech recognition not supported or enabled in this browser.'); return }
    if (isListening) { recognitionRef.current.stop(); setIsListening(false) }
    else { setError(''); setIsListening(true); try { recognitionRef.current.start() } catch { setIsListening(false) } }
  }

  const speakQuestion = txt => {
    if (!enableTTS || !window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(txt)
    u.rate = 1.05; u.pitch = 1.0
    u.onstart = () => setIsSpeaking(true)
    u.onend = () => setIsSpeaking(false)
    u.onerror = () => setIsSpeaking(false)
    window.speechSynthesis.speak(u)
  }

  const toggleMuteTTS = () => {
    if (isSpeaking) { window.speechSynthesis.cancel(); setIsSpeaking(false) }
    else if (question?.question) speakQuestion(question.question)
  }

  useEffect(() => () => { window.speechSynthesis?.cancel() }, [])

  const fetchQuestion = async () => {
    setLoading(true); setError(''); setLastScore(null); setShowScore(false); setTypewriterDone(false)
    window.speechSynthesis?.cancel()
    try {
      const res = await api.get(`/sessions/${sessionId}/question`)
      if (res.data.max_reached || !res.data.question) {
        setCompleted(true)
      } else {
        setQuestion(res.data)
        setQuestionNumber(res.data.question_order || questionNumber + 1)
        setAnswer('')
        const sess = await api.get(`/sessions/${sessionId}`)
        if (sess.data.extracted_skills?.config?.question_count) {
          setTotalQuestions(sess.data.extracted_skills.config.question_count)
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load question. Please try again.')
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchQuestion() }, [])

  const handleSubmit = async () => {
    if (!answer.trim()) { setError('Please provide an answer before submitting.'); return }
    window.speechSynthesis?.cancel()
    if (isListening) recognitionRef.current?.stop()
    setSubmitting(true); setError('')
    try {
      const res = await api.post(`/sessions/${sessionId}/answer`, {
        question_id: question.question_id,
        answer: answer.trim(),
      })
      if (res.data.score) {
        setLastScore({ score: res.data.score, feedback: res.data.feedback })
        setShowScore(true)
        await new Promise(r => setTimeout(r, 3200))
        setShowScore(false)
      }
      if (!res.data.next_available) setCompleted(true)
      else await fetchQuestion()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit answer.')
    } finally { setSubmitting(false) }
  }

  const handleComplete = async () => {
    try { await api.post(`/sessions/${sessionId}/complete`); setScreen('summary') }
    catch (err) { setError(err.response?.data?.detail || 'Failed to complete session.') }
  }

  const wordCount = answer.trim().split(/\s+/).filter(Boolean).length
  const progress = totalQuestions > 0 ? (questionNumber / totalQuestions) * 100 : 0

  // ─── Render ──────────────────────────────────────────────────────────────
  return (
    <div className="max-w-3xl mx-auto animate-fade-in">

      {/* Score Toast */}
      {showScore && lastScore && (
        <div className="fixed top-20 right-5 z-50 w-72 animate-slide-down">
          <ScoreToast score={lastScore.score} feedback={lastScore.feedback} />
        </div>
      )}

      {/* ── Header Bar ── */}
      <div className="card p-5 mb-5">
        <div className="flex items-center justify-between mb-4">
          <div className="min-w-0">
            <h2 className="text-base font-bold text-gray-900 font-display leading-tight">Technical Assessment</h2>
            <p className="text-xs text-gray-400 mt-0.5 truncate">
              {role} · Session <span className="font-mono text-blue-600">{sessionId?.slice(0, 8)}…</span>
            </p>
          </div>
          <div className="text-right flex-shrink-0 ml-4">
            <div className="flex items-baseline gap-0.5 justify-end">
              <span className="text-3xl font-black text-blue-600 font-display leading-none">{questionNumber}</span>
              <span className="text-gray-300 text-xl font-light">/</span>
              <span className="text-lg font-bold text-gray-400 font-display">{totalQuestions}</span>
            </div>
            <p className="text-[10px] text-gray-400 uppercase tracking-widest mt-1">Questions</p>
          </div>
        </div>

        {/* Progress */}
        <div className="progress-track mb-4">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>

        {/* Skills */}
        {skills?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {skills.slice(0, 6).map((s, i) => (
              <span key={i} className="text-[10px] px-2.5 py-1 rounded-full bg-gray-100 border border-gray-200 text-gray-500 font-medium uppercase tracking-wider">
                {s}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* ── Loading ── */}
      {loading && !completed && (
        <div className="card-elevated p-14 text-center animate-fade-in">
          <div className="w-14 h-14 mx-auto mb-5 relative">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 56 56">
              <circle cx="28" cy="28" r="24" fill="none" stroke="#e2e8f0" strokeWidth="4" />
              <circle cx="28" cy="28" r="24" fill="none" stroke="#2563eb" strokeWidth="4"
                strokeDasharray="150" strokeDashoffset="75" strokeLinecap="round"
                style={{ animation: 'spin 1.2s linear infinite' }} />
            </svg>
          </div>
          <div className="loading-dots justify-center mb-4">
            <span /><span /><span />
          </div>
          <p className="text-gray-700 font-semibold text-sm font-display mb-1.5 animate-pulse">
            {LOADING_STEPS[loadingStepIdx].icon} {LOADING_STEPS[loadingStepIdx].text}
          </p>
          <p className="text-gray-400 text-xs">RAG pipeline retrieving knowledge base</p>
        </div>
      )}

      {/* ── Question Card ── */}
      {!loading && !completed && question && (
        <div className="animate-slide-up space-y-4">
          <div className="card p-7 accent-border-left relative">

            {/* Question Header */}
            <div className="flex items-start justify-between gap-4 mb-5">
              <div className="flex items-center gap-2">
                <span className="badge badge-blue">Q{questionNumber}</span>
                {question.difficulty && (
                  <span className={`badge ${
                    question.difficulty === 'hard' ? 'badge-red' :
                    question.difficulty === 'medium' ? 'badge-amber' : 'badge-green'
                  }`}>{question.difficulty}</span>
                )}
              </div>

              {/* TTS */}
              {enableTTS && window.speechSynthesis && (
                <button
                  type="button"
                  onClick={toggleMuteTTS}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
                    isSpeaking
                      ? 'bg-blue-50 border-blue-200 text-blue-700 animate-pulse'
                      : 'bg-white border-gray-200 text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                  title={isSpeaking ? 'Stop' : 'Listen to question'}
                >
                  <SpeakerIcon muted={!isSpeaking} />
                  {isSpeaking ? 'Playing...' : 'Listen'}
                </button>
              )}
            </div>

            {/* Question Text */}
            <div className="mb-6">
              <p className="text-gray-800 text-base md:text-lg leading-relaxed font-medium">
                <Typewriter
                  text={question.question}
                  speed={12}
                  onComplete={() => { setTypewriterDone(true); speakQuestion(question.question) }}
                />
              </p>
            </div>

            {/* Divider */}
            <div className="divider" />

            {/* Answer Area */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="section-label">Your Response</label>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-400 font-medium">{wordCount} words</span>
                  {enableSTT && (
                    <button
                      type="button"
                      onClick={toggleListening}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
                        isListening
                          ? 'bg-red-50 border-red-200 text-red-700 animate-pulse'
                          : 'bg-white border-gray-200 text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <MicIcon active={isListening} />
                      {isListening ? 'Listening...' : 'Dictate'}
                    </button>
                  )}
                </div>
              </div>

              <textarea
                ref={textareaRef}
                id="answer-textarea"
                value={answer}
                onChange={e => { setAnswer(e.target.value); setError('') }}
                placeholder="Explain your understanding, mention relevant trade-offs, concepts, and real-world applications..."
                rows={7}
                disabled={submitting}
                className="answer-textarea"
              />

              {isListening && (
                <div className="mt-2 flex items-center gap-2 text-xs text-red-600 font-medium">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  Voice dictation active — speak clearly
                </div>
              )}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm animate-scale-in flex items-center gap-2.5">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            id="submit-answer-btn"
            onClick={handleSubmit}
            disabled={submitting || !answer.trim()}
            className={`btn-primary w-full py-3.5 flex items-center justify-center gap-2.5 ${
              submitting || !answer.trim() ? 'opacity-40 cursor-not-allowed' : ''
            }`}
          >
            {submitting ? (
              <>
                <span className="spinner-premium spinner-sm" style={{ borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} />
                Scoring Response...
              </>
            ) : (
              <>
                {questionNumber >= totalQuestions ? 'Submit Final Answer' : 'Submit & Next Question'}
                <SendIcon />
              </>
            )}
          </button>
        </div>
      )}

      {/* ── Completed ── */}
      {completed && (
        <div className="card-elevated p-14 text-center animate-scale-in">
          <div className="w-16 h-16 mx-auto mb-5 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center animate-float">
            <svg className="w-8 h-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2 font-display">Interview Complete!</h3>
          <p className="text-gray-500 text-sm max-w-sm mx-auto mb-8 leading-relaxed">
            You've answered all {totalQuestions} RAG-grounded questions.
            Generating your performance report now.
          </p>
          <button
            id="view-summary-btn"
            onClick={handleComplete}
            className="btn-primary px-9 py-3.5 inline-flex items-center gap-2"
          >
            View Evaluation Report
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}
