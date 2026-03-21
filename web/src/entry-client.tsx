import { StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import "./styles.css";
import "./styles-modern.css";
import App from "./App";

const root = document.getElementById("root");

if (root) {
  hydrateRoot(root, <StrictMode><App /></StrictMode>);
}
