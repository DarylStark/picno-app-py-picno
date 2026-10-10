"""Module with the ExecutorRunCommandList."""

import subprocess
from pathlib import Path
from typing import override

from picno.executor import Executor
from picno.model import Image


class RunCommandList(Executor):
    """Executor to run a command with the media list."""

    def __init__(
        self, base_path: Path, command: str, extra_args: list[str] | None = None
    ) -> None:
        """Set the options."""
        self._base_path = base_path
        self._command = command
        self._extra_args = extra_args
        self._files: list[str] = []
        print(self._extra_args)

    @override
    def start(self) -> None:
        """Start method doesn't do anything."""
        pass

    @override
    def done(self) -> None:
        """Execute the command with the file list."""
        cmd: list[str] = [self._command]
        if self._extra_args:
            cmd.extend(self._extra_args)
        cmd.extend(self._files)
        subprocess.run(cmd, check=True)

    @override
    def process_image(self, image: Image) -> None:
        """Process a given image."""
        path = self._base_path / image.physical_file
        self._files.append(str(path.resolve()))


def create_run_command_list(
    base_path: Path, options: dict[str, str] | None = None
) -> RunCommandList:
    """Create the RunCommandList."""
    command = (options or {}).get('command')
    args = (options or {}).get('args')
    args_list = args.split(' ') if args else None

    if command is None:
        raise ValueError('Command should be given!')
    return RunCommandList(
        base_path=base_path, command=command, extra_args=args_list
    )
