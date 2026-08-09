import type { ReactNode } from "react";

export function PageHeader({
  index,
  title,
  children,
}: {
  index: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <header className="mb-16 max-w-[62ch]">
      <p className="mb-4 text-[0.6875rem] uppercase tracking-widest text-ink-3">{index}</p>
      <h1 className="mb-6 text-[2rem] font-semibold leading-[1.18] tracking-tight text-ink sm:text-[2.375rem]">
        {title}
      </h1>
      <p className="text-[1.0625rem] leading-[1.65] text-ink">{children}</p>
    </header>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-20">
      <h2 className="mb-6 border-t border-rule pt-3 text-[1.25rem] font-semibold tracking-tight text-ink">
        {title}
      </h2>
      {children}
    </section>
  );
}
