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
from dpu.components import LOGO, PREAMBLE

logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]

# Page configuration
st.set_page_config(
    page_title="Document Processing & Understanding",
    page_icon=LOGO,
    layout="wide",
)

cols = st.columns([10, 90])
with cols[0]:
    st.write("")
    st.image(LOGO, "", 64)
with cols[1]:
    st.title(":green[DPU App Configurations]")
st.divider()

if not 'preamble' in st.session_state:
    st.session_state['preamble'] = PREAMBLE

with st.container():

    def update_preamble():
        logger.info(f'preamble update: {st.session_state.preamble_new}')
        st.session_state.preamble = st.session_state.preamble_new
    
    preamble_new = st.text_area(
        ":blue[Change the search prompt below:]",
        value=st.session_state["preamble"],
        placeholder="Input the Prompt",
        key="preamble_new",
        on_change=update_preamble,
    )