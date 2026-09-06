"use client";

import * as React from "react";
import { NutritionChatbot } from "@/components/ui/nutrition-chatbot";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  Leaf, Brain, BarChart3, Zap, ShieldCheck, Star,
  ChevronRight, Apple, Play, CheckCircle2, Flame,
  Droplets, Activity, Menu, X, Sparkles, Globe,
} from "lucide-react";

// ─── Intersection Observer Hook for scroll-reveal ───────────────────────────
function useReveal(threshold = 0.15) {
  const ref = React.useRef<HTMLDivElement>(null);
  const [visible, setVisible] = React.useState(false);
  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, visible };
}

// ─── Floating Petal animation (Soft wellness) ────────────────────────────────
function FloatingPetals() {
  const [mounted, setMounted] = React.useState(false);
  const petals = React.useMemo(() =>
    Array.from({ length: 10 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: 4 + Math.random() * 8,
      delay: Math.random() * 6,
      duration: 5 + Math.random() * 7,
    })), []
  );

  React.useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden z-0">
      <style>{`
        @keyframes petal-fall {
          0%   { transform: translateY(-40px) translateX(0) rotate(0deg) scale(1); opacity: 0; }
          20%  { opacity: 0.5; }
          80%  { opacity: 0.2; }
          100% { transform: translateY(100vh) translateX(var(--drift)) rotate(360deg) scale(0.5); opacity: 0; }
        }
        .petal {
          position: absolute;
          top: -40px;
          animation: petal-fall var(--dur) ease-in-out var(--delay) infinite;
          will-change: transform;
        }
      `}</style>
      {petals.map(p => {
        const petalStyle = {
          left: p.left,
          "--dur": `${p.duration}s`,
          "--delay": `${p.delay}s`,
        } as React.CSSProperties;
        return (
          <div key={p.id} className="petal" style={petalStyle}>
            <svg width={p.size} height={p.size} viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <ellipse cx="12" cy="7" rx="3" ry="1.5" fill="currentColor" />
            </svg>
          </div>
        );
      })}
    </div>
  );
}

// ─── Morphing gradient blob ──────────────────────────────────────────────────
function GradientOrb({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      aria-hidden
      className={`absolute rounded-full blur-3xl animate-orb-pulse pointer-events-none ${className}`}
      style={style}
    />
  );
}

// ─── Soft Neumorphic Card ────────────────────────────────────────────────────
function NeuCard({ children, className, style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={`neu-card rounded-2xl ${className}`}
      style={{
        ...style,
        maxWidth: "300px",
        margin: "0 auto",
      } as React.CSSProperties}
    >
      <div className="p-6">{children}</div>
    </div>
  );
}

