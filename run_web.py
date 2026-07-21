import uvicorn
from app.environment import load_environment


def main() -> None:
    load_environment()

    uvicorn.run(
        "web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()