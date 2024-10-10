//go:build e2e

/**
 * Copyright 2023 Google LLC
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
 */

 package test

 import (
	 "context"
	 "encoding/json"
	 "fmt"
	 "testing"
	 "time"

	 logger "github.com/gruntwork-io/terratest/modules/logger"
	 retry "github.com/gruntwork-io/terratest/modules/retry"
	 terraform "github.com/gruntwork-io/terratest/modules/terraform"
	 test_structure "github.com/gruntwork-io/terratest/modules/test-structure"

	 envconfig "github.com/sethvargo/go-envconfig"
	 assert "github.com/stretchr/testify/assert"
 )

 type TestConfig struct {
	 ProjectId string `env:"PROJECT_ID,required"`
 }

 func TestPerProjectEndToEndDeployment(t *testing.T) {


	 const (
		 region = "us-central1"
		 iap_access_domains = "['domain:eks-cicd.joonix.net']"
		 webui_domains = "['eks-cicd.altostrat.com', 'demo.eks-cicd.altostrat.com']"
		 docai_location = "us"
	 )

	 var config TestConfig

	 ctx := context.Background()
	 err := envconfig.Process(ctx, &config)
	 if err != nil {
		 logger.Log(t, "There was an error processing the supplied environment variables:")
		 logger.Log(t, err)
		 t.Fatal()
	 }

	 terraformDir := "../sample-deployments/composer-orchestrated-process"

	 test_structure.RunTestStage(t, "setup", func() {
		 terraformOptions := &terraform.Options{
			 TerraformDir: terraformDir,

			 Vars: map[string]interface{}{
				 "project_id":                    config.ProjectId,
				 "region":                        region,
				 "iap_access_domains":            iap_access_domains,
				 "webui_domains":                 webui_domains,
				 "docai_location":                docai_location
			 },
			 NoColor: true,
		 }

		 test_structure.SaveTerraformOptions(t, terraformDir, terraformOptions)
		 terraform.Init(t, terraformOptions)
	 })

	 defer test_structure.RunTestStage(t, "teardown", func() {
		 terraformOptions := test_structure.LoadTerraformOptions(t, terraformDir)
		 terraform.Destroy(t, terraformOptions)
	 })

	 test_structure.RunTestStage(t, "apply", func() {
		 terraformOptions := test_structure.LoadTerraformOptions(t, terraformDir)
		 terraform.ApplyAndIdempotent(t, terraformOptions)
	 })


	 test_structure.RunTestStage(t, "validate", func() {
		 terraformOptions := test_structure.LoadTerraformOptions(t, terraformDir)
		 ctx := context.Background()

		 instanceAdmin, err := instance.NewInstanceAdminClient(ctx)
		 assert.Nil(t, err)
		 assert.NotNil(t, instanceAdmin)
		 defer instanceAdmin.Close()

		 schedulerJobId := terraform.Output(t, terraformOptions, schedulerJobTfOutput)
		 schedulerClient, err := scheduler.NewCloudSchedulerClient(ctx)
		 assert.Nil(t, err)
		 assert.NotNil(t, schedulerClient)
		 defer schedulerClient.Close()

		 // Wait up to a minute for Spanner to report initial processing units
		 spannerInstanceId := fmt.Sprintf("projects/%s/instances/%s", config.ProjectId, spannerName)
		 waitForSpannerProcessingUnits(t, instanceAdmin, spannerInstanceId, spannerTestProcessingUnits, 6, time.Second*10)

		 // Update the autoscaler config with a new minimum number of processing units
		 setAutoscalerConfigMinProcessingUnits(t, schedulerClient, schedulerJobId, spannerTargetProcessingUnits)

		 // Wait up to five minutes for Spanner to report final processing units
		 waitForSpannerProcessingUnits(t, instanceAdmin, spannerInstanceId, spannerTargetProcessingUnits, 5*6, time.Second*10)
	 })

 }