// ─── Feature Item ────────────────────────────────────────────────────────────
function FeatureItem({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="slide-up-fade stagger-1">
      <div className="neu-card rounded-xl p-6 text-left">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl neu-inset" style={{ background: "var(--card)", boxShadow: "var(--neu-shadow-light)" }}>
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-1">{title}</h3>
            <p className="text-muted-foreground text-sm">{description}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Testimonial Card ────────────────────────────────────────────────────────
function TestimonialCard({ name, role, text, rating }: { name: string; role: string; text: string; rating: number }) {
  return (
    <div className="slide-up-fade stagger-2">
      <NeuCard>
        <div className="pt-2">
          <p className="text-muted-foreground text-sm opacity-60">{text}</p>
          <div className="flex gap-1 mt-3">
            {[...Array(5)].map((_, i) => (
              <span key={i} className={`w-2 h-2 rounded-full ${i < rating ? "primary" : "muted-foreground"} `} />
            ))}
          </div>
          <div className="flex gap-2 mt-2">
            <span className="text-xs text-muted-foreground">{name}</span>
            <span className="text-xs text-muted-foreground">{role}</span>
          </div>
        </div>
      </NeuCard>
    </div>
  );
}

// ─── NavBar ──────────────────────────────────────────────────────────────────
function NavBar() {
  const [open, setOpen] = React.useState(false);
  const [scrolled, setScrolled] = React.useState(false);
  React.useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <header className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${scrolled ? "bg-background/80 backdrop-blur-2xl border-b border-border/50 shadow-sm" : "bg-transparent"}`}>
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <a href="#" className="flex items-center gap-2 group" id="nav-logo">
          <div className="w-8 h-8 rounded-xl gradient-wellness flex items-center justify-center shadow-sm group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
            <Leaf className="w-4 h-4 text-white" />
          </div>
          <span className="text-xl font-black text-gradient-wellness" style={{ fontFamily: "var(--font-outfit)" }}>NutriAI</span>
        </a>

        <ul className="hidden md:flex items-center gap-7">
          <li><a href="#chat" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors relative group">Chat<span className="absolute -bottom-0.5 left-0 w-0 h-px bg-primary group-hover:w-full transition-all duration-300" /></a></li>
        </ul>

        <div className="flex items-center gap-2.5">
          <ThemeToggle onChange={m => document.documentElement.classList.toggle("dark", m === "dark")} />
          <a href="#chat" id="nav-cta" className="hidden md:inline-flex items-center gap-1.5 gradient-wellness text-white text-sm font-bold px-5 py-2 rounded-full shadow-md hover:opacity-90 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200">
            Try NutriAI <Sparkles className="w-3.5 h-3.5" />
          </a>
          <button id="nav-menu" onClick={() => setOpen(!open)} className="md:hidden p-2 rounded-lg text-muted-foreground hover:bg-accent/30 transition-colors">
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="md:hidden bg-background/95 backdrop-blur-2xl border-b border-border/60 px-4 pb-4">
          <ul className="flex flex-col gap-1 pt-2">
            <li><a href="#chat" onClick={() => setOpen(false)} className="block px-3 py-2.5 text-sm font-medium text-foreground/80 hover:text-primary hover:bg-primary/8 rounded-xl transition-colors">Chat</a></li>
            <li className="pt-2"><a href="#chat" className="flex items-center justify-center gap-2 gradient-wellness text-white text-sm font-bold px-5 py-2.5 rounded-full">Try NutriAI <Sparkles className="w-3.5 h-3.5" /></a></li>
          </ul>
        </div>
      )}
    </header>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Home() {
  React.useEffect(() => {
    const prefersDark = typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const stored = localStorage.getItem("theme");
    const mode = stored ? stored === "dark" ? "dark" : "light" : prefersDark ? "dark" : "light";
    document.documentElement.classList.toggle("dark", mode === "dark");
  }, []);

  return (
    <>
      <FloatingPetals />
      <NavBar />
      <main className="flex-1 relative z-10">
        <GradientOrb className="top-1/4 -left-40 w-[400px] h-[400px] opacity-20" style={{ background: "radial-gradient(circle, oklch(0.92 0.04 145), oklch(0.95 0.03 175))", animationDelay: "0s" }} />
        <GradientOrb className="bottom-1/4 -right-40 w-[300px] h-[300px] opacity-15" style={{ background: "radial-gradient(circle, oklch(0.94 0.03 280), oklch(0.92 0.02 200))", animationDelay: "2.5s" }} />
        <GradientOrb className="top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] opacity-8 blur-[100px]" style={{ background: "radial-gradient(circle, oklch(0.96 0.02 145), transparent)", animationDelay: "1s" }} />

        {/* Floating leaves */}
        {[0, 1].map(i => (
          <div key={i} aria-hidden className={`absolute rounded-full bg-primary/5 flex items-center justify-center animate-float`}
            style={{ top: `${[15, 70][i]}%`, [["right", "left"][i]]: `${[12, 30][i]}%`, width: `${[40, 32][i]}px`, height: `${[40, 32][i]}px`, animationDelay: `${i * 2}s` }}>
            <Leaf className="w-4 h-4 text-primary/40" />
          </div>
        ))}

        {/* Hero/Intro Section */}
        <section className="py-24 px-4 max-w-7xl mx-auto">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-black text-foreground mb-4" style={{ fontFamily: "var(--font-outfit)" }}>
              Calm <span className="text-primary">Wellness</span>
            </h1>
            <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
              Your personal guide to meditation, fitness tracking, and holistic health
            </p>
          </div>
        </section>

        {/* Features Showcase */}
        <section className="py-16 px-4 bg-gradient-to-b from-[--background] to-[--card]">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-foreground mb-4" style={{ fontFamily: "var(--font-outfit)" }}>Wellness Features</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Track your meditation progress, monitor fitness goals, and maintain holistic wellness
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <FeatureItem
                icon=<Leaf className="w-5 h-5 text-primary/60" />
                title="Meditation Timer"
                description="Track your meditation sessions with customizable timers and gentle interval bells"
              />
              <FeatureItem
                icon=<Activity className="w-5 h-5 text-primary/60" />
                title="Fitness Tracking"
                description="Monitor your daily activity, steps, and exercise progress with smart analytics"
              />
              <FeatureItem
                icon=<Brain className="w-5 h-5 text-primary/60" />
                title="Wellness Journal"
                description="Log your mood, meals, and reflections daily with smart suggestions"
              />
            </div>
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="py-16 px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-foreground mb-4" style={{ fontFamily: "var(--font-outfit)" }}>What Users Say</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Join thousands who've transformed their wellness journey
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <TestimonialCard
                name="Sarah Johnson"
                role="Meditation Practitioner"
                text="The meditation timer has transformed my daily practice. I've been consistent for 3 months straight!"
                rating={5}
              />
              <TestimonialCard
                name="Mike Chen"
                role="Fitness Enthusiast"
                text="Fitness tracking integration with my Apple Watch is seamless. Love the analytics!"
                rating={4}
              />
              <TestimonialCard
                name="Emma Williams"
                role="Wellness Coach"
                text="The wellness journal helps me track patterns I never noticed before. Highly recommended!"
                rating={5}
              />
            </div>
          </div>
        </section>

        {/* App Download CTAs */}
        <section className="py-16 px-4 bg-gradient-to-b from-[--primary]/10 to-[--secondary]/10">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-black text-foreground mb-4" style={{ fontFamily: "var(--font-outfit)" }}>
                Start Your Wellness Journey
              </h2>
              <p className="text-muted-foreground text-lg max-w-xl mx-auto">
                Download the app and begin your path to better health today
              </p>
            </div>

            </div>
        </section>

        {/* Chat Section */}
        <section id="chat" className="py-24 px-4 bg-gradient-to-b from-[--primary]/5 to-[--secondary]/5">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <span className="inline-block text-xs font-bold tracking-widest uppercase text-primary/70 bg-primary/8 px-4 py-1.5 rounded-full mb-4 border border-primary/15">
                <Sparkles className="w-3 h-3 inline mr-1" />AI Wellness Assistant
              </span>
              <h2 className="text-4xl md:text-5xl font-black text-foreground mb-4" style={{ fontFamily: "var(--font-outfit)" }}>
                Chat with <span className="text-primary">NutriAI</span>
              </h2>
              <p className="text-muted-foreground text-lg">
                Ask about nutrition, meditation, or fitness goals
              </p>
            </div>
            <div>
              <NutritionChatbot apiUrl={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"} />
            </div>
          </div>
        </section>
      </main>

      <ThemeToggle
        onChange={(mode) => document.documentElement.classList.toggle("dark", mode === "dark")}
      />
    </>
  );
}