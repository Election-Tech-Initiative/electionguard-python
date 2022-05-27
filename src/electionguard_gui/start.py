import eel


@eel.expose
def setup_election(guardianCount: int, quorum: int, manifest: str) -> None:
    print(
        f"Setting up election with guardianCount: {guardianCount}, quorum: {quorum}, manifest: {manifest}"
    )


def run() -> None:
    eel.init("src/electionguard_gui/web")
    eel.start("main.html")
