import { useState, useEffect } from "react";

export interface MarketStatus {
  isOpen: boolean;
  exchange: string;
  countdown: string;
  timeET: string;
}

/** Compute NYSE market status for a given UTC Date. */
function computeMarketStatus(now: Date): MarketStatus {
  // Parse current ET time using the browser's Intl engine (handles DST correctly).
  const etParts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "numeric",
    second: "numeric",
    hour12: false,
    weekday: "short",
  }).formatToParts(now);

  const get = (type: string) =>
    parseInt(etParts.find((p) => p.type === type)?.value ?? "0", 10);

  const weekdayStr = etParts.find((p) => p.type === "weekday")?.value ?? "";
  const h = get("hour");
  const m = get("minute");
  const s = get("second");
  const currentMinutes = (h === 24 ? 0 : h) * 60 + m;

  const OPEN = 9 * 60 + 30;
  const CLOSE = 16 * 60;
  const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  const ALL_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const isWeekday = WEEKDAYS.includes(weekdayStr);
  const isOpen = isWeekday && currentMinutes >= OPEN && currentMinutes < CLOSE;

  const timeET = `${String(h === 24 ? 0 : h).padStart(2, "0")}:${String(m).padStart(2, "0")} ET`;

  let countdown = "";
  if (isOpen) {
    const secs = (CLOSE - currentMinutes) * 60 - s;
    const hh = Math.floor(secs / 3600);
    const mm = Math.floor((secs % 3600) / 60);
    countdown = hh > 0 ? `${hh}h ${mm}m until close` : `${mm}m until close`;
  } else if (isWeekday && currentMinutes < OPEN) {
    const secs = (OPEN - currentMinutes) * 60 - s;
    const hh = Math.floor(secs / 3600);
    const mm = Math.floor((secs % 3600) / 60);
    countdown = hh > 0 ? `Opens in ${hh}h ${mm}m` : `Opens in ${mm}m`;
  } else {
    // Weekend or after close — find next weekday
    const dayIndex = ALL_DAYS.indexOf(weekdayStr);
    let offset = 1;
    while (true) {
      const nextDay = ALL_DAYS[(dayIndex + offset) % 7];
      if (WEEKDAYS.includes(nextDay)) {
        countdown = `Opens ${nextDay} 09:30 ET`;
        break;
      }
      offset++;
      if (offset > 7) break;
    }
  }

  return { isOpen, exchange: "NYSE", countdown, timeET };
}

/** Returns live NYSE market status, updating every second. */
export function useMarketStatus(): MarketStatus {
  const [status, setStatus] = useState<MarketStatus>(() =>
    computeMarketStatus(new Date()),
  );

  useEffect(() => {
    const tick = () => setStatus(computeMarketStatus(new Date()));
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return status;
}
