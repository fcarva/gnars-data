import type { PagePayload } from "./types";

declare global {
  interface Window {
    __GNARS_PAGE_PAYLOAD__?: PagePayload;
  }
}

export {};
