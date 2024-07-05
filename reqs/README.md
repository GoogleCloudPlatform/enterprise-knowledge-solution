
# Python components

Note the .in files are the maintained, while the .txt files are locked with hashes to
the specific versions. Invoke.sh will automatically create new lock files (and sync) as
required.

## requirements_all.txt

This is the global lock file for the virtual environment that is based on all of the `*.in` requirement files.

This also acts as a constraint file for all of the specific .txt output file, i.e., all requirements are
synchronized to the global requirements_all.txt.

## requirements_bootstrap.in and requirements_bootstrap.txt

These are the requirements for invoke.sh and is bootstrapped using pip in a first virtual environment.

## requirements_dev.in and requirements_dev.txt

These are the development requirements required for the Python environment including all tools for
testing, linting, syntax checking, etc.

