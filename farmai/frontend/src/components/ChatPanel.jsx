import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Bot, User, Globe, ChevronDown } from 'lucide-react';
import { api } from '../api/client';

const LANG_OPTIONS = [
  { code: 'en', label: 'English' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'hi', label: 'हिन्दी' },
];

const INITIAL_BOT_MESSAGE = {
  sender: 'bot',
  text: 'Hello! I am FarmAI — your AI-powered IPM advisory assistant. Ask me questions about disease treatment, organic remedies, or irrigation. Powered by your local knowledge base.',
  sources: ['knowledge_base/docs/ipm_crop_diseases.md'],
};

/** Render markdown-lite: bold, bullet points, KVK blockquote */
function BotMessageText({ text }) {
  if (!text) return null;
  // Split on double-newline for paragraphs
  const lines = text.split('\n');
  return (
    <div className="space-y-1.5">
      {lines.map((line, i) => {
        if (line.trim() === '') return <div key={i} className="h-1" />;
        // Blockquote (KVK notice)
        if (line.trim().startsWith('>')) {
          return (
            <div key={i} className="border-l-2 border-amber-400 pl-2 text-amber-700 bg-amber-50/60 rounded text-[10px] italic">
              {line.replace(/^>\s*/, '').replace(/\*\*/g, '')}
            </div>
          );
        }
        // Bullet points
        if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
          return (
            <div key={i} className="flex gap-1.5">
              <span className="text-emerald-500 flex-shrink-0 mt-0.5">•</span>
              <span dangerouslySetInnerHTML={{ __html: line.replace(/^[-*]\s+/, '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
            </div>
          );
        }
        // Numbered
        if (/^\d+\.\s/.test(line.trim())) {
          const [num, ...rest] = line.trim().split('. ');
          return (
            <div key={i} className="flex gap-1.5">
              <span className="text-emerald-600 font-bold flex-shrink-0">{num}.</span>
              <span dangerouslySetInnerHTML={{ __html: rest.join('. ').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
            </div>
          );
        }
        // Heading-style
        if (line.trim().startsWith('**') && line.trim().endsWith('**')) {
          return (
            <p key={i} className="font-bold text-slate-900 text-xs">
              {line.trim().replace(/\*\*/g, '')}
            </p>
          );
        }
        // Normal text with inline bold
        return (
          <p key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
        );
      })}
    </div>
  );
}

export default function ChatPanel({ currentAnalysis }) {
  const [messages, setMessages] = useState([INITIAL_BOT_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('en');
  const [showLangMenu, setShowLangMenu] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Context-aware suggested questions
  const suggestedQuestions = currentAnalysis
    ? [
        `What organic remedies work for ${currentAnalysis.disease?.label || 'this disease'}?`,
        'How does today\'s humidity affect risk?',
        'Is drip irrigation better in this situation?',
        'What cultural practices can prevent recurrence?',
      ]
    : [
        'What is IPM and how does it work?',
        'Best organic fungicide for tomato?',
        'When should I irrigate in high humidity?',
        'How to prevent early blight next season?',
      ];

  const handleSend = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;
    setInput('');
    setMessages(prev => [...prev, { sender: 'user', text: query }]);
    setLoading(true);

    try {
      const analysisId = currentAnalysis?.analysis_id ?? null;
      const res = await api.sendChat(query, analysisId, language);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: res.answer,
        sources: res.sources,
        grounded: res.grounded,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'Unable to connect to advisory service. Please check your network or consult your local Krishi Vigyan Kendra (KVK).',
        sources: [],
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const currentLang = LANG_OPTIONS.find(l => l.code === language);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[560px]">
      {/* ── Header ── */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-700">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">FarmAI Assistant</h4>
            <span className="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              {currentAnalysis
                ? `Context: ${currentAnalysis.crop} — ${currentAnalysis.disease?.label ?? '—'}`
                : 'General IPM Advisory · KB Grounded'}
            </span>
          </div>
        </div>

        {/* Language selector */}
        <div className="relative">
          <button
            onClick={() => setShowLangMenu(v => !v)}
            className="flex items-center gap-1 text-[11px] font-semibold text-slate-600 hover:text-emerald-700 border border-slate-200 rounded-lg px-2 py-1 transition-colors"
          >
            <Globe className="w-3.5 h-3.5" />
            {currentLang?.label}
            <ChevronDown className="w-3 h-3" />
          </button>
          {showLangMenu && (
            <div className="absolute right-0 top-8 bg-white border border-slate-200 rounded-xl shadow-lg z-10 py-1 min-w-[100px]">
              {LANG_OPTIONS.map(l => (
                <button
                  key={l.code}
                  onClick={() => { setLanguage(l.code); setShowLangMenu(false); }}
                  className={`w-full text-left px-3 py-1.5 text-xs hover:bg-emerald-50 hover:text-emerald-700 transition-colors ${
                    l.code === language ? 'font-bold text-emerald-700' : 'text-slate-700'
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex gap-2.5 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.sender === 'bot' && (
              <div className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 flex-shrink-0 mt-1">
                <Bot className="w-3.5 h-3.5" />
              </div>
            )}
            <div className={`max-w-[84%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
              m.sender === 'user'
                ? 'bg-emerald-600 text-white font-medium rounded-tr-none'
                : 'bg-slate-100 text-slate-800 rounded-tl-none'
            }`}>
              {m.sender === 'bot' ? (
                <BotMessageText text={m.text} />
              ) : (
                <p>{m.text}</p>
              )}
              {m.sources?.length > 0 && m.sender === 'bot' && (
                <div className="mt-2 pt-1.5 border-t border-slate-200/70 text-[10px] text-slate-400 font-medium">
                  📚 {m.sources.map(s => s.split('/').pop()).join(' · ')}
                </div>
              )}
            </div>
            {m.sender === 'user' && (
              <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 flex-shrink-0 mt-1">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-2 items-center text-xs text-slate-400 pl-9">
            <span className="flex gap-0.5">
              {[0, 1, 2].map(i => (
                <span key={i} className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </span>
            Searching knowledge base…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Suggested prompts ── */}
      <div className="px-4 py-2 bg-slate-50/70 border-t border-slate-100 flex items-center gap-1.5 overflow-x-auto text-[11px] no-scrollbar">
        <Sparkles className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
        {suggestedQuestions.map((q, i) => (
          <button
            key={i}
            onClick={() => handleSend(q)}
            disabled={loading}
            className="px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-600 hover:text-emerald-700 hover:border-emerald-300 font-medium whitespace-nowrap transition-colors disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* ── Input ── */}
      <div className="p-3 border-t border-slate-100">
        <form onSubmit={e => { e.preventDefault(); handleSend(); }} className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about organic remedies, disease symptoms, or sprays…"
            className="flex-1 text-xs border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-medium"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white p-2.5 rounded-xl transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
