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
	"testing"

	logger "github.com/gruntwork-io/terratest/modules/logger"
	terraform "github.com/gruntwork-io/terratest/modules/terraform"
	test_structure "github.com/gruntwork-io/terratest/modules/test-structure"
	envconfig "github.com/sethvargo/go-envconfig"
)

type TestConfig struct {
	ProjectId               string `env:"PROJECT_ID,required"`
	Region                  string `env:"REGION,required"`
	DocAiLocation           string `env:"DOC_AI_LOCATION,required"`
	VertexAiDataStoreRegion string `env:"VERTEX_AI_DATA_STORE_REGION,required"`
	IapAccessDomains        string `env:"IAP_ACCESS_DOMAINS,required"`
	WebUiDomains            string `env:"WEB_UI_DOMAINS,required"`
	CustomClassifierId      string `env:"CUSTOM_CLASSIFIER_ID, required"`
}

func TestE2e(t *testing.T) {

	var config TestConfig

	ctx := context.Background()
	err := envconfig.Process(ctx, &config)
	if err != nil {
		logger.Log(t, "There was an error processing the supplied environment variables:")
		logger.Log(t, err)
		t.Fatal()
	}

	terraformDir := "../../sample-deployments/composer-orchestrated-process"

	test_structure.RunTestStage(t, "setup", func() {
		terraformOptions := &terraform.Options{
			TerraformDir: terraformDir,

			Vars: map[string]interface{}{
				"project_id":                  config.ProjectId,
				"region":                      config.Region,
				"iap_access_domains":          config.IapAccessDomains,
				"webui_domains":               config.WebUiDomains,
				"docai_location":              config.DocAiLocation,
				"vertex_ai_data_store_region": config.VertexAiDataStoreRegion,
				"custom_classifier_id":        config.CustomClassifierId,
			},
			NoColor: true,
		}

		test_structure.SaveTerraformOptions(t, terraformDir, terraformOptions)
		terraform.Init(t, terraformOptions)
	})

	test_structure.RunTestStage(t, "apply", func() {
		terraformOptions := test_structure.LoadTerraformOptions(t, terraformDir)
		terraform.InitAndApply(t, c)
	})

	test_structure.RunTestStage(t, "migrate-tfstate", func() {
		terraformOptions := test_structure.LoadTerraformOptions(t, terraformDir)
		terraformOptions["MigrateState"] = true
		terraform.InitE(t, terraformOptions)
	})
}
