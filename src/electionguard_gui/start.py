import eel


@eel.expose
def say_hello_py(x: str) -> None:
    print(f"Hello from {x}")


def run() -> None:
    say_hello_py("Python World!")
    eel.init("src/electionguard_gui/web")
    eel.start("main.html")
