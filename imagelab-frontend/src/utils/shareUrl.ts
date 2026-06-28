export type ShareExpiryOption = "none" | "1" | "7" | "30";

export function getShareTokenFromUrl(): string | null {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("share")?.trim();
  return token || null;
}

export function buildShareUrl(token: string): string {
  const url = new URL(window.location.href);
  url.searchParams.set("share", token);
  return url.toString();
}

export function clearShareTokenFromUrl(): void {
  const url = new URL(window.location.href);
  url.searchParams.delete("share");
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
}

export function computeShareExpiresAt(option: ShareExpiryOption): string | undefined {
  if (option === "none") return undefined;
  const expires = new Date();
  expires.setDate(expires.getDate() + Number(option));
  return expires.toISOString();
}

export const SHARE_EXPIRY_LABELS: Record<ShareExpiryOption, string> = {
  none: "No expiry",
  "1": "1 day",
  "7": "7 days",
  "30": "30 days",
};
