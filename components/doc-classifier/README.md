# Document Processing

This is a framework with a number of processors for applying processing steps to documents. It primarily operates on GCS objects, and is intended to provide a framework for applying both open source parsers (such as Langchain [Document Loaders](https://python.langchain.com/v0.1/docs/modules/data_connection/document_loaders/), [unzip](https://docs.python.org/3/library/zipfile.html), [msg-extract](https://pypi.org/project/extract-msg/), and [pyexcel](https://pypi.org/project/pyexcel/)), and Google native providers such [DocAI](https://cloud.google.com/document-ai/docs/overview) parsers.

## Quick start

### Local Development

- `./invoke.sh init` will create the Python3 virtual environment. It is available in .venv.
- `./invoke.sh process` (see [tasks.py](tasks.py) for implementation) provides a local implementation of the processor.
- `./invoke.sh --list` will show the list of options.

### Deployments

The instructions for Cloud Function and for Cloud Run deployment is available in the [README.md](deployments/cloud_function/README.md).

## Python

### Dependencies

Python dependencies are resolved to a single [reqs/requirements_all.txt](reqs/requirements_all.txt) which acts as the requirements for the shared virtual environment and the constraint for individual project requirements.

### Python-based Deployments

There are Python-based deployments, such as in [deployments/cloud_function/main.py](deployments/cloud_function/main.py) which leverage one or more libraries. There is an associates requirements.in and requirements.txt for these libraries (using -r) capturing the full non-library dependencies. It is assumed that all of the relevant libraries will be staged in the deployment.

### Libraries

There are Python-based libraries, such as in [libs/processor-base](libs/processor-base) which also have a requirements.in. There can be one or more .pth files, such as [libs/packages.pth](libs/packages.pth) which define libraries that should be included in the site path. These are loaded into the common virtual environment.

See the deployments for patterns for including the libraries in Docker containers and in Cloud Functions.

### invoke.sh

Running invoke.sh will do the following -

- Installing a virtual environment if needed
- Re-compile the requirements*.txt from the requirements*.in if necessary
- Re-synchronise the virtual environment sites from requirements_all.txt if necessary
- Link in local libraries.

It uses tasks.py and the [pyinvoke](https://www.pyinvoke.org/) library and can be used to define common tasks that need to be run, including re-synchronising the environment as well as running Python scripts.

## Processor Base Framework

The [processor-base](libs/processor-base/README.md) library is a framework for building processors, designed to make it easy to implement.

In particular, it includes the following:

- GCS abstraction to provide Pythonic ways to work equally with GCS objects and local files. Many Google APIs require GCS objects, while open source libraries require local files. Development is often more convenient locally with files, while deployment is with GCS objects. This enables writing code that works equally well with both.
- BigQuery results writing. Writing using BigQuery [Storage Write API](https://cloud.google.com/bigquery/docs/write-api) enables persisting status messages for further processing.
