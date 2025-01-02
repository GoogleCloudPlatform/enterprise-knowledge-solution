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

/*** This page is to upload a document either a single upload or the bulk upload. There are 2 ways to assign
 * Case ID for a user:
 * a) Manually enter the app registeration id in the field
 * b) Else select from the table results by clicking on the search applicant button
 */


/* eslint-disable no-undef */
/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from 'react';
import { Container, Button, Row, Col, Spinner, FloatingLabel, Form, Card } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import axios from 'axios';
import { useHistory, Link } from 'react-router-dom'
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { baseURL } from '../configs/firebase.config'
import DragDropUpload from './DragDropUpload';
import Headers from './Headers';
import options from '../configs/Program';
import { ReactComponent as Back } from '../images/arrow-back.svg';
import '../App.css';
import '../css/Upload.css';


function Upload() {
	const history = useHistory();
	//Set the states
	const [tableComponent, setTableComponent] = useState(false);
	const [selectedCaseId, setSelectedCaseId] = useState();
	const [stateValue, setStateValue] = useState({ state: 'california' });
	const [comments, setComment] = useState('');
	const [fileUploadSpinner, setFileUploadSpinner] = useState(false);
	const [searchFlag, setSearchFlag] = useState(false);
	const [inputFlag, setInputFlag] = useState(false);


	// To submit the data to the API
	const fileRetrieve = (filesdata) => {
		setFileUploadSpinner(true)
		let data = new FormData()

		console.log("filesdata", filesdata);
		const fileObj = filesdata.map((i) => {
			return i.file
		})
		console.log("fileOBJ", fileObj)
		filesdata.forEach((ele) => {
			console.log("ele", ele.file);
			data.append('files', ele.file);
		})
		if (stateValue.state === '') {
			toast.error('Please Choose State', {
				position: "bottom-center",
				autoClose: 5000,
				hideProgressBar: true,
				closeOnClick: true,
				pauseOnHover: false,
				draggable: true,
				progress: undefined,
			})
			setFileUploadSpinner(false);
		}
		else {

			console.log("state value", stateValue);
			console.log("comments", comments)
			let caseids = '';
			// As a user as 2 options to give the caseid, either by entering which sets the state in selectedCaseId or else by clicking on the displayed row which is stored in selectedcaseid.caseid
			if (selectedCaseId !== undefined && selectedCaseId.hasOwnProperty('caseid')) {
				console.log("1")
				caseids = selectedCaseId['caseid']
			}
			else if (selectedCaseId !== undefined) {
				console.log("2")
				caseids = selectedCaseId
			}
			else {
				console.log("3")
				caseids = selectedCaseId
			}

			console.log("CASEID", caseids, typeof (caseids))

			// There are 2 calls for the upload API, one when the caseid is not given automatically the backend will generate a 36 character string
			if (selectedCaseId === undefined) {
				axios.post(`${baseURL}/upload_service/v1/upload_files?context=${stateValue.state}&comment=${comments}&user=${localStorage.getItem('user').split('@')[0]}`, data, {
					headers: {
						'Accept': 'application/json',
						'Content-Type': 'multipart/form-data'
					},
				}).then((responseData) => {
					console.log("response data");
					filesdata.forEach(f => f.remove())
					setStateValue({ state: '' });
					setSelectedCaseId();
					setComment([]);
					toast.success("File Uploaded Successfully !", {
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
			}
			// else the manually entered or the selected row caseid is given
			else {

				axios.post(`${baseURL}/upload_service/v1/upload_files?context=${stateValue.state}&case_id=${caseids}&comment=${comments}`, data, {
					headers: {
						'Accept': 'application/json',
						'Content-Type': 'multipart/form-data'
					},
				}).then((responseData) => {
					console.log("response data");
					filesdata.forEach(f => f.remove())
					setStateValue({ state: '' });
					setSelectedCaseId();
					setComment([]);
					setFileUploadSpinner(false);
					toast.success("File Uploaded Successfully !", {
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
					console.log("error", err.message);
					setFileUploadSpinner(false);
					if (err.message === 'Request failed with status code 422') {
						toast.error(`Please upload pdf files only`, {
							position: "bottom-center",
							autoClose: 5000,
							hideProgressBar: false,
							closeOnClick: true,
							pauseOnHover: true,
							draggable: true,
							progress: undefined,
						});
					}


				})
			}
		}
	}

	// when the user types the text this function is invoked to set the caseid
	const inputValueChanges = (e) => {
		console.log("e.target.value", e.target.value.length);
		setInputFlag(true);
		setSelectedCaseId();
		if (e.target.value.length === 0) {
			setSelectedCaseId();
		}
		else {
			setSelectedCaseId(e.target.value)
		}
	}

	// The child component gets the data of selected row caseid when the user is selected from the search applicant page
	const handleTableData = (searchTableDetails) => {
		setInputFlag(false);
		setSearchFlag(true)
		console.log("cleared", searchTableDetails);
		if (searchTableDetails === undefined) {
			setSelectedCaseId()
		}
		else {
			setSelectedCaseId(searchTableDetails)
		}
	}
	useEffect(() => {
		setTableComponent(true);
	})

	// To select the state from the dropdown
	const stateChange = (e) => {
		console.log("state value changed", e.target.value)
		setStateValue({ state: e.target.value })
	}
	return (
		<div>
			<Headers />
			<div className="subHeaderUpload">
				<Link to={{ pathname: '/', }} className="drBack">
					<Back fill="#aaa" />
				</Link>{' '}
				<label className={["raLabels", "raSpace"].join(" ")}> Upload a Document</label>
			</div>
			<Container className="uploadContainer">
				<Card style={{ borderRadius: '1.25rem' }}>
					<Card.Body>
						<Card.Text as='div'>
							<Row className='customRow'>
								<DragDropUpload className="dragdropuploadclass" onFileChange={fileRetrieve} />
								{fileUploadSpinner ? <Spinner animation="border" variant="primary" /> : ''}
							</Row>
						</Card.Text>
					</Card.Body>
				</Card>

				<br />

			</Container>
		</div>


	)

};

export default Upload;


const textInputsStyles = {
	width: '100%',
	borderRadius: '16px',
	fontSize: '12px'
}

const labelsStyles = {
	fontWeight: 'bolder',
	fontSize: '12px'
}
