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

/** This page renders a PDF view and the extracted values in the inputboxes. Here there are two cases
 * a) PDF with the extracted values
 * b) If the document is unclassifed, a user can manually classify by selected the doument class
 *
 * When a user selects an input box then the associated field is highlighted in the PDF using the canvas.
 * If the coordinates are not extracted it throws an error. And also supporting documents don't
 * extract the coordinates so not able to draw rectangles.
 */


import React, { useState, useEffect, useRef } from 'react';
import { Container, Col, Row, Button, FloatingLabel, Form, Card, ProgressBar } from 'react-bootstrap';

import { useHistory } from 'react-router-dom'
import {
  useLocation, Link, useParams
} from "react-router-dom";
import axios from 'axios';
import moment from 'moment';
import { ToastContainer, toast } from 'react-toastify';
import { BsFillCheckCircleFill } from 'react-icons/bs';
import 'react-toastify/dist/ReactToastify.css';
import { baseURL } from '../configs/firebase.config';
import options from '../configs/DocTypeClass';
import { ReactComponent as Check } from '../images/check-circle.svg';
import { ReactComponent as File } from '../images/file.svg';
import { ReactComponent as Cross } from '../images/cancel.svg';
import { ReactComponent as Back } from '../images/arrow-back.svg';
import Headers from './Headers';
import '../App.css'
import '../css/DocumentReview.css'


var pdfjsLib = window['pdfjs-dist/build/pdf'];
pdfjsLib.GlobalWorkerOptions.workerSrc = '//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';


let inputData = [];
let inputDocClass = '';
let inputDocType = '';
let viewer = ''
var thePdf = null;
let headerHeight;

