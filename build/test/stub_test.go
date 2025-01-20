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

//go:build stub

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

func runCommand(cmd *exec.Cmd) string {
	originalArgs := cmd.Args
	// Create a new Cmd instance for each retry with the original arguments (excluding cmd.Path)
	cmd = exec.Command(originalArgs[0], originalArgs[1:]...)
	fmt.Printf("Executing command: `%s`\n", cmd)
	output, err := cmd.CombinedOutput()
	if err != nil {
		log.Printf("Command failed with the following error: %s\n", err)
	}
	return string(output)
}

func TestDagIsAvailable(t *testing.T) {
	assert.EventuallyWithT(t, func(collect *assert.CollectT) {
		cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list")
		result := runCommand(cmd)

		assert.Contains(t, result, c.DAG_ID, fmt.Sprintf("DAG '%s' is not recognized by Composer, it might take a few minutes to propagate\n", c.DAG_ID))
	}, 5*time.Minute, 30*time.Second, "external state has not changed to 'true'; still false")
}

func TestDAGIsTriggered(t *testing.T) {
	assert.EventuallyWithT(t, func(collect *assert.CollectT) {
		cmd := exec.Command("../../sample-deployments/composer-orchestrated-process/scripts/trigger_workflow.sh")
		result := runCommand(cmd)

		// trigger_workflow.sh returns ANSI escaped characters for formatting, remove these for testing string results
		re := regexp.MustCompile(`\x1b\[[0-9;]*[mG]`)
		result = re.ReplaceAllString(result, "")

		assert.Contains(t, result, c.DAG_ID, fmt.Sprintf("DAG '%s' is not recognized by Composer, it might take a few minutes to propagate\n", c.DAG_ID))
	}, 5*time.Minute, 30*time.Second, "external state has not changed to 'true'; still false")
}

func TestDAGIsSuccess(t *testing.T) {
	assert.EventuallyWithT(t, func(collect *assert.CollectT) {
		cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list-runs", "--", "-d", c.DAG_ID)
		result := runCommand(cmd)

		assert.NotContains(t, result, "| running |", fmt.Sprintf("DAG '%s' is not yet complete, still has status 'running'\n", c.DAG_ID))
		assert.Contains(t, result, "| success |", fmt.Sprintf("DAG '%s' does not have the expected status 'success'\n", c.DAG_ID))
	}, 60*time.Minute, 1*time.Minute, "external state has not changed to 'true'; still false")

}

/*
func TestDAGIsSuccess(t *testing.T) {
	assert.EventuallyWithT(t, func(collect *assert.CollectT) {
		cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list-runs", "--", "-d", c.DAG_ID)
		result := runCommand(cmd)

		assert.Contains(t, result, "| success |", fmt.Sprintf("DAG '%s' does not have the expected status 'success'\n", c.DAG_ID))
	}, 5*time.Minute, 1*time.Minute, "external state has not changed to 'true'; still false")

}
*/
