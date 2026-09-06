"use client";

import * as React from "react";
import { useState, useRef, useEffect } from "react";
import {
  Leaf,
  Send,
  Mic,
  MicOff,
  X,
  RefreshCw,
  ChevronDown,
  Sparkles,
  AlertCircle,
  Loader2,
  BarChart3,
  Flame,
  Droplets,
  Globe,
  Apple,
  Bot,
  User,
} from "lucide-react";

// ─── ClientTimestamp ─────────────────────────────────────────────────────────
// Prevents hydration mismatch by only rendering on client

function ClientTimestamp({ date }: { date: Date }) {
  const [formatted, setFormatted] = React.useState("");

  React.useEffect(() => {
    setFormatted(date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
  }, [date]);

  return <span className="text-[10px] text-muted-foreground mt-1 px-1">{formatted}</span>;
}

// ─── Types ─────────────────────────────────────────────────────────────────

type Role = "user" | "assistant" | "system";

interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
  nutritionInfo?: Record<string, string | number> | null;
  co2Info?: { food: string; co2_per_100g_kg: number } | null;
  suggestions?: string[];
  isStreaming?: boolean;
}

interface NutritionChatbotProps {
  apiUrl?: string;
  className?: string;
}

// ─── Constants ──────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "assistant",
  content: `👋 **Hello! I'm NutriAI** — your personal nutrition and wellness assistant.

I can help you with:
🥗 **Nutrition analysis** — calories, macros, vitamins for any food
🌍 **Carbon footprint** — environmental impact of your meals  
💪 **Goal planning** — weight loss, muscle gain, energy
🗓️ **Meal planning** — personalized daily plans
🔬 **Science-backed advice** — evidence-based nutrition guidance

**Try asking me:**
- "How many calories in grilled salmon?"
- "Create a high-protein meal plan"
- "What's the carbon footprint of my beef dinner?"
- "Am I getting enough iron on a plant-based diet?"`,
  timestamp: new Date(),
  suggestions: [
    "Analyze my meal: grilled chicken with rice",
    "Create a weight loss meal plan",
    "What foods are high in protein?",
    "Carbon footprint of beef vs lentils",
  ],
};

// ─── Markdown renderer (simple) ─────────────────────────────────────────────

