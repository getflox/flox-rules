from os.path import isdir, join, isfile
from venv import EnvBuilder

from loguru import logger
from plumbum import local

from floxcore.console import info, success


def ensure_venv(rules_venv, sources):
    if isdir(rules_venv):
        return

    info(f"Creating rule execution virtual env {rules_venv}")
    builder = EnvBuilder(with_pip=True)
    builder.create(rules_venv)

    for source in sources:
        install_dependencies(rules_venv, source)


def install_dependencies(venv_path, source):
    req = join(source, "requirements.txt")
    if not isfile(req):
        logger.debug(f"Skipping {source} as unable to locate requirements.txt file")
        return

    pip = local[join(venv_path, "bin", "pip")]
    pip["install", "-r", req]()

    success(f"Installed dependencies from {req}")
