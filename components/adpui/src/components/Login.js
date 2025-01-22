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

/* This page is the starting point of the UI where a user can sign in 2 ways
 * a) User can signup with the email accounts other than the google account
 * b) User can choose google signin button to directly sign through the google accounts
 * The configuration files for goole is setup in the firebase.config.js file.
 */

import React, { useState } from "react";
import { Redirect } from 'react-router';
import { Button } from 'primereact/button';
import { Image,Row,Col } from 'react-bootstrap';
import {
  signInWithEmailAndPassword,
} from "firebase/auth";
import { FcGoogle } from "react-icons/fc";
import { auth, signInWithGoogle } from "../configs/firebase.config";
import "../App.css";
import imgFile from '../images/googleCloud.png';


function Login() {
  // React States
  const [errorMessages, setErrorMessages] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);

  // To sign with the other email accounts
  const handleSubmit = async (event) => {
    //Prevent page reload
    event.preventDefault();

    var { uname, pass } = document.forms[0];
    try {
      const user = await signInWithEmailAndPassword(
        auth,
        uname.value,
        pass.value
      );
      console.log(user);
      if (user) {
        setIsSubmitted(true);
        console.log("User signedin success");
        localStorage.setItem('login', true);
        localStorage.setItem('user', user.user.email);
        window.location = "/";
      }
    } catch (error) {
      console.log(error.message);
      setErrorMessages({ name: "uname", message: error.message });
    }
  };


  // Generate JSX code for error message login
  const renderErrorMessage = (name) =>
    name === errorMessages.name && (
      <div className="error">{errorMessages.message}</div>
    );

  // JSX code for login form
  const renderForm = (
    <div>
    <div className="form">
      <form onSubmit={handleSubmit}>
        <div className="input-container">
          <Row>
            <h5 style={{fontWeight:'bolder'}}>Sign In</h5>
          </Row>
          <Row>
            <Col className="col-4" style={{marginTop: '0.6em'}}>
            <label>Email </label>
            </Col>

            <Col className="col-8">
            <input type="text" name="uname" style={{width:'100%'}} placeholder="Please enter email" className="loginInput" required />
          {renderErrorMessage("uname")}
            </Col>

          </Row>
        </div>
        <div className="input-container">

        <Row>
            <Col className="col-4"style={{marginTop: '0.6em'}}>
            <label>Password </label>
            </Col>

            <Col className="col-8">
            <input type="password" name="pass" style={{width:'100%'}} placeholder="Please enter password" className="loginInput" required />
          {renderErrorMessage("pass")}
            </Col>

          </Row>
        
        </div>
        <div className="input-container">
        <Row>
          <Col className="col-4">
          </Col>
          <Col className="col-8">
          <input type="submit" style={{width:'100%'}} value="Sign In"/>
          </Col>
        </Row>
          
          
          
        </div>
        
      </form>

 
    </div>
         
   </div>
  );

  return (
    <div className="logindiv">
      <div className="login-form">
      <Image src={imgFile} width='260px' height='70px' style={{display: 'block',
    margin: '0 auto'}}/>
      <h4 className="loginTitle">Claims Data Activator</h4> <br/>
        {isSubmitted ? <Redirect to="/" /> : renderForm}
      </div>
    </div>
  );


}

export default Login;
