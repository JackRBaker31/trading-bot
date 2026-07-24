from pathlib import Path

ROOT = Path.cwd()
QUERY = ROOT / "app" / "research_query_service.py"
TYPES = ROOT / "frontend" / "src" / "lib" / "types.ts"
PAGE = ROOT / "frontend" / "src" / "pages" / "NewsPage.tsx"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected one match, found {count}: {old[:100]!r}"
        )
    return text.replace(old, new, 1)


def patch_query() -> None:
    text = QUERY.read_text(encoding="utf-8")
    if '"confidence_breakdown"' not in text:
        text = replace_once(
            text,
            '            "confidence": signal.confidence,\n',
            '            "confidence": signal.confidence,\n'
            '            "confidence_breakdown": [\n'
            '                factor.to_dictionary()\n'
            '                for factor in signal.confidence_breakdown\n'
            '            ],\n',
        )
    QUERY.write_text(text, encoding="utf-8")


def patch_types() -> None:
    text = TYPES.read_text(encoding="utf-8")
    if "export interface NewsConfidenceFactor" not in text:
        marker = "export interface NewsSignal {\n"
        addition = """export interface NewsConfidenceFactor {
  code: string;
  label: string;
  contribution: number;
  detail: string;
}

"""
        text = replace_once(text, marker, addition + marker)

    if "confidence_breakdown:" not in text:
        text = replace_once(
            text,
            "  confidence: number;\n  event_type: string;\n",
            "  confidence: number;\n"
            "  confidence_breakdown: NewsConfidenceFactor[];\n"
            "  event_type: string;\n",
        )
    TYPES.write_text(text, encoding="utf-8")


def patch_page() -> None:
    text = PAGE.read_text(encoding="utf-8")
    if "Confidence Breakdown" not in text:
        marker = "              {/* Reasoning summary */}\n"
        panel = """              {/* Confidence breakdown */}
              {signal.confidence_breakdown?.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                    Confidence Breakdown
                  </p>
                  <div className="space-y-2">
                    {signal.confidence_breakdown.map((factor) => (
                      <div
                        key={factor.code}
                        className="flex items-start justify-between gap-4 rounded-lg bg-muted/30 p-2.5"
                      >
                        <div>
                          <p className="text-xs font-medium">{factor.label}</p>
                          <p className="mt-0.5 text-[10px] leading-relaxed text-muted-foreground">
                            {factor.detail}
                          </p>
                        </div>
                        <span
                          className={cn(
                            "shrink-0 font-mono text-xs font-bold",
                            factor.contribution > 0
                              ? "text-emerald-400"
                              : factor.contribution < 0
                                ? "text-destructive"
                                : "text-muted-foreground",
                          )}
                        >
                          {factor.contribution > 0 ? "+" : ""}
                          {(factor.contribution * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

"""
        text = replace_once(text, marker, panel + marker)
    PAGE.write_text(text, encoding="utf-8")


def main() -> None:
    for path in (QUERY, TYPES, PAGE):
        if not path.exists():
            raise FileNotFoundError(
                "Run this script from the trading-bot project root."
            )
    patch_query()
    patch_types()
    patch_page()
    print("KAIRO News Confidence Engine integrated.")


if __name__ == "__main__":
    main()
