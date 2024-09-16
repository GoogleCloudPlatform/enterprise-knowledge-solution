# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import glob

from invoke import task, Collection
from uv import find_uv_bin

import components.processing.tasks
import components.webui.tasks


# Find the base directory for invoke
BASE_DIR = os.path.dirname(__file__)

########
#
# Maintaining the virtual environment tasks
#


VENV_DIR = os.path.join(BASE_DIR, ".venv")
REQS_ALL = os.path.join(BASE_DIR, "reqs", "requirements_all.txt")


@task
def sync(c, upgrade=False, upgrade_package=""):
    """Synchronise environments."""
    c.run(f'"{find_uv_bin()}" pip sync -q "{REQS_ALL}"')


@task(
    help={
        "upgrade": "Upgrade all dependencies (subject to contraints)",
        "upgrade-package": "Upgrade the specific dependency",
        "quiet": "Quiet output",
    },
    post=[sync],
)
def lock(c, upgrade=False, upgrade_package="", quiet=True):
    """Lock and synchronise environments."""

    REQ_ALL_IN = os.path.join(BASE_DIR, "reqs", "requirements_all.in")

    opt_quiet = "-q" if quiet else ""

    opt_upgrade = ""
    opt_upgrade_package = ""
    if upgrade:
        opt_upgrade = "--upgrade "
    if upgrade_package:
        opt_upgrade_package = f"--upgrade-package {upgrade_package}"

    # Lock the consolidated requirements
    c.run(
        f'"{find_uv_bin()}" pip compile '
        f"{opt_quiet} {opt_upgrade} {opt_upgrade_package} "
        f'"{os.path.relpath(REQ_ALL_IN, os.getcwd())}" -o "{os.path.relpath(REQS_ALL, os.getcwd())}"'
    )

    # Generate a constraints file
    CONSTRAINTS = os.path.join(BASE_DIR, "reqs", "constraints.txt")
    c.run(f'cat "{REQS_ALL}" | grep -v "^-e " > "{CONSTRAINTS}"')

    # Gather all requirements
    reqs_in = list(glob.glob(
        os.path.join(BASE_DIR, "**", "pyproject.toml"),
        recursive=True))
    reqs_in += list(glob.glob(
        os.path.join(BASE_DIR, "**", "requirements.in"),
        recursive=True))

    # Re-generate the requirements.txt for specific deployments
    # (honouring consolidated requirements)
    REL_CONSTRAINTS = os.path.relpath(CONSTRAINTS, os.getcwd())
    for req_in in reqs_in:
        req_txt = os.path.join(os.path.dirname(req_in), "requirements.txt")
        if os.path.exists(req_txt):
            c.run(
                f'"{find_uv_bin()}" pip compile {opt_quiet} --generate-hashes '
                f'-c "{REL_CONSTRAINTS}" "{os.path.relpath(req_in, os.getcwd())}" | '
                'grep -v "\\${PROJECT_ROOT}" >'
                f'"{req_txt}"'
            )

#
# Build collection from all available tasks
#


# Root tasks
namespace = Collection(sync, lock)

# Sub-tasks
namespace.add_collection(components.processing.tasks, name="processing")
namespace.add_collection(components.webui.tasks, name="webui")
