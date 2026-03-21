import type { AssetAmount } from "../types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const fmtUSD = (v: number | null): string => {
  if (v == null) return "—";
  if (v >= 1_000_000) return "$" + (v / 1_000_000).toFixed(2) + "M";
  if (v >= 1_000) return "$" + (v / 1_000).toFixed(1) + "k";
  return "$" + Math.round(v);
};

export const fmtUSDFull = (v: number): string =>
  "$" + v.toLocaleString("en-US", { maximumFractionDigits: 0 });

export const fmtDate = (iso: string): string => {
  const dt = new Date(iso + "T00:00:00");
  if (Number.isNaN(dt.getTime())) return iso;
  const mo = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return mo[dt.getMonth()] + " '" + String(dt.getFullYear()).slice(2);
};

export const fmtRelative = (iso: string): string => {
  const diff = Date.now() - new Date(iso).getTime();
  if (Number.isNaN(diff)) return iso;
  const days = Math.floor(diff / 86_400_000);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return days + " days ago";
  if (days < 365) return Math.floor(days / 30) + " mo ago";
  return Math.floor(days / 365) + " yr ago";
};

export const fmtETH = (v: number | null): string =>
  v == null || v === 0 ? "—" : v.toFixed(2) + " ETH";

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "Unknown date";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value.slice(0, 10);
  }
  return `${MONTHS[parsed.getUTCMonth()]} ${parsed.getUTCDate()}, ${parsed.getUTCFullYear()}`;
}

export function shortAddress(address: string): string {
  if (!address || address.length < 12) {
    return address;
  }
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export function titleCase(value: string): string {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}

export function formatLabel(value: string | null | undefined): string {
  if (!value) {
    return "";
  }
  return value
    .replace(/[_-]+/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .map((chunk) => (/^[A-Z0-9]+$/.test(chunk) ? chunk : chunk.charAt(0).toUpperCase() + chunk.slice(1)))
    .join(" ");
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatUsd(value: number | null | undefined): string | null {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return null;
  }
  const absolute = Math.abs(value);
  const decimals = absolute >= 1000 ? 0 : absolute >= 10 ? 2 : 4;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatAssetSymbol(symbol: string | null | undefined, tokenContract?: string | null): string {
  const clean = String(symbol ?? "").trim().toUpperCase();
  if (!clean) {
    return tokenContract ? `TOKEN ${shortAddress(tokenContract).replace("...", " ")}` : "UNKNOWN";
  }
  const tokenMatch = clean.match(/^TOKEN-([A-Z0-9]{4,})$/);
  if (tokenMatch) {
    return `TOKEN ${tokenMatch[1]}`;
  }
  if (/^0X[A-F0-9]{6,}$/.test(clean)) {
    return `TOKEN ${clean.slice(2, 8)}`;
  }
  return clean;
}

export function assetTone(symbol: string | null | undefined): string {
  const clean = String(symbol ?? "").trim().toUpperCase();
  if (clean === "ETH") {
    return "eth";
  }
  if (clean === "USDC") {
    return "usdc";
  }
  if (clean === "GNARS") {
    return "gnars";
  }
  if (clean === "SENDIT") {
    return "sendit";
  }
  if (clean.startsWith("TOKEN-") || /^0X[A-F0-9]{6,}$/.test(clean)) {
    return "token";
  }
  return clean.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "unknown";
}

export function formatAssetDescriptor(
  symbol: string | null | undefined,
  assetKind?: string | null,
  tokenContract?: string | null,
): string {
  const tone = assetTone(symbol);
  if (assetKind === "native") {
    return "Native";
  }
  if (assetKind === "erc20") {
    if (tone === "token") {
      return tokenContract ? `Unverified ERC-20 · ${shortAddress(tokenContract)}` : "Unverified ERC-20";
    }
    return tokenContract ? `ERC-20 · ${shortAddress(tokenContract)}` : "ERC-20";
  }
  return tokenContract ? shortAddress(tokenContract) : "";
}

export function formatAmount(symbol: string, amount: number, tokenContract?: string | null): string {
  const absolute = Math.abs(amount);
  const decimals = absolute >= 100 ? 0 : absolute >= 10 ? 1 : absolute >= 1 ? 2 : 4;
  const formatted = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(amount);
  return `${formatted} ${formatAssetSymbol(symbol, tokenContract)}`;
}

export function primaryAssetLabel(items: AssetAmount[]): string {
  if (!items.length) {
    return "No treasury flows";
  }
  const [primary] = [...items].sort((left, right) => right.amount - left.amount);
  return formatAmount(primary.symbol, primary.amount);
}

export function trimZeroes(value: string): string {
  return value.replace(/\.0+$/, "").replace(/(\.\d*?)0+$/, "$1");
}
