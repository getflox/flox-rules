import json
from os.path import join, basename, dirname, isdir

import click as click
from loguru import logger
from plumbum import local

from flox_rules.manager import list_rules
from flox_rules.virtualenv import ensure_venv, install_dependencies
from floxcore import CONFIG_DIRS
from floxcore.console import tqdm, success, error
from floxcore.context import Flox
from floxcore.remotes import universal_copy
from floxcore.utils.table import DataObjectTable

VENV_PATH = CONFIG_DIRS.get_in("user", "rules-venv")


@click.group(invoke_without_command=True)
@click.pass_obj
@click.pass_context
def rules(ctx, flox: Flox):
    """List all available rules"""
    if ctx.invoked_subcommand:
        return

    available_rules = list_rules(flox)
    if not available_rules:
        error('No rules available. Maybe configure some with "flox config --plugin=rules"?')
        return

    DataObjectTable(list_rules(flox), hide=["parameters"]).show()


@rules.command(name="apply")
@click.pass_obj
def rules_apply(flox: Flox):
    """
    Apply standard project rules on the project
    """
    ensure_venv(VENV_PATH, flox.settings.rules.source)

    python = local[f"{join(VENV_PATH, 'bin', 'python')}"]
    filtered_rules = [r for r in list_rules(flox) if not r.excluded]
    rules_progress = tqdm(filtered_rules)

    for rule in rules_progress:
        rules_progress.set_description(rule.description)
        module = basename(rule.location).replace(".py", "")

        params = {}
        for name, default in rule.parameters.items():
            params[name] = flox.settings[default.replace("settings:", "")] \
                if str(default).startswith("settings:") else default

        params.update(dict(
            project_dir=flox.working_dir,
            meta=flox.meta.all()
        ))

        params_json = json.dumps({k: v for k, v in params.items() if k in rule.parameters.keys()})

        execution = f"import sys, json; sys.path.insert(0, '{dirname(rule.location)}'); " \
                    f"from {module} import {rule.function}; " \
                    f"args = '{params_json}';" \
                    f"{rule.function}(**json.loads(args))"
        logger.debug(f"Running python code: {execution} with params: {params_json}")

        (python["-c", execution] > click.get_binary_stream('stdout'))()


@rules.command(name="update")
@click.pass_obj
def rules_update(flox: Flox):
    """Update rules definitions from external sources"""

    if not isdir(VENV_PATH):
        ensure_venv(VENV_PATH, flox.settings.rules.source)

    updater = tqdm(flox.settings.rules.source)

    for source in updater:
        install_dependencies(VENV_PATH, source)
        universal_copy(flox, CONFIG_DIRS.get_in("user", "rules"), source)

        updater.success(f"Updated remote source: {source}")

    success("All sources updated")
