import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: {
    default: "Cape Town and Enschede — what limits building",
    template: "%s · Cape Town and Enschede",
  },
  description:
    "Two cities that are hard to build in for opposite reasons. Cape Town has run out of land; Enschede has plenty and still cannot build. What kind of limit you have decides what you can do about it.",
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
              Every number on this site says how solid it is — official, derived, engineering
              or estimate — and where it came from. Where a number is only an estimate, the
              point it supports is written so it still holds if the number changes. If it
              would not hold, it is not made.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
