import { useState, useRef, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import {
  MicrophoneIcon, ArrowUpTrayIcon, StopIcon, CheckCircleIcon,
  ExclamationCircleIcon, MusicalNoteIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { predictAudio } from '../services/api'
import EmotionResult from '../components/ui/EmotionResult'

const EMOTION_COLORS = {
  happy:   { bg: 'bg-yellow-400/20',  text: 'text-yellow-300', ring: 'ring-yellow-400/40', emoji: '😄' },
  calm:    { bg: 'bg-blue-400/20',    text: 'text-blue-300',   ring: 'ring-blue-400/40',   emoji: '😌' },
  fearful: { bg: 'bg-purple-400/20',  text: 'text-purple-300', ring: 'ring-purple-400/40', emoji: '😨' },
  disgust: { bg: 'bg-red-400/20',     text: 'text-red-300',    ring: 'ring-red-400/40',    emoji: '🤢' },
  angry:   { bg: 'bg-orange-400/20',  text: 'text-orange-300', ring: 'ring-orange-400/40', emoji: '😠' },
  sad:     { bg: 'bg-slate-400/20',   text: 'text-slate-300',  ring: 'ring-slate-400/40',  emoji: '😢' },
  neutral: { bg: 'bg-slate-400/20',   text: 'text-slate-300',  ring: 'ring-slate-400/40',  emoji: '😐' },
  surprised:{ bg: 'bg-teal-400/20',   text: 'text-teal-300',   ring: 'ring-teal-400/40',   emoji: '😲' },
}

export default function PredictPage() {
  const [file, setFile]           = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [result, setResult]       = useState(null)
  const mediaRecorder             = useRef(null)
  const chunks                    = useRef([])

  const mutation = useMutation({
    mutationFn: predictAudio,
    onSuccess: (res) => {
      setResult(res.data)
      toast.success(`Detected: ${res.data.predicted_emotion}`)
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Prediction failed')
    },
  })

  // ── Dropzone ───────────────────────────────────────────────────────────────
  const onDrop = useCallback((accepted) => {
    if (accepted[0]) { setFile(accepted[0]); setResult(null) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'audio/*': ['.wav', '.mp3', '.ogg', '.flac', '.m4a'] },
    maxSize: 16 * 1024 * 1024,
    multiple: false,
  })

  // ── Microphone recording ───────────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      chunks.current = []
      mediaRecorder.current = new MediaRecorder(stream)
      mediaRecorder.current.ondataavailable = (e) => chunks.current.push(e.data)
      mediaRecorder.current.onstop = () => {
        const blob = new Blob(chunks.current, { type: 'audio/wav' })
        const recorded = new File([blob], 'recording.wav', { type: 'audio/wav' })
        setFile(recorded)
        setResult(null)
        stream.getTracks().forEach((t) => t.stop())
      }
      mediaRecorder.current.start()
      setIsRecording(true)
    } catch {
      toast.error('Microphone access denied.')
    }
  }

  const stopRecording = () => {
    mediaRecorder.current?.stop()
    setIsRecording(false)
  }

  const handlePredict = () => {
    if (!file) return toast.error('Upload or record audio first.')
    mutation.mutate(file)
  }

  const emotion = result?.predicted_emotion
  const colors  = EMOTION_COLORS[emotion] || EMOTION_COLORS.neutral

  return (
    <div className="min-h-screen gradient-mesh pt-24 pb-16 px-4">
      <div className="max-w-3xl mx-auto space-y-8">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-display text-4xl font-bold text-white mb-2">
            Detect Emotion
          </h1>
          <p className="text-slate-400">Upload an audio file or record your voice to analyze emotion.</p>
        </motion.div>

        {/* Upload Zone */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          {...getRootProps()}
          className={`card cursor-pointer border-2 border-dashed transition-all duration-300 text-center py-14
            ${isDragActive ? 'border-brand-500 bg-brand-500/5' : 'border-surface-border hover:border-brand-500/50 hover:bg-white/2'}`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-4">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors
              ${isDragActive ? 'bg-brand-500/20' : 'bg-white/5'}`}>
              <ArrowUpTrayIcon className={`w-8 h-8 ${isDragActive ? 'text-brand-400' : 'text-slate-400'}`} />
            </div>
            {file ? (
              <div className="flex items-center gap-2 text-brand-400 font-medium">
                <MusicalNoteIcon className="w-5 h-5" />
                <span>{file.name}</span>
                <span className="text-slate-500 text-sm">({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            ) : (
              <>
                <p className="text-slate-300 font-medium">
                  {isDragActive ? 'Drop it here…' : 'Drag & drop audio here'}
                </p>
                <p className="text-slate-500 text-sm">WAV, MP3, OGG, FLAC, M4A — max 16 MB</p>
              </>
            )}
          </div>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="flex gap-4 flex-wrap"
        >
          {/* Mic button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all duration-200
              ${isRecording
                ? 'bg-red-500/20 text-red-300 ring-1 ring-red-500/40 hover:bg-red-500/30'
                : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'}`}
          >
            {isRecording ? (
              <><StopIcon className="w-5 h-5" /><span>Stop Recording</span>
                <span className="flex w-2 h-2 rounded-full bg-red-400 animate-pulse" /></>
            ) : (
              <><MicrophoneIcon className="w-5 h-5" /><span>Record Mic</span></>
            )}
          </button>

          {/* Predict button */}
          <button
            onClick={handlePredict}
            disabled={!file || mutation.isPending}
            className="btn-primary flex items-center gap-2 flex-1 justify-center"
          >
            {mutation.isPending ? (
              <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Analyzing…</span></>
            ) : (
              <><MicrophoneIcon className="w-5 h-5" /><span>Predict Emotion</span></>
            )}
          </button>
        </motion.div>

        {/* Result */}
        <AnimatePresence>
          {result && (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1,    y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            >
              <EmotionResult result={result} colors={colors} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
