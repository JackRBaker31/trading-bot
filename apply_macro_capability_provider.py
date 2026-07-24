from pathlib import Path


ROOT = Path.cwd()
DEPENDENCIES = ROOT / "web" / "dependencies.py"
APP = ROOT / "web" / "app.py"
PAGE = ROOT / "frontend" / "src" / "pages" / "CopilotPage.tsx"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected one match, found {count}: {old[:100]!r}"
        )
    return text.replace(old, new, 1)


def patch_dependencies() -> None:
    text = DEPENDENCIES.read_text(encoding="utf-8")

    if "MacroCapabilityProvider" not in text:
        anchor = "from app.copilot_service import CopilotService\n"
        imports = (
            anchor
            + "from app.macro_analysis_service import MacroAnalysisService\n"
            + "from app.macro_capability_provider import MacroCapabilityProvider\n"
        )
        text = replace_once(text, anchor, imports)

    if "def create_macro_analysis_service(" not in text:
        text += """


def create_macro_analysis_service(
) -> MacroAnalysisService:
    return MacroAnalysisService()


def create_macro_capability_provider(
) -> MacroCapabilityProvider:
    return MacroCapabilityProvider(
        bars_provider=(
            lambda symbol, output_size: (
                create_technical_historical_client()
                .get_daily_bars(
                    symbol=symbol,
                    output_size=output_size,
                )
            )
        ),
        analysis_service=(
            create_macro_analysis_service()
        ),
    )
"""

    old_provider = """            UnavailableCapabilityProvider(
                capability="MACRO",
                maximum=10.0,
                summary=(
                    "Macro capability has "
                    "not yet been connected."
                ),
            ),
"""
    if old_provider in text:
        text = replace_once(
            text,
            old_provider,
            "            create_macro_capability_provider(),\n",
        )

    DEPENDENCIES.write_text(text, encoding="utf-8")


def patch_app() -> None:
    text = APP.read_text(encoding="utf-8")

    if "create_macro_capability_provider" not in text:
        text = replace_once(
            text,
            "    create_copilot_service,\n",
            (
                "    create_copilot_service,\n"
                "    create_macro_capability_provider,\n"
            ),
        )

    if '"/api/copilot/macro-analysis"' not in text:
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""
        route = """    @app.get(
        "/api/copilot/macro-analysis",
        tags=["copilot"],
    )
    def macro_analysis(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_macro_capability_provider()
            .get_analysis()
            .to_dictionary()
        )


"""
        text = replace_once(text, marker, route + marker)

    APP.write_text(text, encoding="utf-8")


def patch_page() -> None:
    text = PAGE.read_text(encoding="utf-8")

    if "useMacroAnalysis" not in text:
        react_end = text.find("\n\n")
        text = (
            text[:react_end + 2]
            + 'import {\n'
            + '  useMacroAnalysis,\n'
            + '} from "@/hooks/useMacroAnalysis";\n\n'
            + text[react_end + 2:]
        )

    if "MacroAnalysisPanel" not in text:
        marker = (
            '} from "@/components/copilot/TechnicalAnalysisPanel";'
        )
        text = replace_once(
            text,
            marker,
            (
                marker
                + '\nimport {\n'
                + '  MacroAnalysisPanel,\n'
                + '} from "@/components/copilot/MacroAnalysisPanel";'
            ),
        )

    if "const macroAnalysisQuery" not in text:
        marker = (
            "  const technicalAnalysisQuery =\n"
            "    useTechnicalAnalysis(\n"
            "      technicalSymbol,\n"
            "    );\n"
        )
        text = replace_once(
            text,
            marker,
            marker
            + "\n"
            + "  const macroAnalysisQuery =\n"
            + "    useMacroAnalysis();\n",
        )

    if "<MacroAnalysisPanel" not in text:
        anchor = "          {conversation.map(\n"
        panel = """          {macroAnalysisQuery.data && (
            <MacroAnalysisPanel
              analysis={
                macroAnalysisQuery.data
              }
              refreshing={
                macroAnalysisQuery
                  .isFetching
              }
              onRefresh={() => {
                void macroAnalysisQuery
                  .refetch();
              }}
            />
          )}

"""
        text = replace_once(text, anchor, panel + anchor)

    PAGE.write_text(text, encoding="utf-8")


def main() -> None:
    for path in (DEPENDENCIES, APP, PAGE):
        if not path.exists():
            raise FileNotFoundError(
                "Run this script from the trading-bot project root."
            )

    patch_dependencies()
    patch_app()
    patch_page()
    print("Macro Capability Provider integrated.")


if __name__ == "__main__":
    main()