function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("**") && line.endsWith("**") && line.length > 4) {
      // Bold heading line
      const content = line.slice(2, -2);
      elements.push(
        <p key={i} className="font-bold text-foreground mt-3 mb-1">
          {content}
        </p>
      );
    } else if (line.startsWith("- ") || line.startsWith("• ")) {
      // Bullet list item
      const content = line.slice(2);
      elements.push(
        <div key={i} className="flex gap-2 items-start my-0.5">
          <span className="text-primary mt-1 flex-shrink-0">•</span>
          <span>{renderInlineMarkdown(content)}</span>
        </div>
      );
    } else if (/^\d+\.\s/.test(line)) {
      // Numbered list
      const match = line.match(/^(\d+)\.\s(.+)/);
      if (match) {
        elements.push(
          <div key={i} className="flex gap-2 items-start my-0.5">
            <span className="text-primary font-semibold flex-shrink-0 min-w-[1.2rem]">{match[1]}.</span>
            <span>{renderInlineMarkdown(match[2])}</span>
          </div>
        );
      }
    } else if (line.startsWith("| ")) {
      // Table — collect all rows
      const tableRows: string[] = [];
      while (i < lines.length && lines[i].startsWith("| ")) {
        if (!lines[i].includes("---")) tableRows.push(lines[i]);
        i++;
      }
      if (tableRows.length > 0) {
        const headers = tableRows[0].split("|").filter(Boolean).map(s => s.trim());
        const rows = tableRows.slice(1);
        elements.push(
          <div key={`table-${i}`} className="overflow-x-auto my-2">
            <table className="text-xs border-collapse w-full">
              <thead>
                <tr>
                  {headers.map((h, hi) => (
                    <th key={hi} className="border border-border/60 bg-primary/10 px-2 py-1 text-left font-semibold text-foreground">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, ri) => {
                  const cells = row.split("|").filter(Boolean).map(s => s.trim());
                  return (
                    <tr key={ri} className="even:bg-accent/10">
                      {cells.map((cell, ci) => (
                        <td key={ci} className="border border-border/60 px-2 py-1">{cell}</td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    } else if (line === "") {
      elements.push(<div key={i} className="h-1" />);
    } else {
      elements.push(
        <p key={i} className="leading-relaxed">
          {renderInlineMarkdown(line)}
        </p>
      );
    }
    i++;
  }

  return elements;
}

function renderInlineMarkdown(text: string): React.ReactNode {
  // Bold **text**
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="font-semibold text-foreground">{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

// ─── Nutrition Card ──────────────────────────────────────────────────────────

function NutritionCard({ info }: { info: Record<string, string | number> }) {
  const food = info.food as string;
  const entries = Object.entries(info).filter(([k]) => k !== "food");

  const macroIcons: Record<string, React.ReactNode> = {
    calories: <Flame className="w-3.5 h-3.5 text-orange-400" />,
    protein: <BarChart3 className="w-3.5 h-3.5 text-blue-400" />,
    carbs: <Apple className="w-3.5 h-3.5 text-green-400" />,
    fat: <Droplets className="w-3.5 h-3.5 text-yellow-400" />,
  };

  const primaryMacros = ["calories", "protein", "carbs", "fat"];
  const primary = entries.filter(([k]) => primaryMacros.includes(k));
  const extras = entries.filter(([k]) => !primaryMacros.includes(k));

  return (
    <div className="mt-3 rounded-xl border border-primary/20 bg-primary/5 p-3">
      <div className="flex items-center gap-1.5 mb-2">
        <Leaf className="w-3.5 h-3.5 text-primary" />
        <span className="text-xs font-bold text-primary">{food}</span>
      </div>
      <div className="grid grid-cols-4 gap-1.5 mb-2">
        {primary.map(([key, val]) => (
          <div key={key} className="bg-background rounded-lg p-1.5 text-center">
            <div className="flex justify-center mb-0.5">{macroIcons[key] || null}</div>
            <div className="text-xs font-bold text-foreground">{val}</div>
            <div className="text-[10px] text-muted-foreground capitalize">{key}</div>
          </div>
        ))}
      </div>
      {extras.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {extras.map(([key, val]) => (
            <span key={key} className="text-[10px] bg-background px-2 py-0.5 rounded-full border border-border/50 text-muted-foreground">
              {key.replace(/_/g, " ")}: <strong>{val}</strong>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── CO2 Badge ──────────────────────────────────────────────────────────────

function Co2Badge({ info }: { info: { food: string; co2_per_100g_kg: number } }) {
  const co2 = info.co2_per_100g_kg;
  const color = co2 < 1 ? "text-green-500 bg-green-50 border-green-200 dark:bg-green-950/30 dark:border-green-900" :
    co2 < 6 ? "text-yellow-600 bg-yellow-50 border-yellow-200 dark:bg-yellow-950/30 dark:border-yellow-900" :
    "text-red-500 bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-900";
  const label = co2 < 1 ? "🟢 Eco-friendly" : co2 < 6 ? "🟡 Moderate" : "🔴 High impact";

  return (
    <div className={`mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${color}`}>
      <Globe className="w-3 h-3" />
      CO₂: {co2} kg/100g · {label}
    </div>
  );
}

// ─── Message Bubble ──────────────────────────────────────────────────────────

function MessageBubble({
  message,
  onSuggestion,
}: {
  message: Message;
  onSuggestion: (s: string) => void;
}) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"} items-start`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-white text-xs
        ${isUser ? "bg-gradient-to-br from-violet-400 to-purple-600" : "gradient-wellness"}`}>
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      {/* Content */}
      <div className={`max-w-[82%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "gradient-wellness text-white rounded-tr-sm"
              : "bg-card border border-border/60 text-foreground rounded-tl-sm"
          }`}
        >
          {isUser ? (
            <span>{message.content}</span>
          ) : message.isStreaming ? (
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
              <span className="text-muted-foreground italic">Analyzing...</span>
            </span>
          ) : (
            <div className="space-y-0.5">
              {renderMarkdown(message.content)}
            </div>
          )}
        </div>

        {/* Nutrition card */}
        {!isUser && message.nutritionInfo && (
          <NutritionCard info={message.nutritionInfo as Record<string, string | number>} />
        )}

        {/* CO2 badge */}
        {!isUser && message.co2Info && <Co2Badge info={message.co2Info} />}

        {/* Suggestions */}
        {!isUser && message.suggestions && message.suggestions.length > 0 && (
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {message.suggestions.slice(0, 3).map((s) => (
              <button
                key={s}
                onClick={() => onSuggestion(s)}
                className="text-[11px] bg-primary/8 border border-primary/20 text-primary px-2.5 py-1 rounded-full hover:bg-primary/15 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <ClientTimestamp date={message.timestamp} />
      </div>
    </div>
  );
}

// ─── Main Chatbot Component ──────────────────────────────────────────────────

export function NutritionChatbot({ apiUrl = API_URL, className = "" }: NutritionChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);

  // ── Check backend health ─────────────────────────────────────────────────
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${apiUrl}/health`, { signal: AbortSignal.timeout(3000) });
        setIsConnected(res.ok);
      } catch {
        setIsConnected(false);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  // ── Auto-scroll ──────────────────────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Auto-resize textarea ─────────────────────────────────────────────────
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }, [input]);

  // ── Send message ─────────────────────────────────────────────────────────
  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    setInput("");
    setError(null);

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };

    const loadingMsg: Message = {
      id: `a-${Date.now()}`,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, loadingMsg]);
    setIsLoading(true);

    // Build history for context
    const history = messages.slice(-8).map(m => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          model: "gemini",
          effort: "Medium",
          history,
        }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const data = await res.json();

      setMessages(prev =>
        prev.map(m =>
          m.id === loadingMsg.id
            ? {
                ...m,
                content: data.response,
                nutritionInfo: data.nutrition_info,
                co2Info: data.co2_info,
                suggestions: data.suggestions || [],
                isStreaming: false,
              }
            : m
        )
      );
    } catch (err: any) {
      const errMsg = err.message?.includes("fetch") || err.message?.includes("Failed")
        ? "Cannot connect to NutriAI backend. Make sure the server is running on port 8000."
        : err.message || "Something went wrong. Please try again.";

      setMessages(prev =>
        prev.map(m =>
          m.id === loadingMsg.id
            ? {
                ...m,
                content: `⚠️ ${errMsg}`,
                isStreaming: false,
              }
            : m
        )
      );
      setError(errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const clearChat = () => {
    setMessages([WELCOME_MESSAGE]);
    setError(null);
  };

  // ── Voice input ──────────────────────────────────────────────────────────
  const toggleVoice = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError("Voice input is not supported in this browser. Try Chrome.");
      return;
    }

    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = false;
    recognitionRef.current = recognition;

    recognition.onresult = (e: any) => {
      let transcript = "";
      for (let i = 0; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript;
      }
      setInput(transcript);
    };

    recognition.onend = () => setIsRecording(false);
    recognition.onerror = () => {
      setIsRecording(false);
      setError("Voice recognition failed. Please try again.");
    };

    recognition.start();
    setIsRecording(true);
  };

  const connectionStatus = isConnected === null ? "checking" : isConnected ? "connected" : "offline";

  return (
    <div className={`flex flex-col h-[600px] rounded-3xl border border-border/60 bg-background overflow-hidden shadow-xl ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-border/60 gradient-wellness-soft">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl gradient-wellness flex items-center justify-center shadow-sm">
            <Leaf className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-foreground" style={{ fontFamily: "var(--font-outfit), sans-serif" }}>
              NutriAI Chat
            </h3>
            <div className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${
                connectionStatus === "connected" ? "bg-green-500 animate-pulse" :
                connectionStatus === "offline" ? "bg-red-400" : "bg-yellow-400 animate-pulse"
              }`} />
              <span className="text-[10px] text-muted-foreground capitalize">
                {connectionStatus === "connected" ? "AI Online · Gemini 2.0 Flash" :
                 connectionStatus === "offline" ? "Backend Offline" : "Connecting..."}
              </span>
            </div>
          </div>
        </div>
<div className="flex items-center gap-1.5">
              <span className="hidden sm:flex items-center gap-1 text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full border border-primary/20">
                <Sparkles className="w-2.5 h-2.5" />
              </span>
              <button
            onClick={clearChat}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/30 transition-colors"
            title="Clear chat"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2 bg-destructive/10 border-b border-destructive/20 text-destructive text-xs">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError(null)}><X className="w-3 h-3" /></button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scroll-smooth">
        {messages.map(msg => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onSuggestion={s => sendMessage(s)}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Scroll to bottom if many messages */}
      {messages.length > 6 && (
        <button
          onClick={() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })}
          className="absolute bottom-24 right-6 w-7 h-7 rounded-full bg-primary/15 border border-primary/25 flex items-center justify-center text-primary hover:bg-primary/25 transition-colors"
        >
          <ChevronDown className="w-4 h-4" />
        </button>
      )}

      {/* Input area */}
      <div className="px-4 pb-4 pt-2 border-t border-border/60 bg-background/80 backdrop-blur-sm">
        <div className="flex items-end gap-2 neu-inset rounded-2xl px-3 py-2 bg-muted/30">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about nutrition, meals, carbon footprint..."
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground/60 outline-none min-h-[36px] max-h-[120px] py-1.5 leading-relaxed"
            disabled={isLoading}
          />
          <div className="flex gap-1.5 pb-0.5">
            <button
              onClick={toggleVoice}
              className={`p-2 rounded-xl transition-all ${
                isRecording
                  ? "bg-red-500 text-white animate-pulse"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/30"
              }`}
              title={isRecording ? "Stop recording" : "Voice input"}
            >
              {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isLoading}
              className="p-2 rounded-xl gradient-wellness text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-all shadow-sm"
              title="Send message"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
        <p className="text-[10px] text-muted-foreground text-center mt-1.5">
          Enter to send · Shift+Enter for new line · AI may make mistakes
        </p>
      </div>
    </div>
  );
}

export default NutritionChatbot;
