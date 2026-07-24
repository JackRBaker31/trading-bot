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
            f"{old[:120]!r}"
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
        "IntelligenceObservabilityService"
        not in text
    ):
        anchor = (
            "from app.copilot_service "
            "import CopilotService\n"
        )

        imports = anchor + """from app.intelligence_observability_service import (
    IntelligenceObservabilityService,
)
from app.operation_diagnostics_repository import (
    OperationDiagnosticsRepository,
)
from app.operation_diagnostics_service import (
    OperationDiagnosticsService,
)
"""

        text = replace_once(
            text,
            anchor,
            imports,
        )

    if (
        "def create_operation_"
        "diagnostics_service("
        not in text
    ):
        text += """


def create_operation_diagnostics_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> OperationDiagnosticsService:
    service = OperationDiagnosticsService(
        repository=(
            OperationDiagnosticsRepository(
                database_path=database_path
            )
        )
    )
    service.initialize()
    return service


def create_intelligence_observability_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> IntelligenceObservabilityService:
    job_service = create_job_service(
        database_path=database_path
    )

    return IntelligenceObservabilityService(
        jobs_provider=(
            lambda limit: (
                job_service.list_recent(
                    limit=limit
                )
            )
        ),
        diagnostics_service=(
            create_operation_diagnostics_service(
                database_path=database_path
            )
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
        "create_intelligence_"
        "observability_service"
        not in text
    ):
        text = replace_once(
            text,
            "    create_copilot_service,\n",
            (
                "    create_copilot_service,\n"
                "    create_intelligence_"
                "observability_service,\n"
            ),
        )

    if (
        '"/api/copilot/'
        'intelligence-health"'
        not in text
    ):
        marker = """    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
"""

        routes = """    @app.get(
        "/api/copilot/intelligence-health",
        tags=["copilot"],
    )
    def intelligence_health(
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
            create_intelligence_observability_service()
            .overview(
                limit=limit
            )
            .to_dictionary()
        )


    @app.get(
        "/api/jobs/{job_id}/diagnostics",
        tags=["jobs"],
    )
    def job_diagnostics(
        job_id: str,
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_intelligence_observability_service()
            .job_report(
                job_id=job_id
            )
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
        "useIntelligenceHealth"
        not in text
    ):
        react_end = text.find(
            "\n\n"
        )

        text = (
            text[:react_end + 2]
            + 'import {\n'
            + '  useIntelligenceHealth,\n'
            + '} from "@/hooks/'
            + 'useIntelligenceObservability";\n\n'
            + text[react_end + 2:]
        )

    if (
        "IntelligenceHealthPanel"
        not in text
    ):
        marker = (
            '} from "@/components/'
            'copilot/'
            'AdvancedIntelligencePanel";'
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + '\nimport {\n'
                + '  IntelligenceHealthPanel,\n'
                + '} from "@/components/'
                + 'copilot/'
                + 'IntelligenceHealthPanel";'
            ),
        )

    if (
        "const intelligenceHealthQuery"
        not in text
    ):
        marker = (
            "  const advancedIntelligenceQuery =\n"
            "    useAdvancedIntelligence();\n"
        )

        text = replace_once(
            text,
            marker,
            (
                marker
                + "\n"
                + "  const intelligenceHealthQuery =\n"
                + "    useIntelligenceHealth();\n"
            ),
        )

    if (
        "<IntelligenceHealthPanel"
        not in text
    ):
        anchor = (
            "          {conversation.map(\n"
        )

        panel = """          {intelligenceHealthQuery.data && (
            <IntelligenceHealthPanel
              overview={
                intelligenceHealthQuery.data
              }
              refreshing={
                intelligenceHealthQuery
                  .isFetching
              }
              onRefresh={() => {
                void intelligenceHealthQuery
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
        "Diagnostics & Observability "
        "integrated."
    )


if __name__ == "__main__":
    main()
