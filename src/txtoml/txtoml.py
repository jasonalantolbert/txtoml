"""
txtoml is a command-line utility that allows you to quickly and easily copy dependencies from a Poetry pyproject.toml
file to a pip requirements.txt file.
"""

import os
import re
from datetime import datetime

import click
import toml


def constrain(dependencies: dict) -> dict:
    """
    Converts Poetry version constraint notation to equivalent pip requirements notation.

    :param dependencies: A dictionary of package names and their Poetry-notation version contraints.
    :return: A dictionary of package names and their pip-notation version constraints.
    """

    def caret(version: str) -> str:
        """
        Handles cases of Poetry caret notation.
        :param version: The Poetry-notation version constraint.
        :return: A pip-notation version constraint.
        """
        version = version.lstrip("^")

        lower_bound = version + (".0" * (2 - version.count(".")))

        numbers = [int(i) for i in re.findall("\d+", lower_bound)]

        for index, number in enumerate(numbers):
            if number > 0:
                numbers[index] += 1
                numbers = [0 if i > index else n for i, n in enumerate(numbers)]
                break
        else:
            numbers[-1] += 1

        upper_bound = ".".join([str(i) for i in numbers])

        return f">={lower_bound}, <{upper_bound}"

    constrained_packages = {}

    for package, version in dependencies.items():
        if package != "python":
            if version.startswith("^"):
                constraint = caret(version)
            elif version.startswith("~"):
                constraint = version.replace("~", "~=")
            else:
                constraint = f"=={version}"

            constrained_packages[package] = constraint

    return constrained_packages


@click.command(help="Quickly and easily copy dependencies from a Poetry pyproject.toml file to a pip "
                    "requirements.txt file.")
@click.argument("source")
@click.argument("output")
@click.option("--include-dev", "-dev", is_flag=True, help="Include development dependencies.")
def txtoml(source: str, output: str, include_dev: bool = False):
    """
    Takes the paths to a pyproject.toml and requirements.txt file and copies dependencies from the former to the latter.

    :param source: The path to a pyproject.toml file.
    :param output: The path to a requirements.txt file.
    :param include_dev: If True, dependencies listed under the "dev-dependencies" section of the pyproject.toml will
                        be included.
    """
    pyproject = toml.load(open(os.path.abspath(source)))

    dependencies = {"regular": constrain(pyproject["tool"]["poetry"]["dependencies"])}

    with open(os.path.abspath(output), "w") as requirements:
        requirements.write(f"# Generated by txtoml on "
                           f"{datetime.strftime(datetime.utcnow(), '%a %b %d at %T UTC')}\n")

        requirements.write("\n# Dependencies\n")

        for package, version in dependencies["regular"].items():
            requirements.write(f"{package}{version}\n")

        if include_dev:
            dependencies.update({"dev": constrain(pyproject["tool"]["poetry"]["dev-dependencies"])})

            requirements.write("\n# Development dependencies\n")

            for package, version in dependencies["dev"].items():
                requirements.write(f"{package}{version}\n")


if __name__ == '__main__':
    txtoml()
