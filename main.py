import logging

from handvision.modules.volume_control import VolumeControlModule
from handvision.vision import StreamCaptureManager


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    StreamCaptureManager(module=VolumeControlModule()).run(source=0, flip=True)


if __name__ == "__main__":
    main()