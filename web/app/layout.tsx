import type { Metadata } from "next";
import Link from "next/link";
import { Public_Sans } from "next/font/google";

import { Starfield } from "@/components/starfield";
import "./globals.css";

const publicSans = Public_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FlameCheck",
  description: "Fire-safety answers from NASA PSI microgravity combustion data, every claim cited.",
};

const NAV = [
  { href: "/", label: "Ask" },
  { href: "/explore", label: "Explore" },
  { href: "/about", label: "About" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${publicSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <Starfield />
        <header className="border-b border-border bg-background/60 backdrop-blur-md">
          <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
            <Link href="/" className="text-lg font-bold tracking-tight text-ink">
              FlameCheck
            </Link>
            <nav className="flex gap-1 text-sm">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="rounded-md px-3 py-1.5 text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <div className="flex flex-1 flex-col">{children}</div>
        <footer className="border-t border-border px-4 py-4 text-center text-xs text-muted-foreground">
          Data: NASA Physical Sciences Informatics (PSI) and NASA Technical Reports Server. Not an
          engineering safety review.
        </footer>
      </body>
    </html>
  );
}
