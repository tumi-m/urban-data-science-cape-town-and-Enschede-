"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import type { Route } from "next";

const SECTIONS: { href: Route; label: string; index: string }[] = [
  { href: "/", label: "Thesis", index: "00" },
  { href: "/constraints", label: "Constraints", index: "01" },
  { href: "/nitrogen", label: "Nitrogen", index: "02" },
  { href: "/mobility", label: "Mobility", index: "03" },
  { href: "/access", label: "Access", index: "04" },
  { href: "/border", label: "Border", index: "05" },
  { href: "/energy", label: "Energy", index: "06" },
  { href: "/methods", label: "Method", index: "07" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-rule bg-surface-1/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
        <Link href="/" className="shrink-0 text-[0.8125rem] font-semibold tracking-tight">
          Enschede
          <span className="ml-1.5 font-normal text-ink-3">spatial constraints</span>
        </Link>

        <nav className="scroll-x -mx-2 flex-1">
          <ul className="flex items-baseline gap-1 px-2">
            {SECTIONS.map((s) => {
              const active = pathname === s.href;
              return (
                <li key={s.href}>
                  <Link
                    href={s.href}
                    aria-current={active ? "page" : undefined}
                    className={`inline-flex items-baseline gap-1.5 whitespace-nowrap rounded px-2 py-1 text-[0.8125rem] transition-colors ${
                      active ? "text-ink" : "text-ink-3 hover:text-ink-2"
                    }`}
                  >
                    <span className="text-[0.625rem] tabular-nums opacity-60">{s.index}</span>
                    {s.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <ThemeToggle />
      </div>
    </header>
  );
}

function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark" | null>(null);

  useEffect(() => {
    const stamped = document.documentElement.getAttribute("data-theme");
    if (stamped === "light" || stamped === "dark") setTheme(stamped);
  }, []);

  function toggle() {
    const resolved =
      theme ??
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = resolved === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("theme", next);
    } catch {
      /* Private browsing. The choice simply does not persist. */
    }
    setTheme(next);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      className="shrink-0 rounded border border-rule px-2 py-1 text-[0.6875rem] uppercase tracking-widest text-ink-3 transition-colors hover:text-ink-2"
      aria-label="Switch colour scheme"
    >
      {theme === "dark" ? "Light" : "Dark"}
    </button>
  );
}
