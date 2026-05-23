import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(val: number, decimals = 3): string {
  return val.toFixed(decimals);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("id-ID", {
    day: "2-digit", month: "long", year: "numeric",
  });
}

export function statusColor(status: string) {
  if (status === "AMAN") return "text-engineering-green";
  if (status === "TIDAK AMAN") return "text-engineering-red";
  return "text-engineering-amber";
}

export function statusBg(status: string) {
  if (status === "AMAN") return "bg-green-50 text-green-700 border-green-200";
  if (status === "TIDAK AMAN") return "bg-red-50 text-red-700 border-red-200";
  return "bg-amber-50 text-amber-700 border-amber-200";
}
