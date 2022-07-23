from typing import Any, Optional
import print_utils


class CliStepBase:
    """
    Responsible for providing common functionality to the individual steps within an end-to-end election command
    from the CLI.
    """

    header_color = "green"
    value_color = "yellow"
    warning_color = "bright_red"
    section_color = "bright_white"
    VERIFICATION_URL_NAME = "verification_url"

    def print_header(self, s: str) -> None:
        print_utils.print_header(s)

    def print_section(self, s: Optional[str]) -> None:
        print_utils.print_section(s)

    def print_value(self, name: str, value: Any) -> None:
        print_utils.print_value(name, value)

    def print_warning(self, s: str) -> None:
        print_utils.print_warning(s)
