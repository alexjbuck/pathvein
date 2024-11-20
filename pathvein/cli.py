from pathlib import Path
from typing import Annotated
from .lib import scan, shuffle
import logging
import typer

context_settings = {
    "help_option_names": ["-h", "--help"],
}

logger = logging.getLogger()

cli = typer.Typer(context_settings=context_settings)


def set_logger_level(verbosity: int, default: int = logging.ERROR) -> None:
    """
    Set the logger level based on the level of verbosity

    level = default - 10*verbosity

    verbosity = # of -v flags passed

    default         = 40 = logging.ERROR
    level with -v   = 30 = logging.WARNING
    level with -vv  = 20 = logging.INFO
    level with -vvv = 10 = logging.DEBUG
    """
    logger.setLevel(default - 10 * verbosity)


@cli.command("scan")
def cli_scan(
    path: Path,
    pattern_spec_paths: Annotated[list[Path], typer.Option("--pattern", "-p")],
    verbosity: Annotated[int, typer.Option("--verbose", "-v", count=True)] = 0,
) -> None:
    set_logger_level(verbosity)
    matches = scan(path, pattern_spec_paths)
    for match in matches:
        print(match[0].as_posix())


@cli.command("shuffle")
def cli_shuffle(
    source: Path,
    destination: Path,
    pattern_spec_paths: Annotated[list[Path], typer.Option("--pattern", "-p")],
    overwrite: bool = False,
    dryrun: bool = False,
    verbosity: Annotated[int, typer.Option("--verbose", "-v", count=True)] = 0,
) -> None:
    set_logger_level(verbosity)
    results = shuffle(source, destination, pattern_spec_paths, overwrite, dryrun)
    for result in results:
        print(f"{result.source.as_posix()} -> {result.destination.as_posix()}")
    print(f"Copied {len(results)} directories")


def main():
    logging.basicConfig(
        level=logging.NOTSET,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%m-%d %H:%M",
        handlers=[logging.FileHandler("/tmp/organizer.log"), logging.StreamHandler()],
    )
    cli()


if __name__ == "__main__":
    main()
