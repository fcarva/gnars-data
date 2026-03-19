import { StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import "./styles.css";
import { renderPage } from "./renderPage";

const payload = window.__GNARS_PAGE_PAYLOAD__;
const root = document.getElementById("root");

if (payload && root) {
  hydrateRoot(root, <StrictMode>{renderPage(payload)}</StrictMode>);
}
