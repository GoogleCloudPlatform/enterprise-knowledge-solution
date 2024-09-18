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
from dpu.api import generate_answer
from dpu.components import LOGO, PREAMBLE, choose_source_id, show_agent_document

logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]

# Put into a single place
SAMPLE_QUERIES = """
```
    When was Form S-1 submitted by CHROMOCELL THERAPEUTICS CORPORATION?
```
```
    How does Maxim Group LLC work with CHROMOCELL THERAPEUTICS CORPORATION?
```
```
    How can we automate our document processing workflow to save time and reduce errors?
```
```
    How can we automate our document processing workflow to save time and reduce errors? Answer in hindi.
```
```
    How can we automate our document processing workflow to save time and reduce errors? Generate answer in spanish.
```
```
    समय बचाने और त्रुटियों को कम करने के लिए हम अपने दस्तावेज़ प्रसंस्करण वर्कफ़्लो को कैसे स्वचालित कर सकते हैं?  अंग्रेज़ी में उत्तर दें.
```
```
    How many shares are offered by Ryde Group Ltd?
```
```
    Create a table to list 2021 and 2022 Revenue of Ryde Group Ltd. and Intelligent Group Limited.
```
"""

#
# Page Layout
#

# Page configuration
st.set_page_config(
    page_title="Search and Summarization",
    page_icon=LOGO,
    layout="wide",
)

# Title
image_col, text_col = st.columns([10, 90])
with image_col:
    st.write("")
    st.image(LOGO, "", 64)
with text_col:
    st.title(":green[Search and Summarize Documents]")
st.divider()


#
# Initialize session state
#


if "answer" not in st.session_state:
    st.session_state["answer"] = ""
if "sources" not in st.session_state:
    st.session_state["sources"] = []
if "chosen_row" not in st.session_state:
    st.session_state["chosen_row"] = None
if "preamble" not in st.session_state:
    st.session_state["preamble"] = PREAMBLE

#
# Form
#


st.markdown(
    """### Given a query, EKS will generate an answer with citations to the documents."""
)

if "preamble" not in st.session_state:
    st.session_state["preamble"] = PREAMBLE

my_js = """ const textArea = document.querySelector('.textarea-test')
    textArea.addEventListener('input',(e)=>{
    textArea.style.height = "auto"
    textArea.style.height = '${textArea.scrollHeight}px';
    }) """

# Render the question
with st.container():

    def update_preamble():
        logger.info(f"preamble update: {st.session_state.preamble_new}")
        st.session_state.preamble = st.session_state.preamble_new

    preamble_new = st.text_area(
        ":blue[Change the :orange[***search context***] below:]",
        value=st.session_state["preamble"],
        placeholder="Search Context",
        key="preamble_new",
        on_change=update_preamble,
        height=140,
    )

    def question_change():
        result = generate_answer(
            st.session_state.question, preamble=st.session_state["preamble"]
        )
        st.session_state.answer = result["answer"]
        st.session_state.sources = result["sources"]

    question_col, example_col = st.columns([85, 15])
    with question_col:
        question = st.text_input(
            ":blue[Type a :orange[***question***] in the box below:]",
            value="",
            placeholder="Question",
            key="question",
            on_change=question_change,
        )
    with example_col:
        st.write("")
        with st.popover("Examples"):
            st.markdown(SAMPLE_QUERIES)

# Render answer if there's a summary returned in the response
if st.session_state.answer:
    st.text_area(":blue[Summary Response: ]", value=st.session_state.answer, height=140)

# Render list of other documents
if st.session_state.sources:
    st.session_state["source_id"] = choose_source_id(
        st.session_state.sources, "Search Results"
    )

# Render the selected document or reference
if "source_id" in st.session_state and st.session_state.source_id:
    logger.info(f"source_id: {st.session_state.source_id}")
    show_agent_document(st.session_state.source_id)
