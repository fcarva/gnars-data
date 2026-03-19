import { renderToString } from "react-dom/server";
import type { PagePayload } from "./types";
import { renderPage } from "./renderPage";

export function renderPageMarkup(payload: PagePayload): string {
  return renderToString(renderPage(payload));
}
