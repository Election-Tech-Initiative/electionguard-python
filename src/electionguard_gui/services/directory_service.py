import os


DOCKER_MOUNT_DIR = "/egui_mnt"


def get_export_dir() -> str:
    return _get_egui_mnt_subdir("export")


def get_data_dir() -> str:
    return _get_egui_mnt_subdir("data")


def _get_egui_mnt_subdir(subdir_name: str) -> str:
    egui_mnt_dir = _get_egui_mnt_dir()
    subdir_path = os.path.join(egui_mnt_dir, subdir_name)
    os.makedirs(subdir_path, exist_ok=True)
    return subdir_path


def _get_egui_mnt_dir() -> str:
    # basically if we're in a docker container
    if os.path.exists(DOCKER_MOUNT_DIR):
        return DOCKER_MOUNT_DIR
    return os.path.join(os.getcwd(), "egui_mnt")
