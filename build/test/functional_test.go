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

// retryFunc defines the type of function that will be used for the assertion
type retryFunc func(t *testing.T, output string) bool

// runCommandWithRetry executes the given command and performs the assertion with retry logic
func runCommandWithRetry(t *testing.T, cmd *exec.Cmd, assertion retryFunc, retries int, retryInterval time.Duration) {
	originalArgs := cmd.Args

	for i := 0; i < retries; i++ {
		// Create a new Cmd instance for each retry with the original arguments (excluding cmd.Path)
		cmd := exec.Command(originalArgs[0], originalArgs[1:]...)
		fmt.Printf("Executing command: `%s`\n", cmd)
		output, err := cmd.CombinedOutput()
		if err != nil {
			log.Printf("Command failed with the following error: %s\n", err)
		}

		if assertion(t, string(output)) {
			break
		}

		if i < retries-1 {
			log.Printf("Retry %d failed. Waiting %s before retrying...\n", i+1, retryInterval)
			time.Sleep(retryInterval)
		}
	}
}

func TestDAGIsAvailable(t *testing.T) {
	cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list")

	assertion := func(t *testing.T, output string) bool {
		return assert.Contains(t, output, c.DAG_ID, fmt.Sprintf("DAG '%s' is not recognized by Composer, it might take a few minutes to propagate\n", c.DAG_ID))
	}

	runCommandWithRetry(t, cmd, assertion, 5, 2*time.Minute)
}

func TestDAGIsTriggered(t *testing.T) {
	cmd := exec.Command("../../sample-deployments/composer-orchestrated-process/scripts/trigger_workflow.sh")

	assertion := func(t *testing.T, output string) bool {
		// Strip ANSI escape codes from the output, otherwise the formatting characters obscure the status messages from the script
		re := regexp.MustCompile(`\x1b\[[0-9;]*[mG]`)
		strippedOutput := re.ReplaceAllString(output, "")

		return assert.Contains(t, strippedOutput, "Trigger DAG - done", "script to trigger workflow did not complete successfully\n")
	}

	runCommandWithRetry(t, cmd, assertion, 3, time.Minute)
}

func TestDAGIsSuccess(t *testing.T) {
	cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list-runs", "--", "-d", c.DAG_ID)

	assertion := func(t *testing.T, output string) bool {
		return assert.Contains(t, output, "| success |", fmt.Sprintf("DAG '%s' has not completed with status 'success'", c.DAG_ID))
	}

	runCommandWithRetry(t, cmd, assertion, 10, 3*time.Minute)
}
