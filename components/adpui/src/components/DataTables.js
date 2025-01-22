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

/** This page is the subpage of Dashboard.js where the application details are shown. A user can select based on
 * the HITL status (Review/Pending/Approved/Rejected) and unclassified.
 * Refresh button is to refresh the table as the ML process take sometime to process the data
 * Search API is to search the records
 */
import { useState, useEffect, useCallback } from "react";
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Container, Row, Col, Button, OverlayTrigger, Popover, Spinner } from 'react-bootstrap';
import { parse } from 'date-fns';
import axios from 'axios';
import {
  Link,
} from 'react-router-dom';
import { BsArrowRepeat } from 'react-icons/bs';
import { baseURL } from '../configs/firebase.config';
import { Ripple } from 'primereact/ripple';
import moment from 'moment';
import { classNames } from 'primereact/utils';
import 'primeicons/primeicons.css';
import 'primereact/resources/themes/lara-light-indigo/theme.css';
import 'primereact/resources/primereact.css';
import 'primeflex/primeflex.css';
import { toast } from "react-toastify";
import '../css/DataTable.css';

function DataTables() {

  //set the states for the table and button enable actions
  const [isLoading, setIsLoading] = useState(false);
  const [dataTableBody, setDataTableBody] = useState([]);

  const [activeAllButton, setActiveAllButton] = useState(false);
  const [activeReviewButton, setActiveReviewButton] = useState(false);
  const [activePendingButton, setActivePendingButton] = useState(false);
  const [activeApprovedButton, setActiveApprovedButton] = useState(false);
  const [activeRejectedButton, setActiveRejectedButton] = useState(false);
  const [activeUnclassifiedButton, setActiveUnclassifiedButton] = useState(false);
  const [activeManualClassifyButton, setActiveManualClassify] = useState(false);
  const [tableLength, setTableLength] = useState('0 documents found');

  const [filter, setFilter] = useState('');
  let [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1);
  const [first1, setFirst1] = useState(0);
  const [rows1, setRows1] = useState(20);

  useEffect(() => {
    setActiveReviewButton(false);
    setActivePendingButton(false);
    setActiveApprovedButton(false);
    setActiveRejectedButton(false);
    setActiveUnclassifiedButton(false);

    //At intial load all Queues will be called
    allQ()
  }, [])


  // To set the filter text
  const onFilter = (e) => {
    console.log("text", e.target.value)
    setFilter(e.target.value);
    setSearchTerm(e.target.value)
  };

  const enterKeyPressed = (e) => {
    console.log("Enter key pressed")
    var code = e.keyCode || e.which;
    if (code === 13) {
      buttonClicked()
    }

  }

  const buttonClicked = () => {
    console.log("SEARCH...", searchTerm)
    if (searchTerm) {
      setIsLoading(true)
      console.log("SEARCH TERM", searchTerm);
      setDataTableBody([])
      searchTerm = searchTerm.replace(/^\s+|\s+$/g, '');
      tableAPICall(searchTerm).then((responseData) => {
        console.log("Search term response", responseData)
        setTableLength(responseData[0].length + ' documents found');
        setDataTableBody(responseData[0]);
        setIsLoading(false);
      })
    }
    else {
      allQ();
    }
  }


  // To refresh the data present in the table
  const tableRefresh = () => {
    console.log("table refresh called");
    allQ();
  }

  // To display the message if the reassign is disabled
  const popover = (
    <Popover id="popover-basic" >
      <Popover.Body style={{ padding: 0 }}>
        Reassign not supported for Application forms
      </Popover.Body>
    </Popover>
  );

  // When the all pill is selected
  const allQ = async () => {
    setSearchTerm('')
    setIsLoading(true)
    setDataTableBody([])
    setActiveRejectedButton(false);
    setActiveApprovedButton(false);
    setActivePendingButton(false);
    setActiveUnclassifiedButton(false);
    setActiveReviewButton(false);
    setActiveManualClassify(false);
    setActiveAllButton(true);
    tableAPICall(searchTerm, 'all').then((responseData) => {
      console.log("review responseData", responseData)
      setTableLength(responseData[0].length + ' documents found')
      setDataTableBody(responseData[0]);
      setIsLoading(false);
    })

  }

  // When the review pill is selected
  const reviewQ = async () => {
    setSearchTerm('')
    setIsLoading(true)
    setDataTableBody([])
    setActiveRejectedButton(false);
    setActiveApprovedButton(false);
    setActivePendingButton(false);
    setActiveAllButton(false);
    setActiveManualClassify(false)
    setActiveUnclassifiedButton(false);
    setActiveReviewButton(true);
    tableAPICall(searchTerm, 'Need Review').then((responseData) => {
      console.log("review responseData", responseData)
      setTableLength(responseData[0].length + ' documents found')
      setDataTableBody(responseData[0]);
      setIsLoading(false)
    })

  }
  // When the approved pill is selected
  const approvedQ = async () => {
    setIsLoading(true)
    setDataTableBody([])
    setActivePendingButton(false);
    setActiveRejectedButton(false);
    setActiveAllButton(false);
    setActiveReviewButton(false);
    setActiveUnclassifiedButton(false);
    setActiveManualClassify(false)
    setActiveApprovedButton(true);
    tableAPICall(searchTerm, 'Approved').then((responseData) => {
      console.log("approved responseData", responseData)
      setTableLength(responseData[0].length + ' documents found')
      setDataTableBody(responseData[0]);
      setIsLoading(false)
    })

  }

  // When the pending pill is selected
  const pendingQ = async () => {
    setSearchTerm('')
    setIsLoading(true)
    setDataTableBody([])
    setActiveReviewButton(false);
    setActiveRejectedButton(false);
    setActiveAllButton(false);
    setActiveApprovedButton(false);
    setActivePendingButton(true);
    setActiveUnclassifiedButton(false);
    setActiveManualClassify(false)
    const responseData = await tableAPICall(searchTerm, 'Pending');
    console.log("PENDING responseData", responseData)
    setTableLength(responseData[0].length + ' documents found')
    setDataTableBody(responseData[0]);
    setIsLoading(false)
  }

  // When the rejected pill is selected
  const rejectedQ = async () => {
    setSearchTerm('')
    setIsLoading(true)
    setDataTableBody([])
    setActiveApprovedButton(false);
    setActiveReviewButton(false);
    setActivePendingButton(false);
    setActiveAllButton(false);
    setActiveUnclassifiedButton(false);
    setActiveRejectedButton(true);
    setActiveManualClassify(false)
    const responseData = await tableAPICall(searchTerm, 'Rejected');
    console.log("REJECTED responseData", responseData)
    setTableLength(responseData[0].length + ' documents found')
    setDataTableBody(responseData[0]);
    setIsLoading(false)
  }

  // When the unclassified pill is selected
  const unclassifiedQ = async () => {
    setSearchTerm('')
    setIsLoading(true)
    setDataTableBody([])
    setActiveApprovedButton(false);
    setActiveReviewButton(false);
    setActivePendingButton(false);
    setActiveAllButton(false);
    setActiveRejectedButton(false);
    setActiveManualClassify(false)
    setActiveUnclassifiedButton(true);
    const responseData = await tableAPICall(searchTerm, 'unclassified');
    console.log("unclassified responseData", responseData)
    setTableLength(responseData[0].length + ' documents found')
    setDataTableBody(responseData[0]);
    setIsLoading(false)
  }

  // when manually classofied
  const manualClassifyQ = async () => {
    setSearchTerm('')
    setIsLoading(true)
    setDataTableBody([])
    setActiveApprovedButton(false);
    setActiveReviewButton(false);
    setActivePendingButton(false);
    setActiveAllButton(false);
    setActiveRejectedButton(false);
    setActiveUnclassifiedButton(false);
    setActiveManualClassify(true)
    const responseData = await tableAPICall(searchTerm, 'manualclassify');
    console.log("manual classify responseData", responseData)
    setTableLength(responseData[0].length + ' documents found')
    setDataTableBody(responseData[0]);
    setIsLoading(false)
  }

  // To set the table headers and body
  const tableAPICall = (searchTerms, status) => {
    return new Promise((resolve, reject) => {
      console.info(`searchTerms: ${searchTerms}`);
      console.info(`status: ${status}`);

      let sendObj = {
        term: searchTerms
      }

      //This call is for the AllQ as the API is different from other Queues
      if (status === 'all') {

        axios.get(`${baseURL}/hitl_service/v1/report_data`).then((statusAll) => {
          let apiData = statusAll.data.data;
          console.log("tableData Accepted", apiData);
          if (apiData.length === 0) {
            setTableLength(0 + ' documents found')
            setIsLoading(false);
          }

          formattingTableData(apiData).then((formattedResponse) => {
            console.log("TABLE BODY", formattedResponse)
            resolve([formattedResponse]);
          })

        }).catch(err => {
          setIsLoading(false);
          console.log("errorssssss", err.message);
          if (err.message === 'Request failed with status code 500') {
            toast.error('Error during fetching from Firestore')
          }

        })
      }
      //This call is for the UnclassifiedQ
      else if (status === 'unclassified') {

        axios.get(`${baseURL}/hitl_service/v1/get_unclassified`).then((statusUnclassified) => {
          let statusUnclassifiedTableBody = [];
          let apiData = statusUnclassified.data.data;
          console.log("tableData Accepted", apiData);
          if (apiData.length === 0) {
            setTableLength(0 + ' documents found')
            setIsLoading(false);
          }
          apiData.forEach((element) => {
            console.info("element", element);

            const tableBody = {
              "actions": (
                <div>
                  <a href={`${baseURL}/hitl_service/v1/fetch_file?case_id=${element.case_id}&uid=${element.uid}&download=true`} target={"_blank"} style={{ ...actionButtonStyles }}>
                    Download
                  </a>
                  {' | '}
                  <Link to={{
                    pathname: `/classify/${element.uid}/${element.case_id}`,
                    //  state: {
                    //    uid: `${element.uid}`,
                    //    caseid: `${element.case_id}`
                    //  }
                  }} style={{ textDecoration: 'none', fontSize: '14px' }}>Manually Classify</Link>

                </div>),

              "applicantname": `${element.applicant_name}`,
              "caseid": `${element.case_id}`,
              "current_status": `${element.current_status}`,
              'process_status': `${element.process_status}`,
              "statuslastupdate": `${element.status_last_updated_by}`,
              "document_display_name": `${element.document_display_name}`,
              "document_type": `${element.document_type}`,
              "extractionscore": `${element.extraction_score === null ? '-' : parseFloat(element.extraction_score * 100).toFixed(1) + '%'}`,
              "extractionstatus": `${element.extraction_status === null ? '-' : element.extraction_status}`,
              "matchscore": `${element.matching_score === null ? '-' : parseFloat(element.matching_score * 100).toFixed(1) + '%'}`,
              "classificationscore": `${element.classification_score === null ? '-' : parseFloat(element.classification_score * 100).toFixed(1) + '%'}`,
              "uploaddate": `${(element.upload_timestamp)}`,
              "last_update_timestamp": `${(element.last_update_timestamp)}`,
              "classifyhumansystem": `${element.is_hitl_classified === null ? '-' : element.is_hitl_classified}`,
              "uid": `${element.uid}`,
            }
            statusUnclassifiedTableBody.push(tableBody)
          })
          console.log("TABLE BODY", statusUnclassifiedTableBody);
          resolve([statusUnclassifiedTableBody]);
        }).catch((err) => {
          setIsLoading(false);
          console.log("errors", err);
          if (err.message === 'Request failed with status code 500') {
            toast.error('Error during fetching from Firestore')
          }

        })
      }
      //For Review/Pending/Rejected/Approved Queues
      else if (['Need Review', 'Pending', 'Rejected', 'Approved'].includes(status)) {
        axios.post(`${baseURL}/hitl_service/v1/get_queue?hitl_status=${status}`).then((hitlStatus) => {
          let apiData = hitlStatus.data.data;
          console.log("tableData Accepted", apiData);
          if (apiData.length === 0) {
            setTableLength(0 + ' documents found')
            setIsLoading(false);
          }
          else {
            formattingTableData(apiData).then((formattedData) => {
              console.log("Formatted DATA", formattedData);
              console.log("TABLE BODY", formattedData)
              resolve([formattedData]);
            })
          }
        }).catch((err) => {
          setIsLoading(false);
          if (err.message === 'Request failed with status code 500') {
            toast.error('Error during fetching from Firestore')
          }
          console.log("error", err);
        })
      }

      else if (status === 'manualclassify') {
        const sendObj = {
          "filter_key": 'is_hitl_classified',
          "filter_value": true
        }
        axios.post(`${baseURL}/hitl_service/v1/search`, sendObj).then((searchFilterText) => {
          let apiData = searchFilterText.data.data;
          if (apiData.length === 0) {
            setTableLength(0 + ' documents found')
            setIsLoading(false);
          }
          else {
            formattingTableData(apiData).then((formattedData) => {
              console.log("Formatted DATA", formattedData);
              setTableLength(formattedData.length + ' documents found')
              console.log("TABLE BODY", formattedData)
              resolve([formattedData]);
            })
          }
        }).catch(err => {
          setIsLoading(false);
          console.log("error in", err.message)
        })

      }
      // when the user search for any text in the searchbox
      else {
        console.log("sendObj", sendObj)
        axios.post(`${baseURL}/hitl_service/v1/search`, sendObj).then((searchFilterText) => {
          let apiData = searchFilterText.data.data;
          if (apiData.length === 0) {
            setTableLength(0 + ' documents found')
            setIsLoading(false);
          }
          else {
            formattingTableData(apiData).then((formattedData) => {
              console.log("Formatted DATA", formattedData);
              setTableLength(formattedData.length + ' documents found')
              console.log("TABLE BODY", formattedData)
              resolve([formattedData]);
            })
          }
        }).catch(err => {
          setIsLoading(false);
          console.log("error in", err.message)
        })

      }
    })

  }

  //Formatting the table body from the API response
  const formattingTableData = (apiTableResponse) => {
    const tableBodyArr = [];
    return new Promise((resolve, reject) => {
      apiTableResponse.forEach((element) => {
        const tableBody = {
          "actions": (
            <div>

              {element.document_class !== null ?
                <div>
                  <Link to={{
                    pathname: `/documentreview/${element.uid}/${element.case_id}`,
                    //  state: {
                    //    uid: `${element.uid}`,
                    //    caseid: `${element.case_id}`
                    //  }
                  }} style={{ ...actionButtonStyles }}>View</Link>

                  {' | '}

                  {/* {' | '}

                  <a href={`${baseURL}/hitl_service/v1/fetch_file?case_id=${element.case_id}&uid=${element.uid}&download=true`} target={"_blank"} style={{ ...actionButtonStyles }}>
                    Download
                  </a> */}

                  {/*{' | '}*/}

                  <Link to={{
                    pathname: `/classify/${element.uid}/${element.case_id}/${element.document_class}/${element.document_type}`,
                    //  state: {
                    //    uid: `${element.uid}`,
                    //    caseid: `${element.case_id}`
                    //  }
                  }} style={{ ...actionButtonStyles }}>Re-Classify</Link>
                </div>
                :
                <>
                  <Link to={{
                    pathname: `/classify/${element.uid}/${element.case_id}?document_class=${element.document_class}&document_type=${element.document_type}`,
                    //  state: {
                    //    uid: `${element.uid}`,
                    //    caseid: `${element.case_id}`
                    //  }
                  }} style={{ ...actionButtonStyles }}>Manually Classify</Link>

                </>
              }

            </div>),
          "applicantname": `${element.applicant_name}`,
          "caseid": `${element.case_id}`,
          "current_status": `${element.current_status}`,
          'process_status': `${element.process_status}`,
          "statuslastupdate": `${element.status_last_updated_by}`,
          "document_display_name": `${element.document_display_name}`,
          "document_type": `${element.document_type}`,
          "extractionscore": `${element.extraction_score === null ? '-' : parseFloat(element.extraction_score * 100).toFixed(1) + '%'}`,
          "extractionstatus": `${element.extraction_status === null ? '-' : element.extraction_status}`,
          "matchscore": `${element.matching_score === null ? '-' : parseFloat(element.matching_score * 100).toFixed(1) + '%'}`,
          "classificationscore": `${element.classification_score === null ? '-' : parseFloat(element.classification_score * 100).toFixed(1) + '%'}`,
          "uploaddate": `${(element.upload_timestamp)}`,
          "last_update_timestamp": `${(element.last_update_timestamp)}`,
          "classifyhumansystem": `${element.is_hitl_classified === null ? '-' : element.is_hitl_classified}`,
          "uid": `${element.uid}`,
          //navigations to other pages

        }
        tableBodyArr.push(tableBody)
        resolve(tableBodyArr)
      })
    })
  }

  const template1 = {
    layout: 'PrevPageLink PageLinks NextPageLink RowsPerPageDropdown CurrentPageReport',
    'PrevPageLink': (options) => {
      return (
        <button type="button" className={options.className} onClick={options.onClick} disabled={options.disabled}>
          <span className="p-3"> {'<'}</span>
          <Ripple />
        </button>
      )
    },
    'NextPageLink': (options) => {
      return (
        <button type="button" className={options.className} onClick={options.onClick} disabled={options.disabled}>
          <span className="p-3">{'>'}</span>
          <Ripple />
        </button>
      )
    },
    'PageLinks': (options) => {
      if ((options.view.startPage === options.page && options.view.startPage !== 0) || (options.view.endPage === options.page && options.page + 1 !== options.totalPages)) {
        const className = classNames(options.className, { 'p-disabled': true });

        return <span className={className} style={{ userSelect: 'none' }}>...</span>;
      }

      return (
        <button type="button" className={options.className} onClick={options.onClick}>
          {options.page + 1}
          <Ripple />
        </button>
      )
    },
  };

  const statusBodyTemplate = (rowData) => {
    const stockClassName = classNames({
      'approved': ['approved'].includes(rowData.current_status.toLowerCase()) ||  ['processed'].includes(rowData.current_status.toLowerCase()),
      'processed': ['processed'].includes(rowData.current_status.toLowerCase()),
      'inprogress': ['in progress', 'inprogress', 'progress', 'processing'].includes(rowData.current_status.toLowerCase()),
      'pending': ['pending', 'review', 'need review'].includes(rowData.current_status.toLowerCase()),
      'rejected': ['rejected'].includes(rowData.current_status.toLowerCase()),
      'failed': ['error', 'failed'].includes(rowData.current_status.toLowerCase()),
    });

    return (
      <div className={stockClassName}>
        {rowData.current_status}
      </div>
    );
  }

  const uploadTimestampBodyTemplate = (rowData) => {
    return <span>{moment.utc(rowData.uploaddate).local().format('YYYY-MM-DD HH:mm:ss')}</span>
  }

  const lastUpdateTimestampBodyTemplate = (rowData) => {
    return <span>{rowData.last_update_timestamp ? moment.utc(rowData.last_update_timestamp).local().format('YYYY-MM-DD HH:mm:ss') : '-'}</span>
  }

  const docclassBodyTemplate = (rowData) => {
    return <span>{rowData.document_display_name}</span>;
  }

  const doctypeBodyTemplate = (rowData) => {
    return <span>{rowData.document_type}</span>;
  }

  const manualClassifyBodyTemplate = (rowData) => {
    return <span className={`docCaptalize`}>{rowData.classifyhumansystem}</span>;
  }

  const extractionStatusBodyTemplate = (rowData) => {
    return <span className={`docCaptalize`}>{rowData.extractionstatus}</span>;
  }


  const onCustomPage1 = (event) => {
    setFirst1(event.first);
    setRows1(event.rows);
    setCurrentPage(event.page + 1);
  }


  return (
    <Container className="dataTableContainer">
      <Row>

      </Row>
      {/* <Row style={{padding:'30px'}}> */}
      <Row>
        <Col className="col-5">
          <label className="labels" style={{ fontSize: '14px', paddingLeft: '5px' }}>Search documents:</label>
          <br />
          <div>
            <input type="text" onChange={onFilter} className="searchInput" onKeyPress={enterKeyPressed} id='searchterm' value={searchTerm} name="searchterm" placeholder="Search by Document Class, Case ID, etc." />
            {'  '}
            <Button
              variant="secondary"
              className="buttonStyles"
              style={{
                backgroundColor: '#2196F3',
                color: 'white',

              }} onClick={buttonClicked}>
              Search
            </Button>

          </div>

        </Col>
        <Col>
          <label className="labels" style={{ fontSize: '14px', paddingLeft: '5px' }}>Filter document list by:</label>
          <br />
          <Button
            variant="secondary"
            onClick={allQ}
            className="buttonStyles"
            style={{
              backgroundColor: activeAllButton === true ? '#2196F3' : '#E9ECEF',
              color: activeAllButton === true ? 'white' : 'black',

            }}>
            All
          </Button>{' '}

          <Button
            variant="secondary"
            className="buttonStyles"
            onClick={reviewQ}
            style={{
              backgroundColor: activeReviewButton === true ? '#2196F3' : '#E9ECEF',
              color: activeReviewButton === true ? 'white' : 'black',
            }}>
            Need Review
          </Button>{' '}
          {/*
          <Button
            variant="secondary"
            className="buttonStyles"
            onClick={pendingQ}
            style={{
              backgroundColor: activePendingButton === true ? '#2196F3' : '#E9ECEF',
              color: activePendingButton === true ? 'white' : 'black',
            }}>
            Pending
          </Button>{' '} */}

          <Button
            variant="secondary"
            onClick={approvedQ}
            className="buttonStyles"
            style={{
              backgroundColor: activeApprovedButton === true ? '#2196F3' : '#E9ECEF',
              color: activeApprovedButton === true ? 'white' : 'black',
            }}>
            Approved
          </Button>{' '}

          <Button
            variant="secondary"
            onClick={rejectedQ}
            className="buttonStyles"
            style={{
              backgroundColor: activeRejectedButton === true ? '#2196F3' : '#E9ECEF',
              color: activeRejectedButton === true ? 'white' : 'black',

            }}>
            Rejected
          </Button>{' '}

          <Button
            variant="secondary"
            onClick={unclassifiedQ}
            className="buttonStyles"
            style={{
              backgroundColor: activeUnclassifiedButton === true ? '#2196F3' : '#E9ECEF',
              color: activeUnclassifiedButton === true ? 'white' : 'black',
            }}>
            Unclassified
          </Button>

          <Button
            variant="secondary"
            onClick={manualClassifyQ}
            className="buttonStyles"
            style={{
              backgroundColor: activeManualClassifyButton === true ? '#2196F3' : '#E9ECEF',
              color: activeManualClassifyButton === true ? 'white' : 'black',
            }}>
            Manually Classified
          </Button>

          <BsArrowRepeat style={{ ...refreshButtonStyles, color: '#2196F3' }} onClick={tableRefresh} /> {' '}

        </Col>
      </Row>
      {/* <Row style={{padding:'0px 30px 10px 30px'}}> */}
      <Row>
        <Col>
          {/**Comman Table for all the Queues, based on the selected Queue data will change */}

          {isLoading ? <Spinner animation="border" variant="primary" /> :
            <div className="datatable-style-demo ">
              <DataTable value={dataTableBody} sortMode="multiple" header={tableLength} size="small" responsiveLayout="scroll"
                paginator paginatorTemplate={template1} first={first1} rows={rows1} onPage={onCustomPage1} paginatorPosition="both" paginatorClassName="justify-content-end"
              >
                {/* <Column field="uid" header="Document ID" body={documentIdBodyTemplate} sortable></Column> */}
                <Column field="actions" header="Actions"></Column>
                {/*<Column field="applicantname" header="Applicant Name" sortable></Column>*/}
                <Column field="documenttype" header="Document Class" body={docclassBodyTemplate} sortable></Column>
                <Column field="documentclass" header="Document Type" body={doctypeBodyTemplate} sortable></Column>
                <Column field="current_status" header="Status" body={statusBodyTemplate} sortable></Column>
                <Column field="process_status" header="Process Detail" sortable></Column>
                <Column field="caseid" header="Case ID" sortable></Column>
                <Column field="last_update_timestamp" header="Last Modified" body={lastUpdateTimestampBodyTemplate} sortable></Column>
                <Column field="statuslastupdate" header="Last Updated By" sortable></Column>
                <Column field="extractionscore" header="Extraction" sortable></Column>
                {/*<Column field="extractionstatus" header="Extraction Status" body={extractionStatusBodyTemplate}></Column>*/}
                <Column field="classificationscore" header="Classification" sortable></Column>
                <Column field="uploaddate" header="Upload Date" body={uploadTimestampBodyTemplate} sortable></Column>
                <Column field="classifyhumansystem" header="Manual Classification" body={manualClassifyBodyTemplate}></Column>


              </DataTable>

            </div>
          }

        </Col>
      </Row>

    </Container>


  )

}

export default DataTables;


const actionButtonStyles = {
  textDecoration: 'none',
  fontSize: '14px'
}

const refreshButtonStyles = { fontSize: '28px', color: 'blue', marginLeft: '1.5rem', cursor: 'pointer' }