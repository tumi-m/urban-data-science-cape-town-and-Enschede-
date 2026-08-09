"use client";

import { useEffect, useState } from "react";

/**
 * Element width, observed rather than assumed.
 *
 * Charts drawn at a guessed width overflow their column at exactly the sizes
 * nobody tests. The node is held in state rather than a ref so that the
 * observer re-attaches if the element is replaced, which is what happens when
 * a parent conditionally renders around it.
 */
export function useMeasure<T extends HTMLElement>() {
  const [node, setNode] = useState<T | null>(null);
  const [rect, setRect] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!node) return;
    const obs = new ResizeObserver(([entry]) => {
      const box = entry.contentRect;
      setRect({ width: box.width, height: box.height });
    });
    obs.observe(node);
    setRect({ width: node.clientWidth, height: node.clientHeight });
    return () => obs.disconnect();
  }, [node]);

  return [setNode, rect] as const;
}
