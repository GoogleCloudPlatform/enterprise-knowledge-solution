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
from dpu.components import show_agent_document, choose_source_id, LOGO, PREAMBLE
from dpu.api import generate_answer

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
    st.title(":green[Search and summarize Documents]")
st.divider()


#
# Initialize session state
#


if not 'answer' in st.session_state:
    st.session_state['answer'] = ''
if not 'sources' in st.session_state:
    st.session_state['sources'] = []
if not 'chosen_row' in st.session_state:
    st.session_state['chosen_row'] = None
if not 'preamble' in st.session_state:
    st.session_state['preamble'] = PREAMBLE

#
# Form
#


st.markdown(
    """### Given a query, DPU will generate an answer with citations to the documents."""
)

# Render the question
with st.container():

    def question_change():
        result = generate_answer(st.session_state.question, preamble=st.session_state['preamble'])
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

# Render answer if there's an answer
if st.session_state.answer:
    st.text_area(
        ":blue[Summary Response: ]",
        value=st.session_state.answer,
    )

# Render list of sources used if there are sources
if st.session_state.sources:
    st.session_state['source_id'] = choose_source_id(st.session_state.sources)

# Render a search result if one is selected
if 'source_id' in st.session_state and st.session_state.source_id:
  logger.info(f'source_id: {st.session_state.source_id}')
  st.divider()
  st.header("Document Details")
  show_agent_document(st.session_state.source_id)
