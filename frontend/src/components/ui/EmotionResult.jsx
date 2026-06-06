import { motion } from 'framer-motion'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'
import { CheckCircleIcon } from '@heroicons/react/24/solid'

export default function EmotionResult({ result, colors }) {
  const { predicted_emotion, confidence, all_probabilities } = result

  const radarData = Object.entries(all_probabilities).map(([name, value]) => ({
    emotion: name.charAt(0).toUpperCase() + name.slice(1),
    value: Math.round(value),
  }))

  return (
    <div className="card space-y-6">
      {/* Main result */}
      <div className="flex items-center gap-6">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 20, delay: 0.1 }}
          className={`w-20 h-20 rounded-2xl ${colors.bg} ring-2 ${colors.ring} flex items-center justify-center text-4xl`}
        >
          {colors.emoji}
        </motion.div>

        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircleIcon className="w-5 h-5 text-emerald-400" />
            <span className="text-slate-400 text-sm font-medium">Detected Emotion</span>
          </div>
          <h2 className={`font-display text-3xl font-bold capitalize ${colors.text}`}>
            {predicted_emotion}
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Confidence: <span className="text-white font-semibold">{confidence}%</span>
          </p>
        </div>

        {/* Confidence ring */}
        <div className="relative w-20 h-20 flex-shrink-0">
          <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
            <circle cx="40" cy="40" r="32" fill="none" stroke="#334155" strokeWidth="6" />
            <motion.circle
              cx="40" cy="40" r="32"
              fill="none"
              stroke="rgb(14,165,233)"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 32}`}
              initial={{ strokeDashoffset: 2 * Math.PI * 32 }}
              animate={{ strokeDashoffset: 2 * Math.PI * 32 * (1 - confidence / 100) }}
              transition={{ duration: 1.2, ease: 'easeOut', delay: 0.2 }}
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-white">
            {confidence}%
          </span>
        </div>
      </div>

      {/* Probability bars */}
      <div className="space-y-2.5">
        <h3 className="text-slate-400 text-xs font-medium uppercase tracking-wider">All Probabilities</h3>
        {Object.entries(all_probabilities)
          .sort(([, a], [, b]) => b - a)
          .map(([emotion, prob], i) => (
            <div key={emotion} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className={`capitalize font-medium ${emotion === predicted_emotion ? 'text-white' : 'text-slate-400'}`}>
                  {emotion}
                </span>
                <span className="text-slate-400 font-mono">{prob}%</span>
              </div>
              <div className="h-2 bg-surface rounded-full overflow-hidden">
                <motion.div
                  className={`h-full rounded-full ${emotion === predicted_emotion ? 'bg-brand-500' : 'bg-slate-600'}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${prob}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut', delay: i * 0.06 }}
                />
              </div>
            </div>
          ))}
      </div>

      {/* Radar chart */}
      {radarData.length > 2 && (
        <div className="pt-4 border-t border-surface-border">
          <h3 className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-4">Emotion Profile</h3>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="emotion" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Radar name="probability" dataKey="value" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.15} strokeWidth={2} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
                  formatter={(v) => [`${v}%`, 'Probability']}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
