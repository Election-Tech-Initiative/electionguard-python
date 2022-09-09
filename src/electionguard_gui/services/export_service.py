import os
from electionguard_gui.services.directory_service import get_data_dir, get_export_dir


def get_export_locations() -> list[str]:
    export_dir = get_export_dir()
    if os.name == "nt":
        drives = get_removable_drives()
        return [export_dir, _get_download_path(), get_data_dir()] + drives
    return [export_dir]


def get_removable_drives() -> list[str]:
    dl = "DEFGHIJKLMNOPQRSTUVWXYZ"
    drives = [f"{d}:\\" for d in dl if os.path.exists(f"{d}:")]
    return drives


def _get_download_path() -> str:
    """
    Returns the default downloads path for linux or windows.
    Code from https://pyquestions.com/python-finding-the-user-s-downloads-folder
    """
    if os.name == "nt":
        # pylint: disable=import-outside-toplevel
        # pylint: disable=import-error
        import winreg

        sub_key = (
            r"SOFTWARE\\Microsoft\Windows\\CurrentVersion\\Explorer\\Shell Folders"
        )
        downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return str(location)
    return os.path.join(os.path.expanduser("~"), "downloads")
