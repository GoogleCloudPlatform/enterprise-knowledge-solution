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

/** This page is redirected when the user loggedin successfully. This page comprises of 2 parts
 * a) Charts: Where we can display the count of pending,approved and rejected forms
 * b) Table data: Where it shows the details of the forms and based on the forms we can perform actions on it
 */

/* eslint-disable eqeqeq */
/* eslint-disable react/jsx-no-target-blank */
import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
} from 'chart.js';
import { Container, Button } from 'react-bootstrap';
import Headers from './Headers';
import 'react-toastify/dist/ReactToastify.css';
import moment from 'moment';
import { toast } from "react-toastify";
import {
  useHistory
} from 'react-router-dom';
import axios from 'axios';
import { baseURL } from '../configs/firebase.config'
import '../App.css'
import '../css/Dashboard.css'
import DataTables from './DataTables';
import ErrorComponent from './ErrorComponent';


function Dashboard() {
  const [chart, setChart] = useState([])
  const [isChartLoading, setIsChartLoading] = useState(false);
  const [approvedChartTrends, setApprovedChartTrends] = useState([]);
  const [rejectedChartTrends, setRejectedChartTrends] = useState([]);
  const [pendingChartTrends, setPendingChartTrends] = useState([]);
  const [unclassifiedChartTrends, setUnclassifiedChartTrends] = useState([]);

  const [rejectedLabel, setRejectedLabel] = useState('')
  const [pendingLabel, setPendingLabel] = useState('')
  const [approvedLabel, setApprovedLabel] = useState('')
  const [unclassifiedLabel, setUnclassifiedLabel] = useState('')

  const history = useHistory();

  let approvedTimeCount = 0
  let rejectedTimeCount = 0
  let pendingTimeCount = 0;
  let unclassfiedTimeCount = 0;

  let approvedTimeCountTrends = 0
  let rejectedTimeCountTrends = 0
  let pendingTimeCountTrends = 0;
  let unclassifiedTimeCountTrends = 0;

  let overallApprovedTimeCountTrends = 0
  let overallRejectedTimeCountTrends = 0
  let overallPendingTimeCountTrends = 0
  let overallUnclassifiedTimeCountTrends = 0

  let statusApproved = 'Approved';
  let statusRejected = 'Rejected';
  let statusPending = 'Pending';
  let statusReview = 'Need Review';

  let rejectedArr = [];
  let approvedArr = [];
  let pendingArr = [];
  let unclassifiedArr = [];

  const [dateArr, setDateArr] = useState([]);

  const forEachDataApproved = (approvedDataa, yesterdayDate) => {

    approvedDataa.forEach((ele) => {
      const eleTimeStamp = ele['upload_timestamp'].split(" ")[0];
      const systemTimestamp = ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0];

      //console.log("i,approvedData", ele, approvedDataa.length);

      if (ele.hitl_status === null && eleTimeStamp === yesterdayDate) {
        // console.log("AUTO APPROVAL IF HITL STATUS NULL", ele['upload_timestamp']);
        approvedTimeCount++

      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].status === 'reassigned' && systemTimestamp === yesterdayDate) {
        //console.log("HITL LAST ELE REASSIGNED.CHECK FOR SYSTEM STATUS TMESTAMP", ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0])
        approvedTimeCount++
      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].timestamp.split(" ")[0] === yesterdayDate) {
        // console.log("HITL LAST ELEMENT", ele.hitl_status[ele.hitl_status.length - 1].timestamp)
        approvedTimeCount++
      }
      else {
        //console.log("NOT SATISFY ABOVE CONDITIONS");
      }
    })
  }

  const forEachDataRejected = (rejectedDataa, yesterdayDate) => {

    rejectedDataa.forEach((ele) => {
      const eleTimeStamp = ele['upload_timestamp'].split(" ")[0];
      const systemTimestamp = ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0];

      //console.log("i,approvedData", ele, rejectedDataa.length);

      if (ele.hitl_status === null && eleTimeStamp === yesterdayDate) {
        // console.log("AUTO APPROVAL IF HITL STATUS NULL", ele['upload_timestamp']);
        rejectedTimeCount++

      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].status === 'reassigned' && systemTimestamp === yesterdayDate) {
        //console.log("HITL LAST ELE REASSIGNED.CHECK FOR SYSTEM STATUS TMESTAMP", ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0])
        rejectedTimeCount++
      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].timestamp.split(" ")[0] === yesterdayDate) {
        //  console.log("HITL LAST ELEMENT", ele.hitl_status[ele.hitl_status.length - 1].timestamp)
        rejectedTimeCount++
      }
      else {
        // console.log("NOT SATISFY ABOVE CONDITIONS");
      }
    })
  }


  const forEachDataPending = (pendingDataa, yesterdayDate) => {

    pendingDataa.forEach((ele, i) => {

      const eleTimeStamp = ele['upload_timestamp'].split(" ")[0];
      const systemTimestamp = ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0];

      //console.log("i,approvedData", ele, pendingDataa.length);

      if (ele.hitl_status === null && eleTimeStamp === yesterdayDate) {
        //console.log("AUTO APPROVAL IF HITL STATUS NULL", ele['upload_timestamp']);
        pendingTimeCount++

      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].status === 'reassigned' && systemTimestamp === yesterdayDate) {
        //console.log("HITL LAST ELE REASSIGNED.CHECK FOR SYSTEM STATUS TMESTAMP", ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0])
        pendingTimeCount++
      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].timestamp.split(" ")[0] === yesterdayDate) {
        //console.log("HITL LAST ELEMENT", ele.hitl_status[ele.hitl_status.length - 1].timestamp)
        pendingTimeCount++
      }
      else {
        //console.log("NOT SATISFY ABOVE CONDITIONS");
      }
    })
  }

  const forEachDataUnclassified = (unclassifiedDataa, yesterdayDate) => {

    unclassifiedDataa.forEach((ele, i) => {

      const eleTimeStamp = ele['upload_timestamp'].split(" ")[0];
      const systemTimestamp = ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0];

      //console.log("i,approvedData", ele, unclassifiedDataa.length);

      if (ele.hitl_status === null && eleTimeStamp === yesterdayDate) {
        //console.log("AUTO APPROVAL IF HITL STATUS NULL", ele['upload_timestamp']);
        unclassfiedTimeCount++

      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].status === 'reassigned' && systemTimestamp === yesterdayDate) {
        //console.log("HITL LAST ELE REASSIGNED.CHECK FOR SYSTEM STATUS TMESTAMP", ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0])
        unclassfiedTimeCount++
      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].timestamp.split(" ")[0] === yesterdayDate) {
        //console.log("HITL LAST ELEMENT", ele.hitl_status[ele.hitl_status.length - 1].timestamp)
        unclassfiedTimeCount++
      }
      else {
        //console.log("NOT SATISFY ABOVE CONDITIONS");
      }
    })
  }

  const forEachDataRejectedTrends = (rejectedDataa, yesterdayDate) => {
    rejectedTimeCountTrends = 0;

    rejectedDataa.forEach((ele, i) => {
      const eleTimeStamp = ele['upload_timestamp'].split(" ")[0];
      const systemTimestamp = ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0];

      console.log("i,approvedData", ele, rejectedDataa.length);

      if (ele.hitl_status === null && eleTimeStamp === yesterdayDate) {
        console.log("AUTO APPROVAL IF HITL STATUS NULL", ele['upload_timestamp']);
        overallRejectedTimeCountTrends++
        rejectedTimeCountTrends++

      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].status === 'reassigned' && systemTimestamp === yesterdayDate) {
        console.log("HITL LAST ELE REASSIGNED.CHECK FOR SYSTEM STATUS TMESTAMP", ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0])
        overallRejectedTimeCountTrends++
        rejectedTimeCountTrends++
      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].timestamp.split(" ")[0] === yesterdayDate) {
        console.log("HITL LAST ELEMENT", ele.hitl_status[ele.hitl_status.length - 1].timestamp)
        overallRejectedTimeCountTrends++
        rejectedTimeCountTrends++
      }
      else {
        console.log("NOT SATISFY ABOVE CONDITIONS");
      }

      if (rejectedDataa.length - 1 === i) {
        rejectedArr.push(rejectedTimeCountTrends);
      }
    })
  }

  const forEachDataApprovedTrends = (approvedDataa, yesterdayDate) => {
    approvedTimeCountTrends = 0;
    console.log("APPROVED DATAAAAAAAAAAAA", approvedDataa.length)



    approvedDataa.forEach((ele, i) => {
      const eleTimeStamp = ele['upload_timestamp'].split(" ")[0];
      const systemTimestamp = ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0];

      console.log("i,approvedData", ele, approvedDataa.length);

      if (ele.hitl_status === null && eleTimeStamp === yesterdayDate) {
        console.log("AUTO APPROVAL IF HITL STATUS NULL", ele['upload_timestamp']);
        overallApprovedTimeCountTrends++
        approvedTimeCountTrends++

      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].status === 'reassigned' && systemTimestamp === yesterdayDate) {
        console.log("HITL LAST ELE REASSIGNED.CHECK FOR SYSTEM STATUS TMESTAMP", ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0])
        overallApprovedTimeCountTrends++
        approvedTimeCountTrends++
      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].timestamp.split(" ")[0] === yesterdayDate) {
        console.log("HITL LAST ELEMENT", ele.hitl_status[ele.hitl_status.length - 1].timestamp)
        overallApprovedTimeCountTrends++
        approvedTimeCountTrends++
      }
      else {
        console.log("NOT SATISFY ABOVE CONDITIONS");
      }

      if (approvedDataa.length - 1 === i) {
        approvedArr.push(approvedTimeCountTrends);
      }
    })
  }

  const forEachDataPendingTrends = (pendingDataa, yesterdayDate) => {
    pendingTimeCountTrends = 0;
    console.log("PENDING DATA", pendingDataa.length)
    if (pendingDataa.length === 0) {
      pendingArr.push(pendingTimeCountTrends);
    }

    pendingDataa.forEach((ele, i) => {
      const eleTimeStamp = ele['upload_timestamp'].split(" ")[0];
      const systemTimestamp = ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0];

      console.log("i,approvedData", ele, pendingDataa.length);

      if (ele.hitl_status === null && eleTimeStamp === yesterdayDate) {
        console.log("AUTO APPROVAL IF HITL STATUS NULL", ele['upload_timestamp']);
        overallPendingTimeCountTrends++
        pendingTimeCountTrends++

      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].status === 'reassigned' && systemTimestamp === yesterdayDate) {
        console.log("HITL LAST ELE REASSIGNED.CHECK FOR SYSTEM STATUS TMESTAMP", ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0])
        overallPendingTimeCountTrends++
        pendingTimeCountTrends++
      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].timestamp.split(" ")[0] === yesterdayDate) {
        console.log("HITL LAST ELEMENT", ele.hitl_status[ele.hitl_status.length - 1].timestamp)
        overallPendingTimeCountTrends++
        pendingTimeCountTrends++
      }
      else {
        console.log("NOT SATISFY ABOVE CONDITIONS");
      }

      if (pendingDataa.length - 1 === i) {
        pendingArr.push(pendingTimeCountTrends);
      }
    })
  }

  const forEachDataUnclassifiedTrends = (unclassifiedDataa, yesterdayDate) => {
    unclassifiedTimeCountTrends = 0;

    if (unclassifiedDataa.length === 0) {
      unclassifiedArr.push(unclassifiedTimeCountTrends);
    }

    unclassifiedDataa.forEach((ele, i) => {
      const eleTimeStamp = ele['upload_timestamp'].split(" ")[0];
      const systemTimestamp = ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0];

      console.log("i,approvedData", ele, unclassifiedDataa.length);

      if (ele.hitl_status === null && eleTimeStamp === yesterdayDate) {
        console.log("AUTO APPROVAL IF HITL STATUS NULL", ele['upload_timestamp']);
        overallUnclassifiedTimeCountTrends++
        unclassifiedTimeCountTrends++

      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].status === 'reassigned' && systemTimestamp === yesterdayDate) {
        console.log("HITL LAST ELE REASSIGNED.CHECK FOR SYSTEM STATUS TMESTAMP", ele.system_status[ele.system_status.length - 1].timestamp.split(" ")[0])
        overallUnclassifiedTimeCountTrends++
        unclassifiedTimeCountTrends++
      }
      else if (ele.hitl_status !== null && ele.hitl_status[ele.hitl_status.length - 1].timestamp.split(" ")[0] === yesterdayDate) {
        console.log("HITL LAST ELEMENT", ele.hitl_status[ele.hitl_status.length - 1].timestamp)
        overallUnclassifiedTimeCountTrends++
        unclassifiedTimeCountTrends++
      }
      else {
        console.log("NOT SATISFY ABOVE CONDITIONS");
      }

      if (unclassifiedDataa.length - 1 === i) {
        unclassifiedArr.push(unclassifiedTimeCountTrends);
      }
    })
  }

  //sample dataset for charts
  ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title);
  useEffect(() => {
    setIsChartLoading(true);
    axios.post(`${baseURL}/hitl_service/v1/get_queue?hitl_status=${statusPending}`).then((pendingData) => {
      console.log("API Data pending", pendingData.data.data.length)
      axios.post(`${baseURL}/hitl_service/v1/get_queue?hitl_status=${statusRejected}`).then((rejectedData) => {
        console.log("API Data rejected", rejectedData.data.data);
        axios.post(`${baseURL}/hitl_service/v1/get_queue?hitl_status=${statusApproved}`).then((approvedData) => {
          console.log("API Data approved", approvedData.data.data.length);

          axios.get(`${baseURL}/hitl_service/v1/get_unclassified`).then((unclassifiedData) => {
            console.log("API Unclassified Data", unclassifiedData.data.data.length)

            console.log("DATEEE", moment().subtract(5, 'days').toISOString().split("T")[0])
            const yesterdayDate = moment().subtract(1, 'days').toISOString().split("T")[0];
            //const yesterdayDate =moment().toISOString().split("T")[0]
            console.log("YESTERDAY", yesterdayDate);

            let lastDate = moment().subtract(7, "days").format("YYYY-MM-DD");
            //let todayDate = moment().toISOString().split("T")[0];
            console.log("CUSTOME DATESSSS", lastDate, yesterdayDate);
            let dateArrs = enumerateDaysBetweenDates(yesterdayDate, lastDate);
            setDateArr(dateArrs);
            console.log("DATE ARR", dateArr);


            let approvedDataa = approvedData.data.data;
            forEachDataApproved(approvedDataa, yesterdayDate)
            console.log("APPROVED TIME COUNT", approvedTimeCount)

            let rejectedDataa = rejectedData.data.data;
            forEachDataRejected(rejectedDataa, yesterdayDate)
            console.log("Rejected TIME COUNT", rejectedTimeCount)

            let pendingDataa = pendingData.data.data;
            forEachDataPending(pendingDataa, yesterdayDate)
            console.log("Pending TIME COUNT", pendingTimeCount)

            let unclassifiedDataa = unclassifiedData.data.data;
            forEachDataUnclassified(unclassifiedDataa, yesterdayDate)
            console.log("unclassifiedDataa TIME COUNT", unclassfiedTimeCount)


            dateArrs.forEach((element) => {
              // console.log("ELEMENT",element)
              forEachDataRejectedTrends(rejectedDataa, element)
              console.log("Rejected TRENDS", rejectedArr)
              setRejectedChartTrends(rejectedArr)
            })

            dateArrs.forEach((element) => {
              //console.log("ELEMENT",element)
              forEachDataApprovedTrends(approvedDataa, element)
              console.log("Approved TRENDS", approvedArr)
              setApprovedChartTrends(approvedArr)
            })

            dateArrs.forEach((element) => {
              //console.log("ELEMENT",element)
              forEachDataPendingTrends(pendingDataa, element)
              console.log("Pending TRENDS", pendingArr)
              setPendingChartTrends(pendingArr)
            })

            dateArrs.forEach((element) => {
              //console.log("ELEMENT",element)
              forEachDataUnclassifiedTrends(unclassifiedDataa, element)
              console.log("Unclassified TRENDS", unclassifiedArr)
              //setUnclassifiedChartTrends(unclassifiedArr)
              setUnclassifiedChartTrends(unclassifiedArr)
            })

            let chartData = {
              Pending: pendingTimeCount,
              Rejected: rejectedTimeCount,
              Approved: approvedTimeCount,
              Unclassified: unclassfiedTimeCount

            }

            console.log("CHARTTT", chart);
            console.log("CHART UNCLASSIFIED TRENDS", unclassifiedChartTrends, overallUnclassifiedTimeCountTrends);
            console.log("CHART REJECTED TRENDS", rejectedChartTrends, overallRejectedTimeCountTrends);
            console.log("CHART PENDING TRENDS", pendingChartTrends, overallPendingTimeCountTrends);
            console.log("CHART APPROVED TRENDS", approvedChartTrends, overallApprovedTimeCountTrends);

            setRejectedLabel(`Rejected  ${overallRejectedTimeCountTrends++}`);
            setPendingLabel(`Pending  ${overallPendingTimeCountTrends}`);
            setApprovedLabel(`Approved  ${overallApprovedTimeCountTrends}`);
            setUnclassifiedLabel(`Unclassified  ${overallUnclassifiedTimeCountTrends}`);


            setChart(chartData);
            setIsChartLoading(false);
          }).catch((err) => {
            setIsChartLoading(false)
            if (err.message === 'Request failed with status code 500') {
              toast.error('Error during fetching from Firestore', { preventDuplicate: true })
            }
          })
        }).catch((err) => {
          setIsChartLoading(false)
          if (err.message === 'Request failed with status code 500') {
            toast.error('Error during fetching from Firestore')
          }
        })
      }).catch((err) => {
        setIsChartLoading(false)
        if (err.message === 'Request failed with status code 500') {
          toast.error('Error during fetching from Firestore')
        }
      })
    }).catch((err) => {
      setIsChartLoading(false);
      if (err.message === 'Request failed with status code 500') {
        toast.error('Error during fetching from Firestore')
      }
      if (err.message === 'Network Error') {
        <ErrorComponent />
      }
    })
  }, [])


  //let customLabelsTrends = Object.keys(chart).map((label,index) =>`${label}: ${ Object.values(chart)[index]}`)
  function enumerateDaysBetweenDates(startDate, lastDate) {
    let date = []

    while (moment(startDate) >= moment(lastDate)) {
      date.push(lastDate);
      lastDate = moment(lastDate).add(1, 'days').format("YYYY-MM-DD");
    }
    return date;
  }


  return (
    <div>
      {/* 2 graphs need to render on the UI */}
      <Headers />
      <br />
      <Container>
        <div className="row">
          <div className="col-6">
            <label className="overviewTrends"></label>
          </div>

          <div className="col-6">
            <Button
              variant="secondary"
              className="uploadDocButton"
              onClick={() => history.push('/upload')}
            >
              Upload a Document
            </Button>{' '}
          </div>
        </div>
      </Container>
      <br />

      <DataTables />


    </div>

  );

}
export default Dashboard;
