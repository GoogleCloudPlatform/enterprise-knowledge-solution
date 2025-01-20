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

func TestDagIsAvailable(t *testing.T) {
	assert.EventuallyWithT(t, func(collect *assert.CollectT) {
		cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list")
		result := runCommand(cmd)

		assert.Contains(t, result, c.DAG_ID)
	}, 5*time.Minute, 30*time.Second, "DAG run_docs_processing is not yet available in Composer")
}

func TestDAGIsTriggered(t *testing.T) {
	cmd := exec.Command("../../sample-deployments/composer-orchestrated-process/scripts/trigger_workflow.sh")
	result := runCommand(cmd)

	// trigger_workflow.sh returns ANSI escaped characters for formatting, remove these for testing string results
	re := regexp.MustCompile(`\x1b\[[0-9;]*[mG]`)
	result = re.ReplaceAllString(result, "")

	assert.Contains(t, result, "Trigger DAG - done ")
}

func TestDAGIsSuccess(t *testing.T) {
	assert.EventuallyWithT(t, func(collect *assert.CollectT) {
		cmd := exec.Command("gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME, "--project", c.PROJECT_ID, "--location", c.LOCATION, "dags", "list-runs", "--", "-d", c.DAG_ID)
		result := runCommand(cmd)

		assert.Contains(t, result, "| success |")
	}, 60*time.Minute, 5*time.Minute, "DAG run_docs_processing did not complete with status 'success'")
}
