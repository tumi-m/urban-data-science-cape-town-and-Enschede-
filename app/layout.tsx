import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: {
    default: "Enschede — spatial constraints",
    template: "%s · Enschede spatial constraints",
  },
  description:
    "A constraint analysis of Enschede in the unit economics of land, nitrogen and energy: which limits on the city are boundaries, which are scalar fields, and what follows from the difference.",
};

/**
 * Applied before first paint so a stamped theme choice never flashes the other
 * mode. Kept to the one job; anything else here delays the paint it protects.
 */
const THEME_BOOTSTRAP = `try{var t=localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
      </head>
      <body className="min-h-screen antialiased">
        <Nav />
        <main className="mx-auto max-w-6xl px-6 pb-32 pt-12">{children}</main>
        <footer className="border-t border-rule">
          <div className="mx-auto max-w-6xl px-6 py-8 text-[0.75rem] leading-relaxed text-ink-3">
            <p className="max-w-[62ch]">
              Every figure on this site carries a class — official, derived, engineering or
              estimate — and the source it came from. Where a figure is an estimate, the
              conclusion it supports is written to survive its replacement, or it is not
              drawn.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
