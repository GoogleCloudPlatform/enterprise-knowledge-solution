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

import re
import base64
import pandas as pd
import os.path
import pathlib
from dpu.api import fetch_agent_doc, PROJECT_ID, fetch_gcs_object
import streamlit as st

from st_aggrid import (
    GridOptionsBuilder,
    AgGrid,
    ColumnsAutoSizeMode,
    DataReturnMode,
    AgGridTheme,
)  # type: ignore


logger = st.logger.get_logger(__name__)   # pyright: ignore[reportAttributeAccessIssue]


LOGO = os.path.join(os.path.dirname(__file__), "../../app/images/logo.png")


#
# Show a list of sources (fetched from API), and return the selected source document ID
#
def choose_source_id(sources):
    with st.container():
        st.header("Sources")

        # Render list of sources
        gb = GridOptionsBuilder()
        gb.configure_selection(
            selection_mode='single',
        )
        gb.configure_default_column(
            resizable=True,
        )
        gb.configure_auto_height(True)
        gb.configure_column("id", header_name="ID", flex=0)
        gb.configure_column("title", header_name="Title", flex=0)
        gb.configure_column("uri", header_name="GCS", flex=1)
        res = AgGrid(
            pd.DataFrame(sources),
            theme=AgGridTheme.BALHAM,  # pyright: ignore[reportArgumentType]
            gridOptions=gb.build(),
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
            data_return_mode=DataReturnMode.AS_INPUT,
            enable_enterprise_modules=False,
        )

        # Pull out selected row or initial row into selected search result
        if res.selected_rows is not None:
            found_records = res.selected_rows.to_dict("records")
            return found_records[0]['id']  # pylint: disable=unsubscriptable-object

        return None


def show_gcs_object(uri: str, item_metadata: dict):

    logger.info(f'Rendering object {uri}.')

    # Parse URI into bucket and path
    gcs_match = re.match(r"gs://([^/]+)/(.*)", uri)
    if not gcs_match:
        raise Exception(f'invalid GCS object name: {uri}')

    bucket = gcs_match.group(1)
    path = gcs_match.group(2)

    title = pathlib.Path(path).name

    # Fetch the raw data and content_type
    data, content_type = fetch_gcs_object(bucket, path)

    with st.container():
        st.subheader(title, divider=True)

        # Metadata
        st.json(item_metadata, expanded=False)

        # Buttons
        download, console = st.columns(2)
        with download:
            st.download_button(
                'Download',
                data,
                file_name=path,
                mime=content_type,
                help='Download the object')
        with console:
            st.link_button(
                'Console',
                f'https://console.cloud.google.com/storage/browser/_details/{bucket}/{path};tab=live_object?project={PROJECT_ID}',
                help='Open object in console',
                type="secondary")


        mime_types = [
            # application/pdf does not seem to work consistently in all browsers
            # 'application/pdf',
            'text/html',
            'text/plain'
        ]
        if content_type in mime_types:
            with st.expander('Content', expanded=True):
                tab_iframe, tab_markdown = st.tabs(["Raw", "Markdown"])
                with tab_iframe:
                    if content_type == 'application/octet-stream':
                        st.markdown('Not available for application/octet-stream')
                    else:
                        encoded = base64.b64encode(data).decode('utf-8').strip()
                        st.write(f'<embed '
                                 f'src="data:{content_type};base64,{encoded}" width="100%" height="100%" '
                                 f'type="{content_type}" style="align: center"></iframe>',
                                 unsafe_allow_html=True)

                with tab_markdown:
                    # Render the markdown (at least the first bit of it)
                    if content_type == 'text/plain':
                        st.markdown(str(data[:1024], 'utf-8'))
                    else:
                        st.markdown('Only available for text/plain')


def choose_related_document(related_docs: list, initial_value: int):

    # Chosen row 
    chosen_row = related_docs[initial_value]

    if len(related_docs) > 1:
  
        # Create dataframe
        df = pd.DataFrame(related_docs)

        # Extract bucket and path
        df['bucket'] = df['uri'].str.extract(r'gs://([^/]*)/')
        df['path'] = df['uri'].str.extract(r'gs://[^/]*/(.*)$')

        # Extract parent and name from the path
        df['name'] = df['path'].apply(lambda p: pathlib.Path(p).name)
        common_prefix = os.path.commonprefix(
            df['path'].apply(lambda p: pathlib.Path(p).parent).to_list())
        df['full_name' ] = df['path'].apply(lambda p: p[len(common_prefix):])
        with st.container():
            st.subheader('Related Documents', divider=True)


            gb = GridOptionsBuilder()
            gb.configure_selection(
                selection_mode='single',
                pre_selected_rows=[str(initial_value)],
            )
            gb.configure_default_column(
                resizable=True,
            )
            gb.configure_column("name", header_name="Name", flex=1)
            gb.configure_column("mimetype", header_name="Type", flex=0)
            gb.configure_column("status", header_name="Status", flex=0)
            gb.configure_column("full_name", header_name="File", flex=1)
            res = AgGrid(
                df,
                theme=AgGridTheme.BALHAM,  # pyright: ignore[reportArgumentType]
                gridOptions=gb.build(),
                columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                data_return_mode=DataReturnMode.AS_INPUT,
                enable_enterprise_modules=False,
            )

        # Find the chosen row (may be initial if not chosen yet)
        if res.selected_rows is not None:
            chosen_row = res.selected_rows.to_dict("records")[0]  # pylint: disable=unsubscriptable-object

    # Find the doc_id (same as root_doc_id initially, but may change)
    if chosen_row['objid']:
        return chosen_row['objid']
    else:
        return chosen_row['uri']


def show_agent_document(root_doc_id: str):

    logger.info(f'Showing document {root_doc_id}')

    # Get document metadata
    full_doc = fetch_agent_doc(root_doc_id)
    if not full_doc:
        logger.info(f'Could not find document {root_doc_id}')
        st.write(f'Could not find document {root_doc_id}')
        return

    objs = full_doc.get('objs', [])

    # Find row we're starting with in the objects
    initial_value = None
    for i in range(len(objs)):
        if 'objid' in objs[i] and objs[i]['objid'] == root_doc_id:
            initial_value = i

    # Render document is same as the root
    doc_id = root_doc_id

    # If there is a list of objects and this is part of it,
    # then we should show all of the related documents together
    if initial_value is not None:
        doc_id = choose_related_document(full_doc['objs'], initial_value)

    # If it's an Agent document, fetch metadata for it
    if not doc_id.startswith('gs://'):
        doc_info = fetch_agent_doc(doc_id)
        if not doc_info:
            logger.info(f'Could not find document {doc_id}')
            st.write(f'Could not find document {doc_id}')
            return
        uri = doc_info['uri']
        item_metadata = doc_info['metadata']
    else:
        uri = doc_id
        item_metadata = {}

    show_gcs_object(uri, item_metadata)

    logger.info('Done rendering gcs object. Nothing more to do!')
