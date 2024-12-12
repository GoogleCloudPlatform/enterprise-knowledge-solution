// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
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
	"testing"

	logging "cloud.google.com/go/logging/logadmin"
	envconfig "github.com/sethvargo/go-envconfig"
	assert "github.com/stretchr/testify/assert"
)

type LoggingConfig struct {
	PROJECT_ID string `env:"PROJECT_ID"`
}

var filters []string = []string{
	`resource.labels.container_name="airflow-scheduler" AND textPayload:("initial_load_from_input_bucket.list_all_input_files" AND "state=success")`,
	`resource.labels.container_name="airflow-scheduler" AND textPayload:("initial_load_from_input_bucket.has_files_to_process" AND "state=success")`,
}

func TestLogExists(t *testing.T) {
	ctx := context.Background()
	var c LoggingConfig
	if err := envconfig.Process(ctx, &c); err != nil {
		log.Fatal(err)
	}
	client, err := logging.NewClient(ctx, c.PROJECT_ID)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	for _, filter := range filters {
		t.Run(filter, func(t *testing.T) {
			fmt.Printf("Checking filter: %s\n", filter)

			it := client.Entries(ctx, logging.Filter(filter))
			entry, err := it.Next()

			assert.NoError(t, err, "it.Next() should not return an error")
			assert.NotNil(t, entry, "Log entry should not be nil")
		})
	}
}
