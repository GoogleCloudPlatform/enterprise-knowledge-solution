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

	"github.com/sethvargo/go-envconfig"
	"github.com/stretchr/testify/assert"
)

type CLIConfig struct {
	PROJECT_ID        string `env:"PROJECT_ID"`
	LOCATION          string `env:"LOCATION"`
	COMPOSER_ENV_NAME string `env:"COMPOSER_ENV_NAME"`
	DAG_ID            string `env:"DAG_ID"`
}

func TestDAGState(t *testing.T) {
	ctx := context.Background()
	var c CLIConfig
	if err := envconfig.Process(ctx, &c); err != nil {
		log.Fatal(err)
	}

	cmd := exec.Command(
		"gcloud", "composer", "environments", "run", c.COMPOSER_ENV_NAME,
		"--location", c.LOCATION,
		"--project", c.PROJECT_ID,
		"dags", "list-runs",
		"--", "-d", c.DAG_ID,
	)

	fmt.Println("Executing command:", cmd.String())

	out, err := cmd.Output()
	if err != nil {
		t.Fatalf("Failed to execute gcloud command: %v", err)
	}

	output := string(out)
	fmt.Println("gcloud output: \n", output)

	matched, err := regexp.MatchString(`\| success \|`, output)
	if err != nil {
		t.Fatalf("Failed to match regex: %v", err)
	}

	assert.True(t, matched, "DAG run with state 'success' not found in gcloud output")
}
