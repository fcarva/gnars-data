import { useDeferredValue, useEffect, useState } from "react";
import type { SearchEntry } from "../types";

export function SearchBox() {
  const [query, setQuery] = useState("");
  const [entries, setEntries] = useState<SearchEntry[]>([]);
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    let ignore = false;
    fetch("/data/search-index.json")
      .then((response) => response.json())
      .then((payload) => {
        if (!ignore) {
          setEntries(payload.records ?? []);
        }
      })
      .catch(() => {
        if (!ignore) {
          setEntries([]);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  const normalized = deferredQuery.trim().toLowerCase();
  const results =
    normalized.length < 2
      ? []
      : entries
          .filter((entry) => {
            const haystack = `${entry.title} ${entry.summary} ${entry.kind}`.toLowerCase();
            return haystack.includes(normalized);
          })
          .slice(0, 8);

  return (
    <div className="searchbox">
      <input
        aria-label="Search Gnars Camp"
        className="searchbox-input"
        placeholder="search people, proposals, projects, archive..."
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      {results.length > 0 ? (
        <div className="searchbox-results">
          {results.map((entry) => (
            <a key={`${entry.kind}:${entry.href}`} className="searchbox-item" href={entry.href}>
              <span className="searchbox-kind">{entry.kind}</span>
              <strong>{entry.title}</strong>
              <span>{entry.summary}</span>
            </a>
          ))}
        </div>
      ) : null}
    </div>
  );
}
