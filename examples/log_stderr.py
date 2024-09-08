#! /opt/venvs/command_watcher/bin/python

from pathlib import Path

from command_watcher import Watch

watch = Watch(service_name="log_stderr")

script = Path.resolve(Path(__file__).parent / ".." / "tests" / "files" / "stderr.sh")

watch.run(str(script))

watch.final_report(status=2)