function DocumentReview() {
  const myRef = useRef(null)

  const toastId = React.useRef(null);

  // Set the states and retireving the navigation parameters
  var context = '';
  let canvas = '';

  //  const { state: { uid, caseid } } = useLocation();
  const { uid, caseid } = useParams();
  console.log("USE PARMAS", uid)
  const history = useHistory();
  const [comments, setComment] = useState([]);
  const [inputList, setInputList] = useState([]);
  const [notes, setNotes] = useState('');
  const [applicationForm, setApplicationForm] = useState('');

  useEffect(() => {
    // based on the uid, get the document for the page
    let url = `${baseURL}/hitl_service/v1/fetch_file?case_id=${caseid}&uid=${uid}`;

    console.log(`Calling ${baseURL}/hitl_service/v1/get_document?uid=${uid}`);
    axios.post(`${baseURL}/hitl_service/v1/get_document?uid=${uid}`, {
    }).then(res => {
      console.info("document data:");
      console.info(res);

      console.info("API RESPONSE DATA", res.data);
      inputData = res.data.data;
      if (inputData && inputData.document_class !== null) {
        inputDocClass = inputData.document_class.split('_').join(" ");
        inputDocType = inputData.document_type.split('_').join(" ")
      }

      console.info("INPUTDATA", inputData)
      let auditTrail = []
      if (inputData && inputData['audit_trail']) {
        console.info("inputData['audit_trail']")
        console.info(inputData['audit_trail'])
        setComment(inputData['audit_trail'] || []);
      } else {
        setComment([]);
      }

      setInputList(inputData.entities)
      console.info("INPUT LIST", inputList);

      // To display PDF onload
      pdfjsLib.getDocument(url).promise.then(function (pdf) {
        thePdf = pdf;
        viewer = document.getElementById('pdf-viewer');
        renderPage(pdf.numPages)
      });
    }).catch((err) => {
      console.error("error", err);
      toast.error(`${err}`, {
        position: "bottom-center",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      });
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  let currPage = 1;
  // Based on the pagenumbers the PDF can be rendered
  function renderPage() {
    headerHeight = ('220px')

    //pageNumber = 1;
    thePdf.getPage(currPage).then(function (page) {
      console.log('Page loaded');
      canvas = document.createElement("canvas");
      canvas.className = `pdf-page-canvas-${currPage}`;
      canvas.strokeStyle = 'black'
      viewer.appendChild(canvas);
      var scale = 1.5;
      var rotation = 0;
      var dontFlip = 0;
      var viewport = page.getViewport({ scale, rotation, dontFlip });

      // Prepare canvas using PDF page dimensions
      context = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      //page.render({canvasContext: canvas.getContext('2d'), viewport: viewport});
      var renderContext = {
        canvasContext: context,
        viewport: viewport
      };
      var renderTask = page.render(renderContext);
      renderTask.promise.then(function () {
        console.log("Pahge rendered")
      });

      currPage++;
      if (thePdf !== null && currPage <= thePdf.numPages) {
        console.log("currpage")

        thePdf.getPage(currPage).then(renderPage);
      }
    })
  }

  // This function is called when we draw the rectangles on any of the PDF document by removing a page and replacing that page with the hightlited of the selected field.
  function againrenderPage(startPage, pageNumber, obj, color) {
    console.log("pageNumber,obj", startPage, pageNumber, obj)
    currPage = startPage;
    console.log("&&&&&&&", currPage, thePdf)
    thePdf.getPage(currPage).then(function (page) {
      console.log('Page loaded', page);
      canvas = document.createElement("canvas");
      canvas.className = `pdf-page-canvas-${currPage}`;
      canvas.strokeStyle = 'black'
      viewer.appendChild(canvas);
      var scale = 1.5;
      var rotation = 0;
      var dontFlip = 0;
      var viewport = page.getViewport({ scale, rotation, dontFlip });

      // Prepare canvas using PDF page dimensions
      context = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      //page.render({canvasContext: canvas.getContext('2d'), viewport: viewport});
      var renderContext = {
        canvasContext: context,
        viewport: viewport
      };
      var renderTask = page.render(renderContext);
      renderTask.promise.then(function () {
        console.log("Pahge rendered");
        if (pageNumber === currPage) {
          const { x1, x2, y1, y2 } = obj;
          console.log("OBJJJJJ", obj);
          let x = x1 * canvas.width;
          let y = y1 * canvas.height;
          let w = (x2 * canvas.width) - (x1 * canvas.width)
          let h = (y2 * canvas.height) - (y1 * canvas.height)

          console.log("X,Y,W,H", x, y, w, h)
          context.strokeStyle = "#4285F4";
          context.fillStyle = color;
          context.fillRect(x, y, w, h);
          context.lineWidth = 5;
          context.strokeRect(x, y, w, h);
        }
        currPage++;
        console.log("currpagee", currPage, thePdf.numPages, thePdf)
        if (thePdf !== null && currPage <= thePdf.numPages) {
          console.log("currpages", currPage)
          thePdf.getPage(currPage).then(againrenderPage(currPage, pageNumber, obj, color));
        }
      });

    })
  }

  // handle input change, when the inputboxes are clicked
  const handleInputChange = (e, index, rectData) => {
    console.log("onchange input", e, index);
    const { value } = e.target;
    const list = [...inputList];
    list[index]['corrected_value'] = value;
    console.log("LIST", list)
    setInputList(list);
  };

  // to save the edited fields record
  const saveUpdatedButton = () => {
    console.log("SAVE UPDATES CLICKED updated correct value", inputList);
    console.log("comment in save update", comments)
    console.log("API DATA", inputData)
    setComment(comments);

    axios.post(`${baseURL}/hitl_service/v1/update_entity?uid=${inputData.uid}`, inputData).then((saveUpdates) => {
      console.log("Updates saved", saveUpdates);
      toast.success("Changes Saved Successfully !", {
        position: "bottom-center",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      })
      history.push('/')

    }).catch((err) => {
      console.log("error", err);
      toast.error(`${err}`, {
        position: "bottom-center",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      });
    })
  };


  //HITL Status for Approve,Reject and Pending/Review
  const hitlStatusButton = (status) => {
    console.log("hitl status clicked");
    const sendObj = {
      uid: inputData.uid,
      status: status,
      user: localStorage.getItem('user').split('@')[0],
      comment: notes
    }
    console.log("sendObj", sendObj);
    axios.post(`${baseURL}/hitl_service/v1/update_hitl_status?uid=${sendObj.uid}&status=${sendObj.status}&user=${sendObj.user}&comment=${sendObj.comment}`).then((responseData) => {
      console.log("status updated API response", responseData);
      history.push('/')
      toast.success(`Successfully changed Status to ${status}`, {
        position: "bottom-center",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      })

    }).catch((err) => {
      console.log("error", err);
      toast.error(`${err}`, {
        position: "bottom-center",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
      });
    })
  }

  // When the user selects the button, the associated values are passed so that a rectangle can be drawn on PDF
  function inputClicked(data) {
    console.log("DATA", data)
    if (data.value_coordinates !== undefined) {
      console.log("Data", data)
      console.log("data cordinates", data.value_coordinates)
      let obj = {
        x1: data.value_coordinates[0] - 0.01,
        x2: data.value_coordinates[2] + 0.01,
        y1: data.value_coordinates[1] - 0.01,
        y2: data.value_coordinates[7] + 0.01,
        page: data.page_no
      }
      console.log("+3 added", obj)
      let pageN = data.page_no
      let color = data.extraction_confidence > 0.90 ? 'hsla(120,100%,75%,0.3)' : (data.extraction_confidence < '0.70' ? 'hsl(0, 100%, 50%,0.3)' : 'hsl(39, 100%, 50%,0.3)')
      callPage(pageN, obj, color)

    }
    else {
      console.log("else condition")
      const element = document.querySelectorAll('canvas').forEach(e => {
        console.log("e", e.className)
        e.remove()
      });
      againrenderPage(1, 0, 0)
      //toast.error('Unable to Detect Field Location',{ pauseOnFocusLoss: false})
      if (!toast.isActive(toastId.current)) {
        console.log(inputData);
        toastId.current = toast.error("Unable to Detect Field Location");
      }

    }
  }

  function callPage(pageN, obj, color) {
    let url = `${baseURL}/hitl_service/v1/fetch_file?case_id=${caseid}&uid=${uid}`
    // context = '';
    //canvas = '';
    //viewer='';
    const element = document.querySelectorAll('canvas').forEach(e => {
      console.log("e", e.className)
      e.remove()
    });
    //pdfjsLib.getDocument(url).promise.then(function (pdf) {
    //thePdf = pdf;
    //viewer = document.getElementById('pdf-viewer');
    //console.log("viwer 1",viewer);
    againrenderPage(1, pageN, obj, color)
    //});
  }

  return (
    <div>
      <Headers />
      <div className="subHeaderReview">

        <div className="row">
          <div className="col-8" style={{ position: "relative", paddingBottom: '0px' }}>
            <Link to={{ pathname: '/', }} className="drBack">
              <Back fill="#aaa" />
            </Link>{' '}

          </div>
          <div className="col-4" style={{ paddingBottom: '0px', textAlign: 'end', width: '20%;' }}>
            <label className="approveLeftVerticalLine">&nbsp;</label>
            <Button type="button" className="buttonStyles" style={{ backgroundColor: "#4285F4" }} onClick={() => hitlStatusButton('Approved')}>Approve</Button>
            <Button type="button" className="buttonStyles" style={{ backgroundColor: "#4285F4" }} onClick={() => hitlStatusButton('Pending')}>Pend</Button>
            <Button type="button" className="buttonStyles" variant="danger" onClick={() => hitlStatusButton('Rejected')}>Reject</Button>

            <label className="approveLeftVerticalLine">&nbsp;</label>

            {/* <Button type="button" className="buttonStyles" style={{backgroundColor:"#4285F4"}} >Reassign</Button>  */}
            <Link to={{
              pathname: `/reassign`,
              state: {
                uid: `${inputData.uid}`,
                caseid: `${inputData.case_id}`
              }
            }} style={{ backgroundColor: '#4285F4', color: "#fff", borderRadius: '20px', lineHeight: '1.7', display: 'inline-block', fontWeight: '400', padding: '4px', fontSize: '15px', textDecoration: 'none', marginRight: "5px" }}>Reassign</Link>


            {/* <Button type="button" className="buttonStyles" style={{backgroundColor:"#4285F4"}} onClick={downloadPDF}>Download</Button> */}
            <a style={{ backgroundColor: '#4285F4', color: "#fff", borderRadius: '20px', lineHeight: '1.7', display: 'inline-block', fontWeight: '400', padding: '4px', fontSize: '15px', textDecoration: 'none' }} href={`${baseURL}/hitl_service/v1/fetch_file?case_id=${inputData.case_id}&uid=${inputData.uid}&download=true`} target={"_blank"}>
              Download
            </a>
            <Button type="button" className="buttonStyles" style={{ backgroundColor: "#4285F4" }} onClick={saveUpdatedButton}>Save</Button>
          </div>
        </div>

      </div>
      {/* <div className="row">

  </div> */}
      <div className='custom-container'>
        {/*To perform the actions*/}


        {/** TO display the PDF and the extracted values of the PDF*/}

        <Row style={{ marginRight: '0px' }}>
          <Col className="col-7" style={{ paddingTop: '0px', overflow: 'scroll', height: 'calc(100vh - ' + headerHeight + ')' }}>
            <div ref={myRef} id='pdf-viewer' style={{ width: '100%', minWidth: '500px', maxWidth: '1200px', backgroundColor: '#ccc', paddingTop: '0px' }}></div>
          </Col>

          <Col className="col-5" style={{ paddingLeft: '0', paddingTop: '0' }}>
            <Container style={{ overflow: 'scroll', height: 'calc(100vh - ' + headerHeight + ')', marginLeft: '10px', padding: '2px' }}>

              <div style={{ backgroundColor: 'white', padding: '8px' }}>
                <Row className="labelVerticalLine">
                  <Col className={["col", "verticalLines"].join(" ")}>
                    <label className="labelBold">Extraction Score</label> <br />
                    <label style={{ color: inputData['extraction_score'] > 0.90 ? ' #93c47d' : (inputData['extraction_score'] < 0.70 ? 'hsl(0, 100%, 50%)' : 'hsl(39, 100%, 50%)'), fontSize: '30px' }}> {inputData.extraction_score === null ? '-' : (inputData.extraction_score * 100).toFixed(1) + '%'}</label>
                  </Col>

                </Row>
                {inputData.entities === null ? '' :
                  <Row className="labelVerticalLine">
                    <Col className={["col", "verticalLines"].join(" ")}>
                      <label className="">Fields</label>
                    </Col>

                  </Row>
                }
                {inputList && inputList.map((x, i) => {
                  console.log("Value for key", x['entity'], "=",  x['value'] )
                  return (
                    <Row>
                      <Col className={["col", "verticalLines"].join(" ")}>

                        <div className="box" key={x['entity']}>
                          {x['corrected_value'] === null ?
                            <FloatingLabel
                              controlId="floatingInput"
                              label={x['entity']}
                            //  className="mb-3"
                            >
                              <Form.Control type="text" name="value" className="extractedInputBox"
                                placeholder="Enter extracted value"
                                defaultValue={x['value']}
                                style={{ borderColor: x['extraction_confidence'] < 0.70 ? '#E93535' : '' }}
                                onChange={e => handleInputChange(e, i, inputList[i])}
                                onFocus={() => inputClicked(inputList[i])} />
                            </FloatingLabel>
                            :
                            <FloatingLabel
                              controlId="floatingInput"
                              label={x['entity']}
                            //  className="mb-3"
                            >
                              <Form.Control type="text" name="corrected_value" className="extractedInputBox"
                                placeholder="Enter Corrected value"
                                defaultValue={x.corrected_value }
                                onChange={e => handleInputChange(e, i)}
                                onFocus={() => inputClicked(inputList[i])} />
                            </FloatingLabel>

                          }
                          <label style={{ fontSize: '10px', color: x['extraction_confidence'] > 0.90 ? ' #93c47d' : (x['extraction_confidence'] < 0.70 ? 'hsl(0, 100%, 50%)' : 'hsl(39, 100%, 50%)') }}>Extraction Score: {(x['extraction_confidence'] * 100).toFixed(1)}{'%'}</label>
                        </div>
                      </Col>

                    </Row>
                  );
                })}
                <FloatingLabel controlId="floatingTextarea" label="Notes" className="mb-3">
                  <Form.Control as="textarea" value={notes} style={{ borderRadius: '12px', height: '8rem' }} onInput={e => setNotes(e.target.value)} placeholder="Leave a comment here" />
                </FloatingLabel>
              </div>

              <Row className="drHistoryContainer">
                {comments.length !== 0 ? <label className="labelBold">Change History</label> : ''}

                {comments.map((x, i) => {
                  return (

                    <Card className="changeHistory">
                      <Card.Body>
                        <Card.Text as='div'>
                          <Row className="commentRow">
                            <Col className="col-3">
                              <label>Timestamp</label>
                            </Col>
                            <Col>
                              <label className="labelBold">{moment(x['timestamp']).fromNow()} ({moment(x['timestamp']).format("YYYY-MM-DD HH:mm")})</label>
                            </Col>
                          </Row>

                          <Row className="commentRow">
                            <Col className="col-3">
                              <label>Updated By</label>
                            </Col>
                            <Col>
                              <label className="labelBold">{x['user'] ? x['user'] : 'System'}</label>
                            </Col>
                          </Row>

                          {x['stage'] &&
                            <Row className="commentRow">
                              <Col className="col-3">
                                <label>Process Stage</label>
                              </Col>
                              <Col>
                                <label className="labelBold">{x['stage']}</label>
                              </Col>
                            </Row>
                          }

                          <Row className="commentRow">
                            <Col className="col-3">
                              <label>{x['stage'] ? 'System Status' : 'Approval Status'}</label>
                            </Col>
                            <Col>
                              <label className="labelBold">{x['status']}</label>
                            </Col>
                          </Row>

                          <Row className="commentRow">
                            <Col className="col-3">
                              <label>Comment</label>
                            </Col>

                            <Col>
                              <label className="labelBold">{x['comment'] === '' ? 'N/A' : x['comment']}</label>
                            </Col>

                          </Row>
                        </Card.Text>
                      </Card.Body>
                    </Card>

                  )

                })}
              </Row>

            </Container>
          </Col>
        </Row>

      </div>
    </div >
  )
}

export default DocumentReview;

