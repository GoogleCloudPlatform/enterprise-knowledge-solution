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

import streamlit as st  # type: ignore
from dpu.components import LOGO


logger = st.logger.get_logger(__name__)   # pyright: ignore[reportAttributeAccessIssue]


st.set_page_config(
    page_title="EKS Web UI",
    page_icon=LOGO,
    layout="wide",
)

cols = st.columns([10, 90])
with cols[0]:
    st.write("")
    st.image(LOGO, "", 64)
with cols[1]:
    st.title(":green[Enterprise Knowledge Solution (EKS) Web UI]")

st.markdown("""   """)
st.markdown("""
    ### About
    This app demonstrates the search and summarization capabilities of the
    Enterprise Knowledge Solution (EKS).

    The app integrates with the Vertex AI Agent Builder using APIs.
""")

if st.button("Start Search"):
    st.switch_page("pages/1_Search_Documents.py")

st.divider()
