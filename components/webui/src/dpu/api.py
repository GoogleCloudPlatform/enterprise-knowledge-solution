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

from __future__ import annotations
import base64
import re

from google.protobuf.json_format import MessageToDict  # type: ignore
from typing import Dict, Optional, Tuple, Any
from google.api_core.gapic_v1.client_info import ClientInfo # type: ignore
from google.api_core.client_options import ClientOptions  # type: ignore
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud.discoveryengine_v1.types import Document # type: ignore
from google.protobuf.struct_pb2 import Struct  # type: ignore # pylint: disable=no-name-in-module

from google.cloud import storage  # type: ignore[attr-defined, import-untyped]
from typing import Tuple
import os
import streamlit as st # type: ignore
import json

logger = st.logger.get_logger(__name__)   # pyright: ignore[reportAttributeAccessIssue]

#####
# 
# Environment configuration (where to find services)
#


PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ["AGENT_BUILDER_LOCATION"]
SEARCH_DATASTORE_ID = os.environ["AGENT_BUILDER_DATA_STORE_ID"]
SEARCH_APP_ID = os.environ["AGENT_BUILDER_SEARCH_ID"]


#####
# 
# Search interfaces
#


st.cache_resource
def search_service_client() -> discoveryengine.SearchServiceClient:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    return discoveryengine.SearchServiceClient(
        client_options=ClientOptions(
            api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com"
                if LOCATION != "global"
                else None
        ),
        client_info=ClientInfo(
          user_agent="cloud-solutions/dpu-webui-v1",
        )
        )


def generate_answer(
    search_query: str,
    preamble: str,
) -> dict:

    logger.info('*** Executing Search ****')

    client=search_service_client()

    # The full resource name of the search app serving config
    serving_config = (f"projects/{PROJECT_ID}"
                      f"/locations/{LOCATION}"
                      "/collections/default_collection"
                      f"/engines/{SEARCH_APP_ID}"
                      "/servingConfigs/default_config")

    # Optional: Configuration options for search
    # Refer to the `ContentSearchSpec` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest.ContentSearchSpec
    content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(

        # For information about snippets, refer to:
        # https://cloud.google.com/generative-ai-app-buxilder/docs/snippets
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
            return_snippet=True
        ),

        # For information about search summaries, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/get-search-summaries
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=5,
            include_citations=True,
            ignore_adversarial_query=True,

            # ignore_non_summary_seeking_query=True,
            model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                preamble=preamble,
            ),

            model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                version="stable",
            ),
        ),

        extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
            max_extractive_answer_count=5,
            max_extractive_segment_count=5,
            return_extractive_segment_score=True,
        ),
    )

    # Refer to the `SearchRequest` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=3,
        content_search_spec=content_search_spec,
        query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
        ),
        spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
            mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
        ),
    )

    response = client.search(request)
  
    result = {}
    result["answer"] = response.summary.summary_text
    result["sources"] = []
    for r in response.results:
        res = _document_to_dict(r.document)
        if res:
            result["sources"].append(res)

    return result


#####
# 
# Document interfaces
#
# Convert documents (whether search or fetched or listed) into a generic object
#


st.cache_resource
def _document_to_dict(doc: Document) -> Optional[dict]:

    def to_proto(value):
        return Struct(
           fields={k: v for k, v in value.items()},
        )

    def struct_data_to_dict(struct_data) -> Dict:
        if type(struct_data).__name__ == "MapComposite":
            return MessageToDict(to_proto(struct_data.pb))
        return MessageToDict(struct_data)

    odoc: Dict[str, Any] = {
        'id': doc.id,
        'name': doc.name,
    }

    # Load metadata (from json_data or struct_data)
    if doc.json_data:
        metadata = json.loads(doc.json_data)
        odoc['metadata'] = json.loads(doc.json_data)
    else:
        metadata = struct_data_to_dict(doc.struct_data)
    odoc['metadata'] = metadata.get('metadata', {})
    odoc['status'] = metadata.get('status', '')
    odoc['objs'] = metadata.get('objs', [])

    # Load derived data if available
    if doc.derived_struct_data:
        doc_info = struct_data_to_dict(doc.derived_struct_data)
        odoc['content'] = [
            snippet.get("snippet")
            for snippet in doc_info.get("snippets", [])
            if snippet.get("snippet") is not None
        ]
        odoc['title'] = doc_info.get('title')
        odoc['uri'] = doc_info.get('link')

    # Otherwise just load normal content 
    elif doc.content:
        odoc['uri'] = doc.content.uri

    return odoc


#####
#
# Document list & fetchers
#


st.cache_resource
def document_service_client() -> discoveryengine.DocumentServiceClient:
    return discoveryengine.DocumentServiceClient(
        client_options=ClientOptions(
            api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com"
                if LOCATION != "global"
                else None
        ),
        client_info=ClientInfo(
          user_agent="cloud-solutions/dpu-webui",
        ))


