from dataclasses import dataclass


@dataclass
class JobConfig:
    gcs_input_prefix: str
    gcs_output_uri: str
    run_id: str


@dataclass
class ProcessorConfig:
    project: str
    location: str
    processor_id: str
    timeout: int


@dataclass
class AlloyDBConfig:
    primary_instance: str
    database: str
    user: str


@dataclass
class BigQueryConfig:
    general_output_table_id: str
