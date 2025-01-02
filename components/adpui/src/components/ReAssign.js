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

/* This page is to reassign the supporting document to a particular application document. A user can assign
 * an application form by clicking on search applicant button where a list of application app registration
 * ids will be displayed and select a row to assign any one of them to the supporting doc
 */


/* eslint-disable eqeqeq */
import { useEffect, useState } from "react";
import axios from 'axios';
import { Card, Button, FloatingLabel, Form, Container, Row, Col } from 'react-bootstrap';
import {
  Link, useHistory
} from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import {
  useLocation
} from "react-router-dom";
import { ReactComponent as File } from '../images/file.svg';
import Headers from "./Headers";
import { baseURL } from '../configs/firebase.config';
import '../css/ReAssign.css'
import { ReactComponent as Back } from '../images/arrow-back.svg';



var pdfjsLib = window['pdfjs-dist/build/pdf'];
pdfjsLib.GlobalWorkerOptions.workerSrc = '//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

let viewer = ''
var thePdf = null;
let inputDocType = '';
let inputDocClass = '';

function ReAssign() {

  var context = '';
  let canvas = '';


  //setting the states and retrieving the navigation parameters
  const { state: { uid, caseid } } = useLocation();
  console.log("UISSS", uid, caseid)
  const history = useHistory();
  const [selectedCaseId, setSelectedCaseId] = useState();
  const [previousCaseIDData, setPreviousCaseIDData] = useState([]);
  const [comments, setComment] = useState('');
  const [tableComponent, setTableComponent] = useState(false);
  const [selectedRowDetails, setSelectedRowDetails] = useState({ case_id: '--', applicant_name: '--' });
  const [applicationForm, setApplicationForm] = useState('')

  // To display the data that is selected to reassign the document to any other application reg id
  function apiCall() {
    //calling the API, to set the table data based on the UI selccted from the previous screen
    return new Promise((resolve, reject) => {
      axios.post(`${baseURL}/hitl_service/v1/get_document?uid=${uid}`, {
      }).then(res => {
        console.log("previous caseIDData", res.data.data);
        let inputData = res.data.data
        if (inputData && inputData.document_class !== null) {
          inputDocClass = inputData.document_class.split('_').join(" ");
          inputDocType = inputData.document_type.split('_').join(" ")
        }
        resolve(res.data.data)
      })
        .catch((err) => {
          reject(err)
        })
    })
  }


  useEffect(() => {
    let url = `${baseURL}/hitl_service/v1/fetch_file?case_id=${caseid}&uid=${uid}`
    console.log("DATA REASSIGN", uid);
    setTableComponent(true);

    apiCall().then((data) => {
      console.log("APIDATA", data);
      setPreviousCaseIDData(data)


      pdfjsLib.getDocument(url).promise.then(function (pdf) {
        thePdf = pdf;
        viewer = document.getElementById('pdf-viewer');
        renderPage(pdf.numPages)
      });
    })


    // To display PDF onload

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {



  }, [])

  let currPage = 1;
  // Based on the pagenumbers the PDF can be rendered
  function renderPage() {

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


  const handleTableData = (searchTableDetails) => {
    console.log("cleared", searchTableDetails);
    setSelectedRowDetails({ case_id: searchTableDetails.caseid, applicant_name: searchTableDetails.applicantname })
    if (searchTableDetails === undefined) {
      setSelectedCaseId()
    }
    else {
      setSelectedCaseId(searchTableDetails);
    }
  }

  // When a reassign button is clicked
  const reassignCaseId = () => {
    console.log("old caseid", previousCaseIDData.case_id);
    console.log("uid", uid.uid);
    console.log("new caseid", selectedCaseId.caseid);
    console.log("user", localStorage.getItem('user').split('@')[0])
    console.log("comments", comments)

    let sendObj = {
      old_case_id: previousCaseIDData.case_id,
      uid: uid,
      new_case_id: selectedCaseId.caseid,
      user: localStorage.getItem('user').split('@')[0],
      comment: comments
    }

    axios.post(`${baseURL}/hitl_service/v1/reassign_case_id`, sendObj).then((reassignResponse) => {
      console.error("Reassign response", reassignResponse);
      history.push("/");
    }).catch(err => {
      console.error(err);
      toast.error(err.message,
        {
          position: "bottom-center",
          autoClose: 3000,
          hideProgressBar: true,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
          progress: undefined,
        });
    })
  }

  return (
    <div >
      <Headers />
      <div className="subHeaderReassign">
        <Link to={{ pathname: '/', }} className="drBack">
          <Back fill="#aaa" />
        </Link>{' '}
        <label className={["raLabels", "raSpace"].join(" ")}> Reassign a Document</label>
      </div>
      <div>
        <Container style={{ padding: '0', marginBottom: '20px', marginTop: '20px' }}>
          <Card className="raSearchCard">
            <Card.Body>
              {/** TO show a pop and select the caseid to reassign */}

              <label className="raSubTitle">
                Search for existing applications:
              </label>

              <br />
              <Row style={{ float: 'right' }}>
                {selectedCaseId ? <Button onClick={reassignCaseId} className="reassignButton">Reassign</Button> : <Button disabled className="reassignButton">Reassign</Button>}
              </Row>
            </Card.Body>
          </Card>
        </Container>
        <br />
        <Container>
          <label className="raSubTitle">
            Document to change:
          </label>
        </Container>
        <Container className="raContainer">
          <Row>
            <Card className="raCard">
              <Card.Body>
                <Card.Title as='div'>
                  <label className="raSubTitle"><span> <File /></span> {inputDocType} {'>'} {inputDocClass}  </label>

                </Card.Title>
              </Card.Body>
            </Card>
          </Row>
          <Row>
            <Col className={["col-7", "raPdfView"].join(' ')}  >
              <div id='pdf-viewer' style={{ width: '100%', minWidth: '800px', maxWidth: '1200px', backgroundColor: '#ccc' }}></div>
            </Col>

            <Col className={["col-5", "raData"].join(' ')} >
              <Row>
                <Col className="col-5">
                  <label className="ralabelBold">Current Assigned Application</label>

                </Col>

                <Col className="col-7">
                  {/* <Link target= {"_blank"} to={{
						pathname: `/documentreview/${previousCaseIDData.uid}/${previousCaseIDData.case_id}`,
					  }} className="saActionButton">{previousCaseIDData.case_id}</Link> */}
                  <Link target="_blank" to={{
                    pathname: `/documentreview/${applicationForm}/${caseid}`,

                  }} >{caseid}</Link>
                </Col>

              </Row>

              {/*<Row>*/}
              {/*  <Col className="col-5">*/}
              {/*    <label className="ralabelBold">Applicant Name</label>*/}
              {/*  </Col>*/}
              {/*  <Col className="col-7">*/}
              {/*    <label>{previousCaseIDData.applicant_name}</label>*/}
              {/*  </Col>*/}
              {/*</Row>*/}

              <Row>
                <Col className="col-5">
                  <label className="ralabelBold">Approval Status</label>
                </Col>
                <Col className="col-7">
                  <label>{previousCaseIDData.current_status}</label>
                </Col>
              </Row>

              <Row>
                <Col className="col-5">
                  <label className="ralabelBold">Doc Processing Status</label>
                </Col>
                <Col className="col-7">
                  <label>{previousCaseIDData.process_status}</label>
                </Col>
              </Row>

              <Row>
                <Col className="col-5">
                  <label className="ralabelBold">New Assigned Application </label>
                </Col>
                <Col className="col-7">
                  <label>{selectedRowDetails.case_id}</label>
                </Col>
              </Row>

              <Row>
                <Col className="col-5">
                  <label className="ralabelBold">New Application Name </label>
                </Col>
                <Col className="col-7">
                  <label>{selectedRowDetails.applicant_name}</label>
                </Col>
              </Row>
              <Row>
                <Col className="col-12">
                  <FloatingLabel controlId="floatingTextarea" label="Notes" >
                    <Form.Control as="textarea" value={comments} onInput={e => setComment(e.target.value)} placeholder="Leave a comment here" className="notesSection" style={{ height: '8rem' }} />
                  </FloatingLabel>
                </Col>
              </Row>
            </Col>
          </Row>
        </Container>
        <br />
      </div>

      {/* </div> */}

      <ToastContainer
        position="bottom-center"
        autoClose={3000}
        hideProgressBar
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />

    </div >
  )
}

export default ReAssign;
