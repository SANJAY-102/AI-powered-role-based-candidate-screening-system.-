import { useState, useRef } from 'react'
import api from '../api/client'

const ROLES = [
  { id: 'ai-ml', label: 'AI/ML Engineer', icon: '🤖', desc: 'ML models, deep learning, embeddings' },
  { id: 'backend', label: 'Backend Engineer', icon: '⚙️', desc: 'APIs, systems, databases' },
  { id: 'data-science', label: 'Data Scientist', icon: '📊', desc: 'Analysis, statistics, ML pipelines' },
]

const LEVEL_BADGE = {
  junior: 'badge-green',
  mid: 'badge-blue',
  senior: 'badge-purple',
}

// ─── Icons ──────────────────────────────────────────────────────────────────
const UploadIcon = () => (
  <svg className="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
)

const FileIcon = () => (
  <svg className="w-7 h-7 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
)

const CheckCircleIcon = () => (
  <svg className="w-7 h-7 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const AlertIcon = () => (
  <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const ArrowIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
  </svg>
)

// ─── Main Component ──────────────────────────────────────────────────────────
export default function UploadScreen({
  setScreen, setSessionId, setRole, setSkills, setExperienceLevel,
  questionCount, personality
}) {
  const [selectedRole, setSelectedRole] = useState('')
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [parsedSkills, setParsedSkills] = useState(null)
  const [parsedTechnologies, setParsedTechnologies] = useState(null)
  const [parsedLevel, setParsedLevel] = useState(null)
  const [step, setStep] = useState(1)
  const [recoverId, setRecoverId] = useState('')
  const [recovering, setRecovering] = useState(false)
  const [showRecovery, setShowRecovery] = useState(false)
  const fileInputRef = useRef(null)

  const handleDragOver = e => { e.preventDefault(); setDragOver(true) }
  const handleDragLeave = () => setDragOver(false)
  const handleDrop = e => {
    e.preventDefault(); setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f && f.type === 'application/pdf') { setFile(f); setError('') }
    else setError('Please upload a PDF file only.')
  }
  const handleFileSelect = e => {
    const f = e.target.files[0]
    if (f) { setFile(f); setError('') }
  }

  const handleSubmit = async () => {
    if (!selectedRole) return setError('Please select a target role first.')
    if (!file) return setError('Please upload your resume PDF.')
    setLoading(true); setError('')
    try {
      const sessionRes = await api.post('/sessions', { role: selectedRole, config: { question_count: questionCount, personality } })
      const { session_id } = sessionRes.data
      const formData = new FormData()
      formData.append('resume', file)
      const resumeRes = await api.post(`/sessions/${session_id}/resume`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      const { skills, technologies, experience_level } = resumeRes.data
      setParsedSkills(skills); setParsedTechnologies(technologies); setParsedLevel(experience_level)
      setSessionId(session_id); setRole(selectedRole); setSkills(skills); setExperienceLevel(experience_level)
      setStep(2)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Something went wrong.')
    } finally { setLoading(false) }
  }

  const handleQuickStart = async () => {
    if (!selectedRole) return setError('Please select a target role first.')
    setLoading(true); setError('')
    try {
      const sessionRes = await api.post('/sessions', { role: selectedRole, config: { question_count: questionCount, personality } })
      const { session_id } = sessionRes.data
      const resumeRes = await api.post(`/sessions/${session_id}/mock-resume`)
      const { skills, technologies, experience_level } = resumeRes.data
      setParsedSkills(skills); setParsedTechnologies(technologies); setParsedLevel(experience_level)
      setSessionId(session_id); setRole(selectedRole); setSkills(skills); setExperienceLevel(experience_level)
      setStep(2)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Something went wrong.')
    } finally { setLoading(false) }
  }

  const handleResumeSession = async () => {
    if (!recoverId.trim()) return setError('Please enter a Session ID.')
    setRecovering(true); setError('')
    try {
      const res = await api.get(`/sessions/${recoverId.trim()}`)
      const { session_id, role, extracted_skills, status } = res.data
      setSessionId(session_id); setRole(role)
      setSkills(extracted_skills?.skills || ['general programming'])
      setExperienceLevel(extracted_skills?.experience_level || 'mid')
      setScreen(status === 'completed' ? 'summary' : 'interview')
    } catch {
      setError('Unable to resume session. Check the Session ID and try again.')
    } finally { setRecovering(false) }
  }

  // ─── STEP 1 ───────────────────────────────────────────────────────────────
  if (step === 1) {
    return (
      <div className="max-w-2xl mx-auto animate-slide-up">

        {/* Role Selection */}
        <div className="card p-6 mb-5">
          <div className="flex items-center gap-2 mb-5">
            <span className="section-label">Step 1</span>
            <span className="text-gray-300">·</span>
            <span className="text-sm font-semibold text-gray-700 font-display">Select Target Role</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {ROLES.map(r => (
              <button
                key={r.id}
                id={`role-${r.id}`}
                onClick={() => { setSelectedRole(r.label); setError('') }}
                className={`role-card ${selectedRole === r.label ? 'selected' : ''}`}
              >
                <div className="flex flex-col gap-2.5">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-xl">
                    {r.icon}
                  </div>
                  <div>
                    <p className={`text-sm font-bold font-display leading-tight ${selectedRole === r.label ? 'text-blue-800' : 'text-gray-800'}`}>
                      {r.label}
                    </p>
                    <p className="text-xs text-gray-500 mt-1 leading-snug">{r.desc}</p>
                  </div>
                </div>
                {selectedRole === r.label && (
                  <span className="absolute top-3 right-3 w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Resume Upload */}
        <div className="card p-6 mb-5">
          <div className="flex items-center gap-2 mb-5">
            <span className="section-label">Step 2</span>
            <span className="text-gray-300">·</span>
            <span className="text-sm font-semibold text-gray-700 font-display">Upload Resume</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Drop Zone — 3 cols */}
            <div
              id="resume-drop-zone"
              className={`md:col-span-3 drop-zone p-8 text-center ${dragOver ? 'drag-over' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileSelect} className="hidden" id="resume-file-input" />
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center">
                  {file ? <FileIcon /> : <UploadIcon />}
                </div>
                {file ? (
                  <div className="animate-scale-in">
                    <p className="text-emerald-700 font-semibold text-sm truncate max-w-[200px]">{file.name}</p>
                    <p className="text-xs text-gray-400 mt-1">{(file.size / 1024).toFixed(0)} KB · Click to change</p>
                  </div>
                ) : (
                  <>
                    <div>
                      <p className="text-gray-700 font-semibold text-sm">Drop PDF Resume Here</p>
                      <p className="text-gray-400 text-xs mt-1">or click to browse files</p>
                    </div>
                    <span className="badge badge-blue">PDF only</span>
                  </>
                )}
              </div>
            </div>

            {/* Quick Start — 2 cols */}
            <div className="md:col-span-2 flex flex-col gap-3">
              <div className="flex-1 p-5 rounded-xl border border-gray-200 bg-gray-50 flex flex-col justify-between">
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-base">⚡</span>
                    <p className="text-sm font-bold text-gray-800 font-display">No PDF?</p>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed">
                    Use a curated demo profile matching your role — perfect for testing the system.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleQuickStart}
                  disabled={loading || !selectedRole}
                  className={`w-full py-2.5 rounded-lg text-xs font-semibold tracking-wide transition-all cursor-pointer border ${
                    !selectedRole
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200'
                      : 'bg-white text-blue-700 border-blue-200 hover:bg-blue-50 hover:border-blue-300'
                  }`}
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="spinner-premium spinner-sm" style={{ borderColor: '#bfdbfe', borderTopColor: '#2563eb' }} />
                      Loading...
                    </span>
                  ) : 'Use Sample Profile'}
                </button>
              </div>

              <button
                type="button"
                onClick={() => setShowRecovery(!showRecovery)}
                className="p-3 rounded-xl border border-gray-200 bg-white text-xs text-gray-500 hover:text-gray-700 hover:border-gray-300 transition-all cursor-pointer font-medium flex items-center justify-center gap-1.5"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Resume a Session
              </button>
            </div>
          </div>

          {/* Session Recovery */}
          {showRecovery && (
            <div className="mt-4 animate-slide-down">
              <div className="divider" />
              <p className="section-label mb-3">Resume Previous Session</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={recoverId}
                  onChange={e => { setRecoverId(e.target.value); setError('') }}
                  placeholder="Paste Session UUID..."
                  disabled={recovering || loading}
                  className="form-input flex-1"
                />
                <button
                  type="button"
                  onClick={handleResumeSession}
                  disabled={recovering || loading || !recoverId.trim()}
                  className={`px-5 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer border ${
                    recovering || loading || !recoverId.trim()
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200'
                      : 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {recovering ? <span className="spinner-premium spinner-sm" style={{ borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} /> : 'Resume'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-5 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm animate-scale-in flex items-center gap-2.5">
            <AlertIcon />
            <span>{error}</span>
          </div>
        )}

        {/* Main CTA */}
        {file && (
          <button
            id="start-interview-btn"
            onClick={handleSubmit}
            disabled={loading || !selectedRole}
            className={`btn-primary w-full py-3.5 flex items-center justify-center gap-2.5 ${
              loading || !selectedRole ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {loading ? (
              <>
                <span className="spinner-premium spinner-sm" style={{ borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} />
                <span>Analyzing Resume...</span>
              </>
            ) : (
              <>
                <span>Analyze Resume &amp; Start Interview</span>
                <ArrowIcon />
              </>
            )}
          </button>
        )}

        {/* Feature Tags */}
        <div className="flex flex-wrap justify-center gap-2 mt-8">
          {['RAG Grounded', 'Adaptive Difficulty', 'Real-time Scoring', 'Session Recovery', 'Voice Input'].map(f => (
            <span key={f} className="badge badge-slate">{f}</span>
          ))}
        </div>
      </div>
    )
  }

  // ─── STEP 2 — Skills Confirmation ──────────────────────────────────────────
  return (
    <div className="max-w-xl mx-auto animate-slide-up">
      <div className="text-center mb-7">
        <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center animate-float">
          <CheckCircleIcon />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-1 font-display">Resume Analyzed</h2>
        <p className="text-sm text-gray-500">Skills extracted and difficulty calibrated for your session.</p>
      </div>

      <div className="card p-6 mb-4">
        {/* Level */}
        <div className="flex items-center justify-between mb-5 pb-5 border-b border-gray-100">
          <div>
            <p className="section-label mb-0.5">Experience Level</p>
            <p className="text-xs text-gray-500">Influences question depth</p>
          </div>
          <span className={`badge ${LEVEL_BADGE[parsedLevel] || 'badge-blue'} text-sm px-4 py-1.5 capitalize`}>
            {parsedLevel}
          </span>
        </div>

        {/* Skills */}
        <div className="mb-5">
          <p className="section-label mb-3">Extracted Skills</p>
          <div className="flex flex-wrap gap-2">
            {parsedSkills?.map((skill, i) => (
              <span key={i} className="skill-chip">{skill}</span>
            ))}
          </div>
        </div>

        {/* Technologies */}
        {parsedTechnologies?.length > 0 && (
          <div>
            <div className="divider" />
            <p className="section-label mb-3">Technologies Detected</p>
            <div className="flex flex-wrap gap-2">
              {parsedTechnologies.map((tech, i) => (
                <span key={i} className="skill-chip skill-chip-purple">{tech}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Config preview */}
      <div className="card p-5 mb-5">
        <div className="grid grid-cols-2 gap-4 text-center divide-x divide-gray-100">
          <div>
            <p className="text-3xl font-bold text-blue-600 font-display">{questionCount}</p>
            <p className="text-xs text-gray-400 uppercase tracking-widest font-semibold mt-1">Questions</p>
          </div>
          <div>
            <p className="text-sm font-bold text-gray-700 font-display leading-snug">{personality}</p>
            <p className="text-xs text-gray-400 uppercase tracking-widest font-semibold mt-1">Interviewer</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => { setStep(1); setParsedSkills(null); setFile(null) }}
          className="btn-secondary flex-1 py-3.5 rounded-xl text-xs uppercase tracking-wider"
        >
          ← Restart
        </button>
        <button
          id="begin-interview-btn"
          onClick={() => setScreen('interview')}
          className="btn-primary flex-[2] py-3.5 flex items-center justify-center gap-2"
        >
          Begin Interview <ArrowIcon />
        </button>
      </div>
    </div>
  )
}
