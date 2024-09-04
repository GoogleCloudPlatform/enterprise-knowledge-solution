# Document Processing
This is a framework with a number of processors for applying processing steps to documents. It primarily operates on GCS objects, and is intended to provide a framework for applying both open source parsers (such as Langchain [Document Loaders](https://python.langchain.com/v0.1/docs/modules/data_connection/document_loaders/), [unzip](https://docs.python.org/3/library/zipfile.html), [msg-extract](https://pypi.org/project/extract-msg/), and [pyexcel](https://pypi.org/project/pyexcel/)), and Google native providers such [DocAI](https://cloud.google.com/document-ai/docs/overview) parsers.

### Dependencies
Python dependencies are resolved to a single [reqs/requirements_all.txt](reqs/requirements_all.txt) which acts as the requirements for the shared virtual environment and the constraint for individual project requirements.

### Libraries
There are Python-based libraries, such as in [libs/processor-base](libs/processor-base) which also have a requirements.in. There can be one or more .pth files, such as [libs/packages.pth](libs/packages.pth) which define libraries that should be included in the site path. These are loaded into the common virtual environment.

See the deployments for patterns for including the libraries in Docker containers and in Cloud Functions.
It uses tasks.py and the [pyinvoke](https://www.pyinvoke.org/) library and can be used to define common tasks that need to be run, including re-synchronising the environment as well as running Python scripts.

### Processor Base Framework

The [processor-base](libs/processor-base/README.md) library is a framework for building processors, designed to make it easy to implement.

In particular, it includes the following:
 * GCS abstraction to provide Pythonic ways to work equally with GCS objects and local files. Many Google APIs require GCS objects, while open source libraries require local files. Development is often more convenient locally with files, while deployment is with GCS objects. This enables writing code that works equally well with both.
 * BigQuery results writing. Writing using BigQuery [Storage Write API](https://cloud.google.com/bigquery/docs/write-api) enables persisting status messages for further processing.

### invoke.sh

Running invoke.sh will do the following -
 * Installing a virtual environment if needed
 * Re-compile the requirements*.txt from the requirements*.in if necessary
 * Re-synchronise the virtual environment sites from requirements_all.txt if necessary
 * Link in local libraries.

### Local Development
 * `./invoke.sh --list` will show the list of options.
 * `./invoke.sh lock` will resolve all of the dependency requirements into the single locked set of versions. This is useful for testing/development.
 * `./invoke.sh sync` will sync the virtual environment dependencies with the locked set of versions. This is useful for testing/development.
 * `./invoke.sh processing.cloud-run-local-deploy` will deploy the processing (outlook etc) to Cloud Run using gcloud. This is useful for testing/development.
 * `./invoke.sh processing.process` will simply run the local code for processing (outlook etc). This is useful for testing/development.


### Deployments
There are Python-based deployments, such as in [deployments/cloud_function/main.py](deployments/cloud_function/main.py) which leverage one or more libraries. There is an associates requirements.in and requirements.txt for these libraries (using -r) capturing the full non-library dependencies. It is assumed that all of the relevant libraries will be staged in the deployment.
The instructions for Cloud Function deployment is available in the [README.md](deployments/cloud_function/README.md) and for Cloud Run is available in the [README.md](deployments/cloud_run/README.md).
 * `./invoke.sh processing.cloud-run-remote-build` will build and deploy the processing (outlook etc) to Cloud Run using Cloud Build.