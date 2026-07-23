from app.copilot_models import (
    CopilotResponse,
    CopilotSuggestion,
)


def test_models_store_values() -> None:
    suggestion = CopilotSuggestion(
        title="Scheduler",
        message="Scheduler is healthy.",
        kind="success",
    )

    response = CopilotResponse(
        summary="Everything healthy.",
        suggestions=(suggestion,),
    )

    assert response.summary == "Everything healthy."
    assert len(response.suggestions) == 1
    assert response.suggestions[0].kind == "success"