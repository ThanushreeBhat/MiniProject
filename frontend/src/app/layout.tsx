import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RailBlock AI - Operations Control",
  description: "Neuro-Symbolic Railway Maintenance Scheduling & Risk Prediction",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className="min-h-full flex flex-col bg-neutral-950 text-neutral-100 font-sans">
        {children}
      </body>
    </html>
  );
}
