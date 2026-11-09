#! /opt/venvs/command_watcher/bin/python

from pathlib import Path

from command_watcher import Watch

base_path = Path.resolve(Path(__file__).parent / "..") / "tests" / "files"

conf = base_path / "conf_empty.yml"

watch = Watch(service_name="stdout", config_file=conf)
watch.run(base_path / "stdout.sh")
watch.final_report()

print("------------------------------")

watch = Watch(service_name="stdout-stderr", config_file=conf)
watch.run(base_path / "stdout-stderr.sh")
watch.final_report()

print("------------------------------")

watch = Watch(service_name="stderr", config_file=conf)
watch.run(base_path / "stderr.sh")
watch.final_report(status=2)
