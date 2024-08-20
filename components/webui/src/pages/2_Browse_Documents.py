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
import pandas as pd  # type: ignore
import streamlit as st  # type: ignore
from st_aggrid import GridOptionsBuilder, AgGrid, ColumnsAutoSizeMode  # type: ignore
from dpu.components import show_agent_document, LOGO
from dpu.api import fetch_all_agent_docs
import pathlib

logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]

st.set_page_config(
    page_title="Browse Documents",
    page_icon=LOGO,
    layout="wide",
)

cols = st.columns([10, 90])
with cols[0]:
    st.write("")
    st.image(LOGO, "", 64)
with cols[1]:
    st.title(":green[Document Corpus]")
st.divider()
st.markdown("""Full Document corpus accessible to the Search App.""")

df = pd.DataFrame(fetch_all_agent_docs())

if len(df) > 0:

  # Extract bucket and path
  df['bucket'] = df['uri'].str.extract(r'gs://([^/]*)/')
  df['path'] = df['uri'].str.extract(r'gs://[^/]*/(.*)$')

  # Extract parent and name from the path
  df['name'] = df['path'].apply(lambda p: pathlib.Path(p).name)
  common_prefix = os.path.commonprefix(
      df['path'].apply(lambda p: pathlib.Path(p).parent).to_list())
  df['full_name' ] = df['path'].apply(lambda p: p[len(common_prefix):])

  gb = GridOptionsBuilder()
  gb.configure_column("name", header_name="Name", flex=0)
  gb.configure_column("full_name", header_name="Full Name", flex=1)
  gb.configure_selection()
  gb.configure_pagination()
  gridOptions = gb.build()

  data = AgGrid(
      df,
      gridOptions=gridOptions,
      columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
      allow_unsafe_jscode=True,
  )

  if data["selected_rows"] is not None and len(data["selected_rows"]) > 0:
      show_agent_document(data["selected_rows"].iloc[0]['id'])