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
        "InvestmentThesisService"
        not in text
    ):
        anchor = (
            "from app.copilot_service "
            "import CopilotService\n"
        )

        imports = (
            anchor
            + "from app."
            "investment_capability_providers "
            "import (\n"
            "    NewsCapabilityProvider,\n"
            "    PortfolioCapabilityProvider,\n"
            "    RiskCapabilityProvider,\n"
            "    UnavailableCapabilityProvider,\n"
            ")\n"
            "from app."
            "investment_thesis_service "
            "import InvestmentThesisService\n"
        )

        text = replace_once(
            text,
            anchor,
            imports,
        )

    if (
        "def create_investment_"
        "thesis_service("
        not in text
    ):
        text += """
\n\ndef create_investment_thesis_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> InvestmentThesisService:
    intelligence_service = (
        create_intelligence_service()
    )
    operations_service = (
        create_operations_query_service()
    )
    graduation_service = (
        create_intelligence_graduation_service(
            database_path=database_path
        )
    )

    return InvestmentThesisService(
        snapshot_provider=(
            intelligence_service
            .get_snapshot
        ),
        risk_provider=(
            operations_service
            .get_risk_status
        ),
        portfolio_provider=(
            operations_service
            .get_portfolio
        ),
        graduation_provider=(
            graduation_service
            .get_status
        ),
        capability_providers=(
            NewsCapabilityProvider(),
            UnavailableCapabilityProvider(
                capability="TECHNICAL",
                maximum=20.0,
                summary=(
                    "Technical capability "
                    "has not yet been connected."
                ),
            ),
            UnavailableCapabilityProvider(
                capability="MACRO",
                maximum=10.0,
                summary=(
                    "Macro capability has "
                    "not yet been connected."
                ),
            ),
            UnavailableCapabilityProvider(
                capability="VALUATION",
                maximum=10.0,
                summary=(
                    "Valuation capability has "
                    "not yet been connected."
                ),
            ),
            PortfolioCapabilityProvider(),
            RiskCapabilityProvider(),
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
        "create_investment_"
        "thesis_service"
        not in text
    ):
        text = replace_once(
            text,
            "    create_copilot_service,\n",
            (
                "    create_copilot_service,\n"
                "    create_investment_"
                "thesis_service,\n"
            ),
        )

    if (
        '"/api/copilot/'
        'investment-theses"'
        not in text
    ):
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""

        route = """    @app.get(
        "/api/copilot/investment-theses",
        tags=["copilot"],
    )
    def investment_theses(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_investment_thesis_service()
            .get_report()
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
        "useInvestmentTheses"
        not in text
    ):
        marker = (
            'import React, {'
        )
        position = text.find(marker)

        if position == -1:
            raise RuntimeError(
                "React import not found."
            )

        end = text.find(
            '\n\n',
            position,
        )

        text = (
            text[:end + 2]
            + 'import {\n'
            + '  useInvestmentTheses,\n'
            + '} from "@/hooks/'
            + 'useInvestmentTheses";\n\n'
            + text[end + 2:]
        )

    if (
        "InvestmentThesisPanel"
        not in text
    ):
        marker = (
            '} from "@/components/'
            'copilot/'
            'DecisionIntelligencePanel";'
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + '\nimport {\n'
                + '  InvestmentThesisPanel,\n'
                + '} from "@/components/'
                + 'copilot/'
                + 'InvestmentThesisPanel";'
            ),
        )

    if (
        "const investmentThesesQuery"
        not in text
    ):
        marker = (
            "  const decisionIntelligenceQuery =\n"
            "    useDecisionIntelligence();\n"
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + "\n"
                + "  const investmentThesesQuery =\n"
                + "    useInvestmentTheses();\n"
            ),
        )

    if (
        "<InvestmentThesisPanel"
        not in text
    ):
        anchor = (
            "          {conversation.map(\n"
        )

        panel = """          {investmentThesesQuery.data && (
            <InvestmentThesisPanel
              report={
                investmentThesesQuery.data
              }
              refreshing={
                investmentThesesQuery
                  .isFetching
              }
              onRefresh={() => {
                void investmentThesesQuery
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
        "Decision Intelligence v3 "
        "integrated."
    )


if __name__ == "__main__":
    main()
