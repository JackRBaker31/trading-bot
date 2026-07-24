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
        "DecisionOutcomeService"
        not in text
    ):
        anchor = (
            "from app.copilot_service "
            "import CopilotService\n"
        )

        imports = (
            anchor
            + "from app."
            "decision_outcome_repository "
            "import "
            "DecisionOutcomeRepository\n"
            "from app."
            "decision_outcome_service "
            "import DecisionOutcomeService\n"
        )

        text = replace_once(
            text,
            anchor,
            imports,
        )

    if (
        "def create_decision_"
        "outcome_service("
        not in text
    ):
        text += """
\n\ndef create_decision_outcome_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> DecisionOutcomeService:
    memory_service = (
        create_decision_memory_service(
            database_path=database_path
        )
    )

    service = DecisionOutcomeService(
        repository=(
            DecisionOutcomeRepository(
                database_path=database_path
            )
        ),
        decisions_provider=(
            lambda limit: (
                memory_service.recent(
                    limit=limit
                )
            )
        ),
        bars_provider=(
            lambda symbol, output_size: (
                create_technical_historical_client()
                .get_daily_bars(
                    symbol=symbol,
                    output_size=output_size,
                )
            )
        ),
    )
    service.initialize()
    return service
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
        "create_decision_outcome_service"
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
                "outcome_service,\n"
            ),
        )

    if (
        '"/api/copilot/'
        'decision-outcomes"'
        not in text
    ):
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""

        routes = """    @app.get(
        "/api/copilot/decision-outcomes",
        tags=["copilot"],
    )
    def decision_outcomes(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
        limit: int = Query(
            default=20,
            ge=1,
            le=100,
        ),
    ) -> dict[str, object]:
        del user

        return (
            create_decision_outcome_service()
            .overview(
                limit=limit
            )
            .to_dictionary()
        )


    @app.post(
        "/api/copilot/decision-outcomes/capture",
        tags=["copilot"],
    )
    def capture_decision_outcomes(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_decision_outcome_service()
            .capture_due()
            .to_dictionary()
        )


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
        "useDecisionOutcomes"
        not in text
    ):
        react_end = text.find(
            "\n\n"
        )

        text = (
            text[:react_end + 2]
            + 'import {\n'
            + '  useCaptureDecisionOutcomes,\n'
            + '  useDecisionOutcomes,\n'
            + '} from "@/hooks/'
            + 'useDecisionOutcomes";\n\n'
            + text[react_end + 2:]
        )

    if (
        "DecisionOutcomePanel"
        not in text
    ):
        marker = (
            '} from "@/components/'
            'copilot/'
            'DecisionMemoryPanel";'
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + '\nimport {\n'
                + '  DecisionOutcomePanel,\n'
                + '} from "@/components/'
                + 'copilot/'
                + 'DecisionOutcomePanel";'
            ),
        )

    if (
        "const decisionOutcomesQuery"
        not in text
    ):
        marker = (
            "  const decisionMemoryQuery =\n"
            "    useDecisionMemory();\n"
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + "\n"
                + "  const decisionOutcomesQuery =\n"
                + "    useDecisionOutcomes();\n\n"
                + "  const captureDecisionOutcomes =\n"
                + "    useCaptureDecisionOutcomes();\n"
            ),
        )

    if (
        "<DecisionOutcomePanel"
        not in text
    ):
        anchor = (
            "          {conversation.map(\n"
        )

        panel = """          {decisionOutcomesQuery.data && (
            <DecisionOutcomePanel
              overview={
                decisionOutcomesQuery.data
              }
              refreshing={
                decisionOutcomesQuery
                  .isFetching
              }
              capturing={
                captureDecisionOutcomes
                  .isPending
              }
              onRefresh={() => {
                void decisionOutcomesQuery
                  .refetch();
              }}
              onCapture={() => {
                captureDecisionOutcomes
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
                "the trading-bot "
                "project root."
            )

    patch_dependencies()
    patch_app()
    patch_page()

    print(
        "Outcome Tracking Phase 2 "
        "integrated."
    )


if __name__ == "__main__":
    main()
