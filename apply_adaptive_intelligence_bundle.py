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
        "AdaptiveIntelligenceService"
        not in text
    ):
        anchor = (
            "from app.copilot_service "
            "import CopilotService\n"
        )
        imports = anchor + """from app.adaptive_intelligence_service import (
    AdaptiveIntelligenceService,
)
from app.investment_committee_service import (
    InvestmentCommitteeService,
)
from app.performance_intelligence_service import (
    PerformanceIntelligenceService,
)
from app.portfolio_optimisation_service import (
    PortfolioOptimisationService,
)
from app.position_sizing_service import (
    PositionSizingService,
)
from app.risk_attribution_service import (
    RiskAttributionService,
)
from app.strategy_evolution_repository import (
    StrategyEvolutionRepository,
)
from app.strategy_evolution_service import (
    StrategyEvolutionService,
)
"""
        text = replace_once(
            text,
            anchor,
            imports,
        )

    if (
        "def create_adaptive_"
        "intelligence_service("
        not in text
    ):
        text += """


def create_adaptive_intelligence_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> AdaptiveIntelligenceService:
    memory_service = (
        create_decision_memory_service(
            database_path=database_path
        )
    )
    outcome_service = (
        create_decision_outcome_service(
            database_path=database_path
        )
    )
    thesis_service = (
        create_investment_thesis_service(
            database_path=database_path
        )
    )
    operations_service = (
        create_operations_query_service()
    )

    performance_service = (
        PerformanceIntelligenceService()
    )
    evolution_service = (
        StrategyEvolutionService(
            repository=(
                StrategyEvolutionRepository(
                    database_path=database_path
                )
            )
        )
    )
    evolution_service.initialize()

    return AdaptiveIntelligenceService(
        decisions_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in memory_service.recent(
                    limit=500
                )
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
        theses_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in thesis_service
                .get_report()
                .theses
            )
        ),
        portfolio_provider=(
            lambda: (
                operations_service
                .get_portfolio()
                .to_dictionary()
            )
        ),
        risk_provider=(
            lambda: (
                operations_service
                .get_risk_status()
                .to_dictionary()
            )
        ),
        performance_service=(
            performance_service
        ),
        portfolio_service=(
            PortfolioOptimisationService()
        ),
        risk_service=(
            RiskAttributionService()
        ),
        sizing_service=(
            PositionSizingService(
                performance_service=(
                    performance_service
                )
            )
        ),
        committee_service=(
            InvestmentCommitteeService()
        ),
        evolution_service=(
            evolution_service
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
        "create_adaptive_"
        "intelligence_service"
        not in text
    ):
        text = replace_once(
            text,
            "    create_copilot_service,\n",
            (
                "    create_copilot_service,\n"
                "    create_adaptive_"
                "intelligence_service,\n"
            ),
        )

    if (
        '"/api/copilot/'
        'adaptive-intelligence"'
        not in text
    ):
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""
        routes = """    @app.get(
        "/api/copilot/adaptive-intelligence",
        tags=["copilot"],
    )
    def adaptive_intelligence(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_adaptive_intelligence_service()
            .report()
            .to_dictionary()
        )


    @app.post(
        "/api/copilot/strategy-evolution/propose",
        tags=["copilot"],
    )
    def propose_strategy_evolution(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        proposals = (
            create_adaptive_intelligence_service()
            .propose_evolution()
        )

        return {
            "created_count": len(
                proposals
            ),
            "proposals": [
                item.to_dictionary()
                for item in proposals
            ],
        }


"""
        text = replace_once(
            text,
            marker,
            routes + marker,
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
        "useAdaptiveIntelligence"
        not in text
    ):
        react_end = text.find(
            "\n\n"
        )
        text = (
            text[:react_end + 2]
            + 'import {\n'
            + '  useAdaptiveIntelligence,\n'
            + '  useProposeStrategyEvolution,\n'
            + '} from "@/hooks/'
            + 'useAdaptiveIntelligence";\n\n'
            + text[react_end + 2:]
        )

    if (
        "AdaptiveIntelligencePanel"
        not in text
    ):
        marker = (
            '} from "@/components/'
            'copilot/'
            'DecisionOutcomePanel";'
        )
        text = replace_once(
            text,
            marker,
            marker
            + '\nimport {\n'
            + '  AdaptiveIntelligencePanel,\n'
            + '} from "@/components/'
            + 'copilot/'
            + 'AdaptiveIntelligencePanel";',
        )

    if (
        "const adaptiveIntelligenceQuery"
        not in text
    ):
        marker = (
            "  const decisionOutcomesQuery =\n"
            "    useDecisionOutcomes();\n"
        )
        text = replace_once(
            text,
            marker,
            marker
            + "\n"
            + "  const adaptiveIntelligenceQuery =\n"
            + "    useAdaptiveIntelligence();\n\n"
            + "  const proposeStrategyEvolution =\n"
            + "    useProposeStrategyEvolution();\n",
        )

    if (
        "<AdaptiveIntelligencePanel"
        not in text
    ):
        anchor = (
            "          {conversation.map(\n"
        )
        panel = """          {adaptiveIntelligenceQuery.data && (
            <AdaptiveIntelligencePanel
              report={
                adaptiveIntelligenceQuery.data
              }
              refreshing={
                adaptiveIntelligenceQuery
                  .isFetching
              }
              proposing={
                proposeStrategyEvolution
                  .isPending
              }
              onRefresh={() => {
                void adaptiveIntelligenceQuery
                  .refetch();
              }}
              onPropose={() => {
                proposeStrategyEvolution
                  .mutate();
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
        "Adaptive Intelligence Bundle "
        "integrated."
    )


if __name__ == "__main__":
    main()
