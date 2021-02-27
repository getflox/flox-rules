import ast
import hashlib
import re
from os import listdir
from os.path import join, isfile, isdir
from typing import List

import click
from flox_rules.model import Rule
from loguru import logger

from floxcore import CONFIG_DIRS
from floxcore.context import Flox


def create_execution_filter(excluded, included):
    exclude_regexp = list(map(lambda x: re.compile(x.replace("*", ".*")), excluded))
    include_regexp = list(map(lambda x: re.compile(x.replace("*", ".*")), included))

    def filter_execution(rule_id):
        return not any([r.match(rule_id) for r in exclude_regexp]) or any([r.match(rule_id) for r in include_regexp])

    return filter_execution


def parse_docstring(func: ast.FunctionDef, docstring: str):
    lines = list(map(lambda x: x.strip(), docstring.splitlines(False)))
    key = next(filter(lambda x: x and x.strip().startswith(":key"), lines)).replace(":key", "").strip()
    description = "\n".join(filter(lambda x: x and not x.strip().startswith(":"), lines))

    params = {}
    defaults = func.args.kw_defaults
    for pos, arg in enumerate(func.args.kwonlyargs):
        default = defaults[pos]
        params[arg.arg] = default.value if default else None

    return key, description, params


def top_level_functions(body):
    return (f for f in body if isinstance(f, ast.FunctionDef))


def parse_file(location: str, ruleset: str, execution_filter):
    with open(location) as f:
        tree = ast.parse(f.read(), filename=location)

        for func in top_level_functions(tree.body):
            key, desc, params = parse_docstring(func, ast.get_docstring(func))
            yield Rule(key, desc, ruleset, click.format_filename(location), func.name, not execution_filter(key),
                       params)


def parse_ruleset(location: str, ruleset: str, execution_filter):
    logger.debug(f"Searching for rule files in: {location}")
    for f in filter(lambda x: isfile(join(location, x)) and x.endswith(".py"), listdir(location)):
        logger.debug(f"Discovered new rule file {f} for ruleset {ruleset}")
        yield from parse_file(join(location, f), ruleset, execution_filter)


def discover_rules(location: str, exclude: list, include: list):
    logger.debug(f"Looking for rulesets in {location}")
    execution_filter = create_execution_filter(exclude, include)
    for d in filter(lambda x: isdir(join(location, x)), listdir(location)):
        logger.debug(f"Discovered new ruleset in {d}@{location}")
        yield from parse_ruleset(join(location, d), d.replace("-ruleset", ""), execution_filter)


def list_rules(flox: Flox) -> List[Rule]:
    available_rules = []
    for location in flox.settings.rules.source:
        source_hash = hashlib.sha256(str(location).encode("UTF-8")).hexdigest()
        storage = join(CONFIG_DIRS.get_in("user", "rules"), source_hash)
        available_rules += list(discover_rules(storage, flox.settings.rules.exclude, flox.settings.rules.include))

    return available_rules
