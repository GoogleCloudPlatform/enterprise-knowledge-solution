"""
Copyright 2022 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

AUTO_APPROVAL_MAPPING = {
    "driver_license": {
        "Accept1": {
            "Validation_Score": 0.4,
            "Matching_Score": 0.8,
            "Extraction_Score": 0.3
        },
        "Accept2": {
            "Validation_Score": 0.6,
            "Matching_Score": 0.5,
            "Extraction_Score": 0.4
        },
        "Reject": {
            "Validation_Score": 0.2,
            "Matching_Score": 0.2,
            "Extraction_Score": 0.2
        }
    },
    "utility_bill": {
        "Accept1": {
            "Validation_Score": 0.2,
            "Matching_Score": 0.4,
            "Extraction_Score": 0.6
        },
        "Accept2": {
            "Validation_Score": 0.5,
            "Matching_Score": 0.5,
            "Extraction_Score": 0.4
        },
        "Reject": {
            "Validation_Score": 0.1,
            "Matching_Score": 0.2,
            "Extraction_Score": 0.3
        }
    },
    "pay_stub": {
        "Accept1": {
            "Validation_Score": 0.3,
            "Matching_Score": 0.5,
            "Extraction_Score": 0.5
        },
        "Accept2": {
            "Validation_Score": 0.5,
            "Matching_Score": 0.4,
            "Extraction_Score": 0.7
        },
        "Reject": {
            "Validation_Score": 0.1,
            "Matching_Score": 0.1,
            "Extraction_Score": 0.1
        }
    },
    "unemployment_form": {
        "Accept1": {
            "Extraction_Score": 0.8
        },
        "Reject": {
            "Extraction_Score": 0.5
        }
    },
    "claims_form": {
        "Accept1": {
            "Validation_Score": 0.4,
            "Matching_Score": 0.8,
            "Extraction_Score": 0.8
        },
        "Accept2": {
            "Validation_Score": 0.6,
            "Matching_Score": 0.5,
            "Extraction_Score": 0.8
        },
        "Reject": {
            "Validation_Score": 0.2,
            "Matching_Score": 0.2,
            "Extraction_Score": 0.2
        }
    }
}
