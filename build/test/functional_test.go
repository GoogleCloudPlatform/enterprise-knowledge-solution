// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

//go:build functional

package main

import (
	"context"
	"fmt"
	"log"
	"os/exec"
	"regexp"
	"strings"
	"testing"
	"time"

	envconfig "github.com/sethvargo/go-envconfig"
	"github.com/stretchr/testify/assert"
)

type CLIConfig struct {
	PROJECT_ID        string `env:"PROJECT_ID"`
	LOCATION          string `env:"LOCATION"`
	COMPOSER_ENV_NAME string `env:"COMPOSER_ENV_NAME"`
	DAG_ID            string `env:"DAG_ID"`
}

var c CLIConfig

func init() {
	ctx := context.Background()
	if err := envconfig.Process(ctx, &c); err != nil {
		log.Fatal(err)
	}
}

func runCommand(cmd *exec.Cmd) string {
	originalArgs := cmd.Args
	// Create a new Cmd instance for each retry with the original arguments (excluding cmd.Path)
	cmd = exec.Command(originalArgs[0], originalArgs[1:]...)
	fmt.Println("Executing command: `", cmd, "`")
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println("Command failed with the following error: ", err)
	}
	return string(output)
}

func runCommandWithPolling(cmd *exec.Cmd, stringToMatch string, retryAttempts int, retryInterval time.Duration) string {
	for i := 0; i < retryAttempts; i++ {
		fmt.Println("Attempt", i+1, "of", retryAttempts)
		result := runCommand(cmd)

		if strings.Contains(result, stringToMatch) {
			return result
		}
		fmt.Println("Output string does not include the expected value, sleeping for", retryInterval, "before trying again")
		time.Sleep(retryInterval)
	}
	return "condition not met"
}

func TestDagIsAvailable(t *testing.T) {
	cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list")
	stringToMatch := c.DAG_ID

	result := runCommandWithPolling(cmd, stringToMatch, 5, 30*time.Second) // typically completes in 2-3 minutes

	assert.Contains(t, result, stringToMatch)
}

func TestDAGIsTriggered(t *testing.T) {
	cmd := exec.Command("../../sample-deployments/composer-orchestrated-process/scripts/trigger_workflow.sh")
	stringToMatch := "Trigger DAG - done"

	result := runCommand(cmd) // 1 attempt only, no polling and retry
	// trigger_workflow.sh returns ANSI escaped characters for formatting, remove these for testing string results
	re := regexp.MustCompile(`\x1b\[[0-9;]*[mG]`)
	result = re.ReplaceAllString(result, "")

	assert.Contains(t, result, stringToMatch)
}

func TestDagIsSuccess(t *testing.T) {
	cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list-runs", "--", "-d", c.DAG_ID)
	stringToMatch := "| success |"

	result := runCommandWithPolling(cmd, stringToMatch, 10, 5*time.Minute) // workflow might be in "running" state for 25+ minutes, can be much greater depending on volume of test docs

	assert.Contains(t, result, stringToMatch)
}
