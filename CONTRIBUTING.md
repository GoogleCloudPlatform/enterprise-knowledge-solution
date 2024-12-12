# Contributing

This document provides guidelines for contributing to the Enterprise Knowledge Solution.

## Before you begin

### Sign our Contributor License Agreement

Contributions to this project must be accompanied by a
[Contributor License Agreement](https://cla.developers.google.com/about) (CLA).
You (or your employer) retain the copyright to your contribution; this simply
gives us permission to use and redistribute your contributions as part of the
project.

If you or your current employer have already signed the Google CLA (even if it
was for a different project), you probably don't need to do it again.

Visit <https://cla.developers.google.com/> to see your current agreements or to
sign a new one.

### Review our Community Guidelines

This project follows [Google's Open Source Community
Guidelines](https://opensource.google/conduct/).

## Contribution Process

### Code Reviews

All submissions, including submissions by project members, require review. We
use [GitHub pull requests](https://docs.github.com/articles/about-pull-requests)
for this purpose.

### Branching and versioning

The `main` branch corresponds to the latest release.
Tagged releases are also maintained for major milestones.

When developing a new feature for an upcoming version, create a feature branch from `main`, and create a PR to merge the feature branch to the latest version branch when complete.

### Python source code dependency management

To manage dependencies across multiple projects, we have adopted the following conventions:

#### Folder structure

Each python component sits under its own folder under the `components/` folder and represents an independent feature of EKS, such as workflow orchestration, doc-processing, form-classifier, etc.

#### pyproject.toml vs requirements.in

Each component declares its own components in one of the following ways:

- `pyproject.toml` : For layered dependencies in a library that can be referenced by other components, place pyproject.toml in the root directory of the library. For example, see [components/processing/libs/processor-base/pyproject.toml](components/processing/libs/processor-base/pyproject.toml)
- `requirements.in` : For declaring dependencies used only by an individual component, use requirements.in. For example, see[components/dpu-workflow/requirements.in](components/dpu-workflow/requirements.in)

#### Generate requirements.txt

The files `requirement.txt` and `constraints.txt` are generated through a script, you should not edit them directly. To generate the `requirements.txt`, run the following commands:

1. Ensure you have an empty `requirements.txt` file in the same folder as `pyproject.toml` or `requirements.in`

   ```bash
   touch components/doc-classifier/src/requirements.txt
   ```

2. Generate the locked `requirement.txt` with the following script:

   ```bash
   ./invoke.sh lock
   ```

#### Dependency upgrades

To upgrade to the latest available version of dependencies, run the script with the following arguments:

```bash
./invoke.sh lock --upgrade
```

Or, to upgrade a single package:

```bash
./invoke.sh lock --upgrade-package package_name
```

This will upgrade all packages to the latest available version, except where a package has a pinned version specified in `pyproject.toml` or `requirements.in`. If you need to upgrade the version of such a package, manually change the pinned version then run the upgrade command again.

#### Combining dependencies

The file [reqs/requirements_all.in](reqs/requirements_all.in) is where the combined dependencies of each component are compiled.

- Dependencies declared in pyproject.toml are imported as editable:

  ```bash
  -e components/processing/libs/processor-base
  ```

- Dependencies declared in requirements.in are read as requirements:

  ```bash
  -r ../components/dpu-workflow/requirements.in
  ```

#### Local Development

To install all dependencies in the local venv, run the following script:

```bash
./invoke.sh sync
```

### Continuous Integration (CI) tests

This repository defines a number of CI tests in `./github/workflows`.
All tests must pass before a feature branch can be merged to a release branch.

### Cloud Build integration tests

Before a PR can be merged to a major version branch, it must pass integration test that confirms the repository can be deployed and pass functional tests in a clean GCP project.

1. A Cloud Build trigger is configured on an internal (non-public) GCP project to run on Pull Requests to each major version branch of this repository. The trigger runs the build defined at [/build/int.cloudbuild.yaml](/build/int.cloudbuild.yaml), which does the following high-level tasks:
   1. Create a new GCP project in an internal test environment
   1. Run the pre_tf_setup.sh script to prepare the GCP project and deployer service account
   1. Apply terraform to create all the terraform resources
   1. Run functional tests to confirm the resources and services are working as intended
   1. Tear down the ephemeral project

### Linting and Formatting

Many of the files in the repository are checked against linting tools and static code analysis for secure coding practices. This workflow is triggered by [.github/workflows/lint.yaml](.github/workflows/lint.yaml), running multiple lint libraries in [Super-Linter](https://github.com/super-linter/super-linter) with the settings configured in [.github/linters/super-linter.env](.github/linters/super-linter.env)

1. To validate that your code passes these checks, use the following methods depending on your environment:

   1. **GitHub Actions**: GitHub Actions will automatically run all configured checks when a PR is created or modified.

   1. **Local**: You can manually trigger the tests in a docker container from your local environment with the following command:

      ```bash
      scripts/lint.sh
      ```

1. For issues that can be fixed automatically, you can automatically fix issues in your local environment with either of the following methods:

   1. **Fix mode**: Run super-linter locally in fix mode by setting an environment variable to additionally run automatic fixes for the libraries configure

      ```bash
      export LINTER_CONTAINER_FIX_MODE=true
      scripts/lint.sh
      ```

   1. **Devcontainer**: Use a [devcontainer](https://containers.dev/) with your preferred IDE to automatically configure all the extensions defined in this repository. Once installed, when you upon the top-level folder of this repository, you will be prompted to launch the devcontainer with all linting extensions preconfigured. See [setup instructions for Visual Studio Code](https://code.visualstudio.com/docs/devcontainers/containers).
