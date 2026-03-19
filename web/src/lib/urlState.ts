import { startTransition, useEffect, useState } from "react";

export function useUrlState<T extends Record<string, string>>(defaults: T): [T, (patch: Partial<T>) => void] {
  const [state, setState] = useState<T>(defaults);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const next = { ...defaults };
    for (const key of Object.keys(defaults)) {
      const value = params.get(key);
      if (value) {
        next[key as keyof T] = value as T[keyof T];
      }
    }
    setState(next);
  }, []);

  const update = (patch: Partial<T>) => {
    startTransition(() => {
      setState((current) => {
        const next = { ...current, ...patch };
        if (typeof window !== "undefined") {
          const params = new URLSearchParams(window.location.search);
          for (const [key, value] of Object.entries(next)) {
            if (!value || value === defaults[key as keyof T]) {
              params.delete(key);
            } else {
              params.set(key, value);
            }
          }
          const query = params.toString();
          const pathname = `${window.location.pathname}${query ? `?${query}` : ""}`;
          window.history.replaceState({}, "", pathname);
        }
        return next;
      });
    });
  };

  return [state, update];
}
