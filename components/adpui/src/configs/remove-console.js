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

export const GlobalDebug = (function () {
    var savedConsole = console;
    /**
    * @param {boolean} debugOn
    * @param {boolean} suppressAll
    */
    return function (debugOn, suppressAll) {
      var suppress = suppressAll || false;
      if (debugOn === false) {
        // supress the default console functionality
        console = {};
        console.log = function () {};
        // supress all type of consoles
        if (suppress) {
          console.info = function () {};
          console.warn = function () {};
          console.error = function () {};
        } else {
          console.info = savedConsole.info;
          console.warn = savedConsole.warn;
          console.error = savedConsole.error;
        }
      } else {
        console = savedConsole;
      }
    };
  })();


  