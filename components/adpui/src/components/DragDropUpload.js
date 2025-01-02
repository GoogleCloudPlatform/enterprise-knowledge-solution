/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

/** This page is a subpage for Upload.js where the drag and drop feature is listed here. A user can either drag
 * or drop the files else select on the window to open a popup from which the files are selected
 */

/* eslint-disable react-hooks/exhaustive-deps */
import React from 'react';
import 'react-dropzone-uploader/dist/styles.css';
import Dropzone from 'react-dropzone-uploader';
import '../App.css';
function DragDropUpload(props) {

  // specify upload params and url for your files
  const getUploadParams = ({ meta }) => {
    //console.log("metaa", meta);
    return { url: 'https://httpbin.org/post' }
  }

  // called every time a file's `status` changes
  const handleChangeStatus = ({ meta, file }, status) => { console.log("") }

  // receives array of files that are done uploading when submit button is clicked
  const handleSubmit = (files, allFiles) => {
    //console.log(files.map(f => f.meta));
    props.onFileChange(files);
    // allFiles.forEach(f => f.remove())
  }

  // To style the drag and drop
  const Layout = ({ input, previews, submitButton, dropzoneProps, files, extra: { maxFiles } }) => {
    return (
      <div>
        <div {...dropzoneProps}>
          {previews}
          {files.length < maxFiles && input}
        </div>
        {submitButton}
      </div>
    )
  }

  return (
    <Dropzone
      getUploadParams={getUploadParams}
      onChangeStatus={handleChangeStatus}
      LayoutComponent={Layout}
      inputContent="Drop documents here, or click to browse"
      // styles={{dropzone:{ minHeight: 200, maxHeight: 250, overflow:'scroll' }}}
      // classNames={{ inputLabelWithFiles: defaultClassNames.inputLabel }}
      onSubmit={handleSubmit}
      accept="*"
      submitButtonContent="Upload"
    />
  );
}

export default DragDropUpload;
