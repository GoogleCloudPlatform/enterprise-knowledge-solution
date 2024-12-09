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
