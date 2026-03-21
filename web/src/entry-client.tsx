import { StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import "./styles.css";
import "./styles-modern.css";
import { renderPage } from "./renderPage";
import App from "./App";

const payload = window.__GNARS_PAGE_PAYLOAD__;
const root = document.getElementById("root");

if (payload && root) {
  hydrateRoot(root, <StrictMode>{renderPage(payload)}</StrictMode>);
} else if (root) {
  hydrateRoot(root, <StrictMode><App /></StrictMode>);
}
