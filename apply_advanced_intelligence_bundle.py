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

    if "AdvancedIntelligenceService" not in text:
        anchor = (
            "from app.copilot_service "
            "import CopilotService\n"
        )
        imports = anchor + """from app.advanced_intelligence_service import (
    AdvancedIntelligenceService,
)
from app.bayesian_confidence_service import (
    BayesianConfidenceService,
)
from app.explainable_decision_service import (
    ExplainableDecisionService,
)
from app.market_regime_service import (
    MarketRegimeService,
)
from app.multi_timeframe_service import (
    MultiTimeframeService,
)
"""
        text = replace_once(
            text,
            anchor,
            imports,
        )

    if (
        "def create_advanced_"
        "intelligence_service("
        not in text
    ):
        text += """


def create_advanced_intelligence_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> AdvancedIntelligenceService:
    thesis_service = (
        create_investment_thesis_service(
            database_path=database_path
        )
    )
    outcome_service = (
        create_decision_outcome_service(
            database_path=database_path
        )
    )

    def bars(
        symbol: str,
        output_size: int,
    ):
        return (
            create_technical_historical_client()
            .get_daily_bars(
                symbol=symbol,
                output_size=output_size,
            )
        )

    def aggregate(
        daily_bars,
        group_size: int,
    ):
        grouped = []

        for index in range(
            0,
            len(daily_bars),
            group_size,
        ):
            chunk = daily_bars[
                index:index + group_size
            ]

            if not chunk:
                continue

            grouped.append(
                type(chunk[0])(
                    symbol=chunk[0].symbol,
                    trading_date=(
                        chunk[-1].trading_date
                    ),
                    open_price=(
                        chunk[0].open_price
                    ),
                    high_price=max(
                        item.high_price
                        for item in chunk
                    ),
                    low_price=min(
                        item.low_price
                        for item in chunk
                    ),
                    close_price=(
                        chunk[-1].close_price
                    ),
                    volume=sum(
                        item.volume
                        for item in chunk
                    ),
                )
            )

        return grouped

    def timeframe_series(
        symbol: str,
    ):
        daily = bars(
            symbol,
            500,
        )

        return {
            "MONTHLY": aggregate(
                daily,
                21,
            ),
            "WEEKLY": aggregate(
                daily,
                5,
            ),
            "DAILY": daily,
        }

    return AdvancedIntelligenceService(
        regime_series_provider=(
            lambda: {
                symbol: bars(
                    symbol,
                    260,
                )
                for symbol in (
                    "SPY",
                    "QQQ",
                    "TLT",
                )
            }
        ),
        timeframe_series_provider=(
            timeframe_series
        ),
        theses_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in thesis_service
                .get_report()
                .theses
            )
        ),
        outcomes_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in outcome_service
                .overview(
                    limit=1000
                )
                .latest
            )
        ),
        regime_service=(
            MarketRegimeService()
        ),
        timeframe_service=(
            MultiTimeframeService()
        ),
        calibration_service=(
            BayesianConfidenceService()
        ),
        explanation_service=(
            ExplainableDecisionService()
        ),
    )
"""

    DEPENDENCIES.write_text(
        text,
        encoding="utf-8",
    )


def patch_app() -> None:
    text = APP.read_text(
        encoding="utf-8"
    )

    if (
        "create_advanced_"
        "intelligence_service"
        not in text
    ):
        text = replace_once(
            text,
            "    create_copilot_service,\n",
            (
                "    create_copilot_service,\n"
                "    create_advanced_"
                "intelligence_service,\n"
            ),
        )

    if (
        '"/api/copilot/'
        'advanced-intelligence"'
        not in text
    ):
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""
        route = """    @app.get(
        "/api/copilot/advanced-intelligence",
        tags=["copilot"],
    )
    def advanced_intelligence(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_advanced_intelligence_service()
            .report()
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
        "useAdvancedIntelligence"
        not in text
    ):
        react_end = text.find(
            "\n\n"
        )
        text = (
            text[:react_end + 2]
            + 'import {\n'
            + '  useAdvancedIntelligence,\n'
            + '} from "@/hooks/'
            + 'useAdvancedIntelligence";\n\n'
            + text[react_end + 2:]
        )

    if (
        "AdvancedIntelligencePanel"
        not in text
    ):
        marker = (
            '} from "@/components/'
            'copilot/'
            'AdaptiveIntelligencePanel";'
        )
        text = replace_once(
            text,
            marker,
            marker
            + '\nimport {\n'
            + '  AdvancedIntelligencePanel,\n'
            + '} from "@/components/'
            + 'copilot/'
            + 'AdvancedIntelligencePanel";',
        )

    if (
        "const advancedIntelligenceQuery"
        not in text
    ):
        marker = (
            "  const adaptiveIntelligenceQuery =\n"
            "    useAdaptiveIntelligence();\n"
        )
        text = replace_once(
            text,
            marker,
            marker
            + "\n"
            + "  const advancedIntelligenceQuery =\n"
            + "    useAdvancedIntelligence();\n",
        )

    if (
        "<AdvancedIntelligencePanel"
        not in text
    ):
        anchor = (
            "          {conversation.map(\n"
        )
        panel = """          {advancedIntelligenceQuery.data && (
            <AdvancedIntelligencePanel
              report={
                advancedIntelligenceQuery.data
              }
              refreshing={
                advancedIntelligenceQuery
                  .isFetching
              }
              onRefresh={() => {
                void advancedIntelligenceQuery
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
                "the trading-bot project root."
            )

    patch_dependencies()
    patch_app()
    patch_page()

    print(
        "Advanced Intelligence Bundle "
        "integrated."
    )


if __name__ == "__main__":
    main()
