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
        "DecisionMemoryService"
        not in text
    ):
        anchor = (
            "from app.copilot_service "
            "import CopilotService\n"
        )

        imports = (
            anchor
            + "from app."
            "decision_memory_repository "
            "import "
            "DecisionMemoryRepository\n"
            "from app."
            "decision_memory_service "
            "import DecisionMemoryService\n"
        )

        text = replace_once(
            text,
            anchor,
            imports,
        )

    if (
        "def create_decision_"
        "memory_service("
        not in text
    ):
        text += """
\n\ndef create_decision_memory_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> DecisionMemoryService:
    service = DecisionMemoryService(
        repository=(
            DecisionMemoryRepository(
                database_path=database_path
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
        "create_decision_memory_service"
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
                "memory_service,\n"
            ),
        )

    old_route_body = """        return (
            create_investment_thesis_service()
            .get_report()
            .to_dictionary()
        )
"""

    new_route_body = """        report = (
            create_investment_thesis_service()
            .get_report()
        )

        create_decision_memory_service(
        ).capture_report(
            report=report
        )

        return report.to_dictionary()
"""

    if old_route_body in text:
        text = replace_once(
            text,
            old_route_body,
            new_route_body,
        )

    if (
        '"/api/copilot/'
        'decision-memory"'
        not in text
    ):
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""

        route = """    @app.get(
        "/api/copilot/decision-memory",
        tags=["copilot"],
    )
    def decision_memory(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
        limit: int = Query(
            default=10,
            ge=1,
            le=100,
        ),
    ) -> dict[str, object]:
        del user

        return (
            create_decision_memory_service()
            .overview(
                limit=limit
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
        "useDecisionMemory"
        not in text
    ):
        react_end = text.find(
            "\n\n"
        )

        text = (
            text[:react_end + 2]
            + 'import {\n'
            + '  useDecisionMemory,\n'
            + '} from "@/hooks/'
            + 'useDecisionMemory";\n\n'
            + text[react_end + 2:]
        )

    if (
        "DecisionMemoryPanel"
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
                + '  DecisionMemoryPanel,\n'
                + '} from "@/components/'
                + 'copilot/'
                + 'DecisionMemoryPanel";'
            ),
        )

    if (
        "const decisionMemoryQuery"
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
                + "  const decisionMemoryQuery =\n"
                + "    useDecisionMemory();\n"
            ),
        )

    if (
        "<DecisionMemoryPanel"
        not in text
    ):
        anchor = (
            "          {conversation.map(\n"
        )

        panel = """          {decisionMemoryQuery.data && (
            <DecisionMemoryPanel
              overview={
                decisionMemoryQuery.data
              }
              refreshing={
                decisionMemoryQuery
                  .isFetching
              }
              onRefresh={() => {
                void decisionMemoryQuery
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
        "Decision Memory Phase 1 "
        "integrated."
    )


if __name__ == "__main__":
    main()
