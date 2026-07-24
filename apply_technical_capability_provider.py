from pathlib import Path


ROOT = Path.cwd()
DEPENDENCIES = ROOT / "web" / "dependencies.py"
APP = ROOT / "web" / "app.py"
PAGE = (
    ROOT
    / "frontend"
    / "src"
    / "pages"
    / "CopilotPage.tsx"
)


def replace_once(
    text: str,
    old: str,
    new: str,
) -> str:
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"Expected one match, "
            f"found {count}: "
            f"{old[:100]!r}"
        )

    return text.replace(
        old,
        new,
        1,
    )


def patch_dependencies() -> None:
    text = DEPENDENCIES.read_text(
        encoding="utf-8"
    )

    if (
        "TechnicalCapabilityProvider"
        not in text
    ):
        anchor = (
            "from app.copilot_service "
            "import CopilotService\n"
        )

        imports = (
            anchor
            + "from app."
            "technical_analysis_service "
            "import "
            "TechnicalAnalysisService\n"
            "from app."
            "technical_capability_provider "
            "import "
            "TechnicalCapabilityProvider\n"
            "from app."
            "twelve_data_historical_data "
            "import "
            "TwelveDataHistoricalDataClient\n"
        )

        text = replace_once(
            text,
            anchor,
            imports,
        )

    if (
        "def create_technical_"
        "historical_client("
        not in text
    ):
        text += """
\n\ndef create_technical_historical_client(
) -> TwelveDataHistoricalDataClient:
    import os

    api_key = os.getenv(
        "TWELVE_DATA_API_KEY"
    )

    if (
        api_key is None
        or not api_key.strip()
    ):
        raise RuntimeError(
            "TWELVE_DATA_API_KEY was not "
            "found in the environment."
        )

    return TwelveDataHistoricalDataClient(
        api_key=api_key,
        timeout_seconds=15.0,
        max_attempts=2,
    )


def create_technical_analysis_service(
) -> TechnicalAnalysisService:
    return TechnicalAnalysisService()
"""

    old_provider = """            UnavailableCapabilityProvider(
                capability="TECHNICAL",
                maximum=20.0,
                summary=(
                    "Technical capability "
                    "has not yet been connected."
                ),
            ),
"""

    new_provider = """            TechnicalCapabilityProvider(
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
                    create_technical_analysis_service()
                ),
            ),
"""

    if old_provider in text:
        text = replace_once(
            text,
            old_provider,
            new_provider,
        )

    DEPENDENCIES.write_text(
        text,
        encoding="utf-8",
    )


def patch_app() -> None:
    text = APP.read_text(
        encoding="utf-8"
    )

    if (
        "create_technical_"
        "historical_client"
        not in text
    ):
        text = replace_once(
            text,
            (
                "    create_copilot_service,\n"
            ),
            (
                "    create_copilot_service,\n"
                "    create_technical_"
                "historical_client,\n"
                "    create_technical_"
                "analysis_service,\n"
            ),
        )

    if (
        '"/api/copilot/'
        'technical-analysis/{symbol}"'
        not in text
    ):
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""

        route = """    @app.get(
        "/api/copilot/technical-analysis/{symbol}",
        tags=["copilot"],
    )
    def technical_analysis(
        symbol: str,
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        bars = (
            create_technical_historical_client()
            .get_daily_bars(
                symbol=symbol,
                output_size=260,
            )
        )

        return (
            create_technical_analysis_service()
            .analyse(
                symbol=symbol,
                bars=bars,
            )
            .to_dictionary()
        )


"""

        text = replace_once(
            text,
            marker,
            route + marker,
        )

    APP.write_text(
        text,
        encoding="utf-8",
    )


def patch_page() -> None:
    text = PAGE.read_text(
        encoding="utf-8"
    )

    if (
        "useTechnicalAnalysis"
        not in text
    ):
        react_end = text.find(
            "\n\n"
        )

        text = (
            text[:react_end + 2]
            + 'import {\n'
            + '  useTechnicalAnalysis,\n'
            + '} from "@/hooks/'
            + 'useTechnicalAnalysis";\n\n'
            + text[react_end + 2:]
        )

    if (
        "TechnicalAnalysisPanel"
        not in text
    ):
        marker = (
            '} from "@/components/'
            'copilot/'
            'InvestmentThesisPanel";'
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + '\nimport {\n'
                + '  TechnicalAnalysisPanel,\n'
                + '} from "@/components/'
                + 'copilot/'
                + 'TechnicalAnalysisPanel";'
            ),
        )

    if (
        "const technicalSymbol"
        not in text
    ):
        marker = (
            "  const investmentThesesQuery =\n"
            "    useInvestmentTheses();\n"
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + "\n"
                + "  const technicalSymbol =\n"
                + "    investmentThesesQuery.data"
                + "?.theses[0]?.symbol ?? null;\n\n"
                + "  const technicalAnalysisQuery =\n"
                + "    useTechnicalAnalysis(\n"
                + "      technicalSymbol,\n"
                + "    );\n"
            ),
        )

    if (
        "<TechnicalAnalysisPanel"
        not in text
    ):
        anchor = (
            "          {conversation.map(\n"
        )

        panel = """          {technicalAnalysisQuery.data && (
            <TechnicalAnalysisPanel
              analysis={
                technicalAnalysisQuery.data
              }
              refreshing={
                technicalAnalysisQuery
                  .isFetching
              }
              onRefresh={() => {
                void technicalAnalysisQuery
                  .refetch();
              }}
            />
          )}

"""

        text = replace_once(
            text,
            anchor,
            panel + anchor,
        )

    PAGE.write_text(
        text,
        encoding="utf-8",
    )


def main() -> None:
    for path in (
        DEPENDENCIES,
        APP,
        PAGE,
    ):
        if not path.exists():
            raise FileNotFoundError(
                "Run this script from "
                "the trading-bot "
                "project root."
            )

    patch_dependencies()
    patch_app()
    patch_page()

    print(
        "Technical Capability Provider "
        "integrated."
    )


if __name__ == "__main__":
    main()
