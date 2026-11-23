import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RailBlock AI - Neuro-Symbolic Railway Maintenance Operations",
  description:
    "Operations Control & Dispatch Dashboard for Railway Maintenance Scheduling, Asset Risk Prediction, and Constraint Verification",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="w-full">
      <body className="w-full bg-[#585d94] text-slate-900 antialiased selection:bg-purple-500/30">
        {children}
      </body>
    </html>
  );
}
