import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, parseISO, formatDistanceToNowStrict } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatGBP(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
  }).format(value);
}

export function formatDate(
  dateString: string | null | undefined,
  includeTime: boolean = true,
): string {
  if (!dateString) return "-";
  try {
    const date = parseISO(dateString);
    return format(date, includeTime ? "dd MMM yyyy, HH:mm" : "dd MMM yyyy");
  } catch (error) {
    return dateString;
  }
}

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return formatDistanceToNowStrict(parseISO(iso), { addSuffix: true });
  } catch {
    return iso;
  }
}