@st.cache_resource(ttl=3600)
def fetch_all_agent_docs(
) -> list[dict]:
    """List Enterprise Search Corpus"""

    # Create request
    client = document_service_client()
    request = discoveryengine.ListDocumentsRequest(
        parent=client.branch_path(PROJECT_ID, LOCATION,
                                  SEARCH_DATASTORE_ID, 'default_branch')
    )

    # Accumulate the corpus of documents
    corpus = []
    for doc in client.list_documents(request=request):
        corpus.append(_document_to_dict(doc))

    return corpus

@st.cache_resource(ttl=3600)
def fetch_agent_doc(doc_id: str) -> Optional[dict]:
    logger.info(f'Fetching doc id {doc_id}')
    client = document_service_client()

    # Fetch document
    response = document_service_client().get_document(
        request=discoveryengine.GetDocumentRequest(
            name=client.document_path(
                project=PROJECT_ID,
                location=LOCATION,
                data_store=SEARCH_DATASTORE_ID,
                branch="default_branch",
                document=doc_id,
            )
        )
    )

    doc = _document_to_dict(response)

    return doc


#####
#
# Google Cloud Storage accessors
#


@st.cache_resource(show_spinner=False)
def get_storage_client():
    return storage.Client(
        client_info=ClientInfo(
            user_agent="cloud-solutions/dpu-webui",
        )
    )


# @st.cache_resource(ttl=3600, show_spinner="Downloading object...")
# def fetch_gcs_object(bucket: str, path: str) -> Tuple[bytes, str]:
#     logger.info(f'Downloading object gs://{bucket}/{path}')
#     obj = get_storage_client().bucket(bucket).get_blob(path)
#     return (obj.download_as_bytes(), obj.content_type)

@st.cache_resource(ttl=3600, show_spinner="Downloading object...")
def get_obj_md_from_gcs(uri: str) -> bytes:
    """Given gs:// uri, download file"""
    client = storage.Client()
    matches = re.search(r'gs://(.*?)/(.*)', uri)
    bucket_name, object_name = matches.group(1), matches.group(2)
    blob = client.bucket(bucket_name).get_blob(object_name)
    # logging.info(f"blob: {blob}")
    return blob

mime_types = {
    "MIME_TYPE_PDF": "application/pdf",
    "MIME_TYPE_JSON": "application/json", 
    "MIME_TYPE_HTM": "text/html", 
    "MIME_TYPE_TXT": "text/plain", 
    "MIME_TYPE_PPT": "pplication/vnd.openxmlformats-officedocument.presentationml.presentation",
    "MIME_TYPE_DOC": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

def get_mime_type(file_name: str):
  mime_type = None
  if file_name:
    if file_name.endswith(".pdf"):
      mime_type = mime_types["MIME_TYPE_PDF"]
    if file_name.endswith(".html"):
      mime_type = mime_types["MIME_TYPE_HTM"]
    if file_name.endswith(".txt"):
      mime_type = mime_types["MIME_TYPE_TXT"]
    if file_name.endswith(".json") or file_name.endswith(".jsonl"):
      mime_type = mime_types["MIME_TYPE_JSON"]
    if file_name.endswith(".pptx") or file_name.endswith(".ppt"):
      mime_type = mime_types["MIME_TYPE_PPT"]
    if file_name.endswith(".docx") or file_name.endswith(".doc"):
      mime_type = mime_types["MIME_TYPE_DOC"]
  
  return mime_type

def show_document(uri: str) -> str:
    link = "https://storage.cloud.google.com/"+uri.lstrip("gs://")
    mime_type = get_mime_type(uri)
    doc_iframe = f'<iframe src="{link}" width="100%" height="800" type="{mime_type}" style="align: center"></iframe>'
    return doc_iframe

def display_file_from_gcs(uri: str):  
    blob = get_obj_md_from_gcs(uri)
    file_size = blob.size  # Get the total file size  
    # logger.info(f"uri: {uri}, file_size: {file_size/(1024)} KB")
    max_size = 1.5 * 1024 * 1024 # 1.5MB - Streamlit does not support rendering of files bigger than 1.5MB
    
    if file_size > max_size:
      logger.warning(f"blob: {blob} - Streamlit cannot render files larger than 1.5MB. Defaulting to a direct link to GCS. This may require updates to IAM permissions.")
      st.markdown("The App cannot render files larger than 1.5MB.")
      #link = "https://storage.cloud.google.com/"+uri.lstrip("gs://")
      # st.markdown(show_document(uri), unsafe_allow_html=True) 
    else:
      mime_type = get_mime_type(uri)
      # logger.info(f"uri: {uri}, mime_type: {mime_type}")
      file = blob.download_as_bytes()
      base64_file = base64.b64encode(file).decode('utf-8')
      st.markdown(f'<iframe src="data:{mime_type};base64,{base64_file}" width="100%" height="1000" type="{mime_type}"></iframe>', unsafe_allow_html=True)
