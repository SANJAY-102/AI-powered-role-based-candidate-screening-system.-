import { useState, useEffect } from 'react'
import api from '../api/client'

// ─── Helpers ──────────────────────────────────────────────────────────────────
const scoreConfig = (score) => ({
  5: { label: 'Excellent', color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', bar: 'bg-emerald-500', ring: 'ring-emerald-200' },
  4: { label: 'Good', color: 'text-teal-700', bg: 'bg-teal-50', border: 'border-teal-200', bar: 'bg-teal-500', ring: 'ring-teal-200' },
  3: { label: 'Fair', color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', bar: 'bg-amber-400', ring: 'ring-amber-200' },
  2: { label: 'Basic', color: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-200', bar: 'bg-orange-400', ring: 'ring-orange-200' },
  1: { label: 'Needs Work', color: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200', bar: 'bg-red-400', ring: 'ring-red-200' },
}[Math.round(score)] || { label: 'N/A', color: 'text-gray-500', bg: 'bg-gray-50', border: 'border-gray-200', bar: 'bg-gray-300', ring: 'ring-gray-200' })

// ─── SVG Gauge ────────────────────────────────────────────────────────────────
function ScoreGauge({ score, max = 5 }) {
  const pct = (score / max) * 100
  const r = 44
  const circ = 2 * Math.PI * r
  const offset = circ - (pct / 100) * circ
  const cfg = scoreConfig(score)

  const gaugeColor = {
    5: '#059669', 4: '#0d9488', 3: '#d97706', 2: '#ea580c', 1: '#dc2626'
  }[Math.round(score)] || '#94a3b8'

  return (
    <div className="relative w-28 h-28 flex-shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#f1f5f9" strokeWidth="7" />
        <circle
          cx="50" cy="50" r={r} fill="none"
          stroke={gaugeColor}
          strokeWidth="7"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-2xl font-black font-display ${cfg.color}`}>{score ? score.toFixed(1) : '—'}</span>
        <span className="text-[9px] text-gray-400 font-semibold uppercase tracking-widest">/5</span>
      </div>
    </div>
  )
}

// ─── Score Bar ────────────────────────────────────────────────────────────────
function ScoreBar({ score }) {
  const cfg = scoreConfig(score)
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${cfg.bar} rounded-full`}
          style={{ width: `${(score / 5) * 100}%`, transition: 'width 0.8s cubic-bezier(0.16,1,0.3,1)' }}
        />
      </div>
      <span className={`text-sm font-bold font-display w-6 text-right ${cfg.color}`}>{score || '—'}</span>
    </div>
  )
}

// ─── Icons ────────────────────────────────────────────────────────────────────
const PrintIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
  </svg>
)

// ─── Main Component ───────────────────────────────────────────────────────────
export default function SummaryScreen({ sessionId, role, setScreen, setSessionId }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedChunks, setExpandedChunks] = useState({})
  const [expandedAnswers, setExpandedAnswers] = useState({})

  useEffect(() => {
    api.get(`/sessions/${sessionId}/summary`)
      .then(r => setSummary(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load summary.'))
      .finally(() => setLoading(false))
  }, [sessionId])

  const toggleChunk = i => setExpandedChunks(p => ({ ...p, [i]: !p[i] }))
  const toggleAnswer = i => setExpandedAnswers(p => ({ ...p, [i]: !p[i] }))
  const handleNewInterview = () => { setSessionId(null); setScreen('upload') }

  // ─── Loading ─────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="max-w-4xl mx-auto text-center py-24 animate-fade-in">
      <div className="w-14 h-14 mx-auto mb-5 relative">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="24" fill="none" stroke="#e2e8f0" strokeWidth="4" />
          <circle cx="28" cy="28" r="24" fill="none" stroke="#2563eb" strokeWidth="4"
            strokeDasharray="150" strokeDashoffset="75" strokeLinecap="round"
            style={{ animation: 'spin 1.2s linear infinite' }} />
        </svg>
      </div>
      <p className="text-gray-800 font-semibold text-base font-display mb-1.5">Assembling Your Report...</p>
      <p className="text-gray-400 text-sm">Computing semantic scores and coverage analysis</p>
    </div>
  )

  if (error) return (
    <div className="max-w-lg mx-auto py-24 text-center">
      <div className="card p-10">
        <p className="text-red-600 mb-5 text-sm">{error}</p>
        <button onClick={handleNewInterview} className="btn-primary px-8 py-3">Start New Interview</button>
      </div>
    </div>
  )

  if (!summary) return null

  const { qa_pairs, analysis, config } = summary
  const avgScore = analysis.avg_score || 0
  const cfg = scoreConfig(avgScore)

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="max-w-4xl mx-auto animate-fade-in">

      {/* ── Report Header ── */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-5 mb-7">
          <div>
            <div className="badge badge-green mb-3">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
              Interview Complete
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-1.5 font-display">Evaluation Report</h2>
            <p className="text-gray-500 text-sm flex flex-wrap items-center gap-2">
              <span>Role: <span className="text-gray-800 font-semibold">{summary.role}</span></span>
              {config?.personality && (
                <span className="badge badge-slate">{config.personality}</span>
              )}
            </p>
          </div>
          <div className="flex gap-2.5 no-print flex-shrink-0">
            <button
              id="print-summary-btn"
              onClick={() => window.print()}
              className="btn-secondary px-4 py-2.5 rounded-lg text-xs flex items-center gap-2"
            >
              <PrintIcon /> Export PDF
            </button>
            <button
              id="new-interview-btn"
              onClick={handleNewInterview}
              className="btn-primary px-5 py-2.5 text-xs flex items-center gap-2"
            >
              New Interview
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          </div>
        </div>

        {/* Skills row */}
        {summary.skills?.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-7">
            {summary.skills.map((s, i) => <span key={i} className="skill-chip">{s}</span>)}
          </div>
        )}

        {/* ── Stats Grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">

          {/* Score Gauge Card */}
          <div className="card p-6 md:col-span-2 flex items-center gap-6">
            <ScoreGauge score={avgScore} />
            <div className="flex-1 min-w-0">
              <p className="section-label mb-1.5">Overall Performance</p>
              <div className={`text-xl font-bold font-display ${cfg.color} mb-1`}>
                {cfg.label}
              </div>
              <p className="text-xs text-gray-400 leading-relaxed mb-4">
                Scored via semantic alignment of answers against RAG-retrieved textbook context.
              </p>
              <div className="space-y-2">
                {qa_pairs.filter(q => q.score).slice(0, 3).map((qa, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-400 w-14 font-semibold font-display">Q{qa.question_order || i + 1}</span>
                    <ScoreBar score={qa.score} />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="flex flex-col gap-4">
            <div className="stat-card stat-card-indigo flex-1">
              <p className="text-3xl font-bold text-indigo-600 font-display mb-1">
                {analysis.answered_questions || summary.total_questions}
              </p>
              <p className="section-label">Questions Answered</p>
            </div>
            <div className="stat-card stat-card-purple flex-1">
              <p className="text-3xl font-bold text-purple-600 font-display mb-1">
                {analysis.avg_answer_length}
              </p>
              <p className="section-label">Avg Words / Answer</p>
            </div>
          </div>
        </div>

        {/* Topics Coverage */}
        {analysis.topics_covered?.length > 0 && (
          <div className="card p-5 mb-2">
            <p className="section-label mb-3">Topic Coverage</p>
            <div className="flex flex-wrap gap-2">
              {analysis.topics_covered.map((topic, i) => (
                <span key={i} className="badge badge-teal">{topic}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Q&A Transcript ── */}
      <div className="space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <p className="section-label">Detailed Question Log</p>
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-[10px] text-gray-400 font-semibold font-display">{qa_pairs.length} questions</span>
        </div>

        {qa_pairs.map((qa, index) => {
          const qCfg = scoreConfig(qa.score)
          return (
            <div
              key={qa.question_id || index}
              className="qa-card animate-slide-up"
              style={{ animationDelay: `${index * 60}ms` }}
            >
              {/* Question Header */}
              <div className="p-6 accent-border-left">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center flex-wrap gap-2 mb-3">
                      <span className="badge badge-blue">Q{qa.question_order || index + 1}</span>
                      {qa.score && (
                        <span className={`badge ${qCfg.bg} ${qCfg.color} border ${qCfg.border}`}>
                          {qa.score}/5 · {qCfg.label}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-800 font-semibold leading-relaxed text-sm md:text-base">{qa.question}</p>
                  </div>
                  {/* Score circle */}
                  {qa.score && (
                    <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex flex-col items-center justify-center ${qCfg.bg} border ${qCfg.border} ring-1 ${qCfg.ring}`}>
                      <span className={`text-base font-black font-display ${qCfg.color}`}>{qa.score}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Answer — collapsible */}
              <div className="border-t border-gray-100">
                <button
                  onClick={() => toggleAnswer(index)}
                  className="w-full px-6 py-3 flex items-center justify-between text-left cursor-pointer hover:bg-gray-50 transition-colors"
                >
                  <span className="section-label">Candidate Response</span>
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${expandedAnswers[index] ? 'rotate-180' : ''}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {expandedAnswers[index] && (
                  <div className="px-6 pb-5 animate-slide-down">
                    <p className="text-gray-600 text-sm leading-relaxed whitespace-pre-wrap">
                      {qa.answer || <span className="text-gray-400 italic">No answer provided.</span>}
                    </p>
                  </div>
                )}
                {!expandedAnswers[index] && qa.answer && (
                  <div className="px-6 pb-4">
                    <p className="text-gray-500 text-sm leading-relaxed line-clamp-2">{qa.answer}</p>
                    {qa.answer.length > 120 && (
                      <button
                        onClick={() => toggleAnswer(index)}
                        className="text-blue-600 text-xs mt-1.5 hover:text-blue-700 cursor-pointer font-medium"
                      >
                        Read more ↓
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* RAG Source */}
              {qa.source_chunk && (
                <div className="border-t border-gray-100 no-print">
                  <button
                    onClick={() => toggleChunk(index)}
                    className="w-full px-6 py-3 flex items-center gap-2 text-left cursor-pointer hover:bg-gray-50 transition-colors"
                  >
                    <svg
                      className={`w-3.5 h-3.5 text-blue-400 transition-transform duration-200 ${expandedChunks[index] ? 'rotate-90' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">RAG Source Context</span>
                    <span className="text-[10px] text-gray-400 ml-auto">Textbook Chunk</span>
                  </button>
                  {expandedChunks[index] && (
                    <div className="px-6 pb-5 animate-slide-down">
                      <div className="source-chunk">{qa.source_chunk}</div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* ── Footer Actions ── */}
      <div className="mt-10 pb-16 flex flex-col sm:flex-row justify-center gap-3 no-print">
        <button
          onClick={() => window.print()}
          className="btn-secondary px-7 py-3.5 rounded-xl flex items-center justify-center gap-2"
        >
          <PrintIcon /> Export Transcript
        </button>
        <button
          onClick={handleNewInterview}
          className="btn-primary px-8 py-3.5 flex items-center justify-center gap-2"
        >
          Start New Interview
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>
  )
}
