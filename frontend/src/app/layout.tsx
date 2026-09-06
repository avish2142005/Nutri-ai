import type { Metadata } from "next";
import { Geist, Geist_Mono, Outfit } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "NutriAI — AI-Powered Nutrition Analyzer",
  description:
    "A full-stack platform for fitness enthusiasts to log meals, get real-time nutrition breakdowns, and receive personalized AI-generated dietary insights grounded in your history and goals.",
  keywords: [
    "nutrition analyzer",
    "AI nutrition",
    "meal tracking",
    "fitness",
    "health",
    "carbon footprint",
    "diet insights",
  ],
  openGraph: {
    title: "NutriAI — AI-Powered Nutrition Analyzer",
    description:
      "Log meals, get real-time nutrition breakdowns, and receive personalized AI dietary insights.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${outfit.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
