from pathlib import Path


ROOT = Path.cwd()

DEPENDENCIES = (
    ROOT / "web" / "dependencies.py"
)

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
        "DecisionEngineService"
        not in text
    ):
        text = replace_once(
            text,
            (
                "from app.copilot_service "
                "import CopilotService\n"
            ),
            (
                "from app.copilot_service "
                "import CopilotService\n"
                "from app."
                "decision_engine_service "
                "import "
                "DecisionEngineService\n"
            ),
        )

    if (
        "def create_decision_"
        "engine_service("
        not in text
    ):
        text += """
\n\ndef create_decision_engine_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> DecisionEngineService:
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

    return DecisionEngineService(
        snapshot_provider=(
            intelligence_service
            .get_snapshot
        ),
        risk_provider=(
            lambda: (
                operations_service
                .get_risk_status()
            )
        ),
        portfolio_provider=(
            lambda: (
                operations_service
                .get_portfolio()
            )
        ),
        graduation_provider=(
            graduation_service
            .get_status
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
        "create_decision_engine_service"
        not in text
    ):
        text = replace_once(
            text,
            (
                "    create_copilot_service,\n"
            ),
            (
                "    create_copilot_service,\n"
                "    create_decision_"
                "engine_service,\n"
            ),
        )

    if (
        '"/api/copilot/'
        'investment-decisions"'
        not in text
    ):
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""

        route = """    @app.get(
        "/api/copilot/investment-decisions",
        tags=["copilot"],
    )
    def investment_decisions(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_decision_engine_service()
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
        "useDecisionIntelligence"
        not in text
    ):
        import_anchor = (
            'import {\n'
            '  useCopilotChangeSummary,'
        )

        if import_anchor in text:
            text = replace_once(
                text,
                import_anchor,
                (
                    'import {\n'
                    '  useDecisionIntelligence,\n'
                    '} from "@/hooks/'
                    'useDecisionIntelligence";\n\n'
                    + import_anchor
                ),
            )
        else:
            first_import = (
                'import React'
            )
            index = text.find(
                first_import
            )
            if index == -1:
                raise RuntimeError(
                    "Could not locate "
                    "CopilotPage imports."
                )
            end = text.find(
                "\n",
                index,
            )
            text = (
                text[:end + 1]
                + 'import {\n'
                + '  useDecisionIntelligence,\n'
                + '} from "@/hooks/'
                + 'useDecisionIntelligence";\n'
                + text[end + 1:]
            )

    if (
        "DecisionIntelligencePanel"
        not in text
    ):
        marker = (
            '} from "@/components/'
            'copilot/'
            'DecisionTimelinePanel";'
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + "\nimport {\n"
                + "  DecisionIntelligencePanel,\n"
                + '} from "@/components/'
                + 'copilot/'
                + 'DecisionIntelligencePanel";'
            ),
        )

    if (
        "const decisionIntelligenceQuery"
        not in text
    ):
        marker = (
            "  const overviewQuery =\n"
            "    useCopilotOverview();\n"
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + "\n"
                + "  const decisionIntelligenceQuery =\n"
                + "    useDecisionIntelligence();\n"
            ),
        )

    if (
        "<DecisionIntelligencePanel"
        not in text
    ):
        anchor = (
            "          {conversation.map(\n"
        )

        panel = """          {decisionIntelligenceQuery.data && (
            <DecisionIntelligencePanel
              report={
                decisionIntelligenceQuery.data
              }
              refreshing={
                decisionIntelligenceQuery
                  .isFetching
              }
              onRefresh={() => {
                void decisionIntelligenceQuery
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
        "Decision Intelligence v2 "
        "integrated."
    )


if __name__ == "__main__":
    main()
