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

/*** This is the common file for both Upload.js and Reassign.js files. Where a user can search for
 * an applicant to assign an registration id in upload and reasssign.js files. A user has to select a row
 * then the associated caseid is tagged to that application
*/

import { Button, Card } from 'react-bootstrap';
import React, { useState } from 'react';
import axios from 'axios';
import { baseURL } from '../configs/firebase.config';
import { Ripple } from 'primereact/ripple';
import {
	Link
} from 'react-router-dom';
import { classNames } from 'primereact/utils';
import { DataTable } from 'primereact/datatable';
import moment from 'moment';
import { Column } from 'primereact/column';
import 'primeicons/primeicons.css';
import 'primereact/resources/themes/lara-light-indigo/theme.css';
import 'primereact/resources/primereact.css';
import 'primeflex/primeflex.css';
import '../css/SearchApplicant.css'



function SearchForApplicantTable(props) {
	console.log("PROPS PASSED IN REASSIGN", props)

	const [dataTableBody, setDataTableBody] = useState([]);
	const [isLoading, setIsLoading] = useState(false);
	const [filter, setFilter] = useState('');
	const [tableLength, setTableLength] = useState('0 documents found');
	const [searchTerm, setSearchTerm] = useState('')
	const [currentPage, setCurrentPage] = useState(1);
	const [selectedProduct1, setSelectedProduct1] = useState(null);
	const [first1, setFirst1] = useState(0);
	const [rows1, setRows1] = useState(20);


	// To se the table data on page onload
	const tableAPICall = (searchTerms, status) => {
		return new Promise((resolve, reject) => {
			console.log("^^^^^^^^^^^^^", searchTerms, status);
			let sendObj = {
				term: searchTerms
			}

			//This call is for the AllQ as the API is different from other Queues
			if (status === 'all') {

				axios.get(`${baseURL}/hitl_service/v1/report_data`).then((statusAll) => {
					let apiData = statusAll.data.data;
					console.log("tableData Accepted", apiData);

					if (props.page === 'reaasignpage') {
						let supportingDocRecords = apiData
						var index = supportingDocRecords.filter(function (o) {
							return o.document_type === 'application_form';
						})
						formattingTableData(index).then((formattedResponse) => {
							console.log("TABLE BODY", formattedResponse)
							setTableLength(formattedResponse.length + ' documents found')
							setDataTableBody(formattedResponse)
							setIsLoading(false);
						})

					}
					else if (props.page === 'uploadpage') {
						formattingTableData(apiData).then((formattedResponse) => {
							console.log("TABLE BODY", formattedResponse)
							setTableLength(formattedResponse.length + ' documents found')
							setDataTableBody(formattedResponse)
							setIsLoading(false);
						})
					}



				}).catch(err => {
					setIsLoading(false);
					console.log("errorssssss", err, err.message);

				})
			}

			else {
				console.log("sendObj", sendObj)
				axios.post(`${baseURL}/hitl_service/v1/search`, sendObj).then((searchFilterText) => {
					let apiData = searchFilterText.data.data;
					if (apiData.length === 0) {
						setIsLoading(false);
					}
					else {
						if (props.page === 'reaasignpage') {
							let supportingDocRecords = apiData
							var index = supportingDocRecords.filter(function (o) {
								return o.document_type === 'application_form';
							})
							formattingTableData(index).then((formattedData) => {
								console.log("Formatted DATA", formattedData);
								console.log("TABLE BODY", formattedData)
								setTableLength(formattedData.length + ' documents found')
								setDataTableBody(formattedData);
								setIsLoading(false);
							})
						}
						else if (props.page === 'uploadpage') {
							formattingTableData(apiData).then((formattedData) => {
								console.log("Formatted DATA", formattedData);
								console.log("TABLE BODY", formattedData)
								setTableLength(formattedData.length + ' documents found')
								setDataTableBody(formattedData);
								setIsLoading(false);
							})
						}
					}
				}).catch(error => {
					setIsLoading(false);
					console.log("error in", error)
				})

			}
		})
	}

	// when a row is selected, the associated id is sent to the parent component
	function handleTableData(e) {
		setSelectedProduct1(e.value)
		props.onSelectTableData(e.value);
	}

	const buttonClicked = () => {
		setIsLoading(true)
		console.log("Searching...", searchTerm)
		if (searchTerm) {
			console.log("SEARCH TERM", searchTerm);
			setDataTableBody([])
			tableAPICall(searchTerm)
			// tableAPICall(searchTerm,'all').then((responseData) => {
			//  console.log("Search term response", responseData)
			//  setTableLength(responseData[0].length + ' documents found');
			//  setIsLoading(false)
			//  setDataTableBody(responseData[0]);
			//   })
		}
		else {
			tableAPICall(searchTerm, 'all');
		}
	}

	// This function is to format all the data that needs to be displayed in the UI in the form of table
	const formattingTableData = (apiTableResponse) => {
		const tableBodyArr = [];
		return new Promise((resolve, reject) => {
			apiTableResponse.forEach((element) => {
				const tableBody = {
					"caseid": `${element.case_id}`,
					"documenttype": `${element.document_type === null ? 'N/A' : (element.document_type).split('_').join(" ")}`,
					"documentclass": `${element.document_class === null ? 'N/A' : (element.document_class).split('_').join(" ")}`,
					"uploaddate": `${(element.upload_timestamp)}`,
					"applicantname": `${element.applicant_name}`,
					"matchscore": `${element.matching_score === null ? 'N/A' : parseFloat(element.matching_score * 100).toFixed(1) + '%'}`,
					"extractionscore": `${element.extraction_score === null ? 'N/A' : parseFloat(element.extraction_score * 100).toFixed(1) + '%'}`,
					"validationscore": `${element.validation_score === null ? 'N/A' : parseFloat(element.validation_score * 100).toFixed(1) + '%'}`,
					'process_status': `${element.process_status}`,
					"current_status": `${element.current_status}`,
					"statuslastupdate": `${element.status_last_updated_by}`,

					"uid": `${element.uid}`,
					//navigations to other pages
					"actions": (
						<Link to={{
							pathname: `/documentreview/${element.uid}/${element.case_id}`,
						}} className="saActionButton">Review</Link>

					)
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
			'approved': rowData.current_status === 'Approved' || rowData.current_status === 'approved' || rowData.current_status === 'Processed' || rowData.current_status === 'processed',
			'processed':  rowData.current_status === 'Processed' || rowData.current_status === 'processed',
			'rejected': rowData.current_status === 'Rejected' || rowData.current_status === 'rejected' || rowData.current_status === 'Failed',
			'pending': rowData.current_status === 'Pending' || rowData.current_status === 'pending' || rowData.current_status === 'In Progress' || rowData.current_status === 'Review' || rowData.current_status === 'review',
		});

		console.log("current_status", rowData.current_status)
		console.log("stockClassName", stockClassName)
		return (
			<div className={stockClassName}>
				{rowData.current_status}
			</div>
		);
	}

	const dateBodyTemplate = (rowData) => {
		return <span>{moment.utc(rowData.uploaddate).local().format('YYYY-MM-DD HH:mm:ss')}</span>
	}


	const doctypeBodyTemplate = (rowData) => {
		return <span className={`docCaptalize`}>{rowData.documenttype}</span>;
	}
	const docclassBodyTemplate = (rowData) => {
		return <span className={`docCaptalize`}>{rowData.documentclass}</span>;
	}

	const onCustomPage1 = (event) => {
		setFirst1(event.first);
		setRows1(event.rows);
		setCurrentPage(event.page + 1);
	}

	const onFilter = (e) => {
		console.log("text", e.target.value)
		setFilter(e.target.value);
		setSearchTerm(e.target.value)
	};

	const onRowSelect = (event) => {
		console.log("onRowSelect", event)
		props.onSelectTableData(event.data);

	}

	const onRowUnselect = (event) => {
		console.log("onRowUnselect", event)
	}

	const enterKeyPressed = (e) => {
		console.log("Enter key pressed")
		var code = e.keyCode || e.which;
		if (code === 13) {
			buttonClicked()
		}

	}



	return (
		<div>

			<input type="text" onChange={onFilter} onKeyPress={enterKeyPressed} value={searchTerm} id='searchterm' name="searchterm" style={{ borderRadius: '13px', padding: '5px 15px', width: '300px' }} placeholder="Search for Applicants" />{'  '}
			{isLoading ? <Button
				variant="secondary"
				className="searchInputButton"
				style={{
					backgroundColor: '#2196F3',
					color: 'white',

				}}>
				Searching...
			</Button> : <Button
				variant="secondary"
				className="searchInputButton"
				style={{
					backgroundColor: '#2196F3',
					color: 'white',

				}} onClick={buttonClicked}>
				Search
			</Button>}
			{dataTableBody.length === 0 ? '' : TableDisplay()}

		</div>
	)


	function TableDisplay() {
		return (
			<div className="saContainer">
				<div className="datatable-style-demo ">
					<label></label>
					<DataTable value={dataTableBody} sortMode="multiple" header={tableLength} size="small" responsiveLayout="scroll" paginator paginatorTemplate={template1} first={first1} rows={rows1} onPage={onCustomPage1} selectionMode="single" selection={selectedProduct1} onSelectionChange={e => handleTableData(e)} onRowSelect={onRowSelect} onRowUnselect={onRowUnselect} paginatorPosition="both" paginatorClassName="justify-content-end">
						{/* <DataTable value={dataTableBody} selection={selectedproducts} onSelectionChange={e => setSelectedProducts(e.value)} dataKey="id" responsiveLayout="scroll"> */}
						<Column selectionMode="single" headerStyle={{ width: '3em' }}></Column>
						{/*<Column field="applicantname" header="Applicant Name" sortable></Column>*/}
						<Column field="caseid" header="App Reg ID" sortable></Column>
						<Column field="current_status" header="Approval Status" body={statusBodyTemplate} sortable></Column>
						<Column field="process_status" header="Doc Processing Status" sortable></Column>
						<Column field="statuslastupdate" header="Updated By" sortable></Column>
						<Column field="documenttype" header="Document Type" body={doctypeBodyTemplate} sortable></Column>
						<Column field="documentclass" header="Document Class" body={docclassBodyTemplate} sortable></Column>
						<Column field="uploaddate" header="Upload Date" body={dateBodyTemplate} sortable></Column>
						<Column field="extractionscore" header="Extraction" sortable></Column>
						<Column field="matchscore" header="Matching" sortable></Column>
						<Column field="validationscore" header="Validation Score" sortable></Column>
						<Column field="actions" header="Actions"></Column>

					</DataTable>
				</div>
			</div>
		)
	}

}



export default SearchForApplicantTable

