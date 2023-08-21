# ######################################################################################################################
#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.                                                  #
#                                                                                                                      #
#  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance      #
#  with the License. You may obtain a copy of the License at                                                           #
#                                                                                                                      #
#   http://www.apache.org/licenses/LICENSE-2.0                                                                         #
#                                                                                                                      #
#  Unless required by applicable law or agreed to in writing, software distributed under the License is distributed    #
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for   #
#  the specific language governing permissions and limitations under the License.                                      #
# ######################################################################################################################

import json
import os
import shutil

import aws_cdk
from aws_cdk import App, CfnOutput

from stack import MWAAStack

# Project specific
project_name = os.getenv("SEEDFARMER_PROJECT_NAME", "")
deployment_name = os.getenv("SEEDFARMER_DEPLOYMENT_NAME", "")
module_name = os.getenv("SEEDFARMER_MODULE_NAME", "")

if len(f"{project_name}-{deployment_name}") > 36:
    raise ValueError("This module cannot support a project+deployment name character length greater than 35")


def _param(name: str) -> str:
    return f"SEEDFARMER_PARAMETER_{name}"


# App specific
vpc_id = os.getenv(_param("VPC_ID"))  # required
private_subnet_ids = json.loads(os.getenv(_param("PRIVATE_SUBNET_IDS"), ""))  # required
dag_bucket_name = os.getenv(_param("DAG_BUCKET_NAME"))
airflow_version = os.getenv(_param("AIRFLOW_VERSION"))
dag_path = os.getenv(_param("DAG_PATH"))
environment_class = os.getenv(_param("ENVIRONMENT_CLASS"))
max_workers = os.getenv(_param("MAX_WORKERS"), "1")
unique_requirements_file = os.getenv("UNIQUE_REQUIREMENTS_FILE")

if not vpc_id:
    raise ValueError("missing input parameter vpc-id")

if not private_subnet_ids:
    raise ValueError("missing input parameter private-subnet-ids")

app = App()

# zip plugin
shutil.make_archive("plugins/plugins", "zip", "plugins/")

optional_args = {}
if dag_bucket_name:
    optional_args["dag_bucket_name"] = dag_bucket_name
if dag_path:
    optional_args["dag_path"] = dag_path
if environment_class:
    optional_args["environment_class"] = environment_class
if max_workers and max_workers.isnumeric():
    optional_args["max_workers"] = int(max_workers)  # type: ignore
optional_args["airflow_version"] = airflow_version if airflow_version else "2.5.1"


stack = MWAAStack(
    scope=app,
    id=f"{project_name}-{deployment_name}-{module_name}",
    project_name=project_name,
    deployment_name=deployment_name,  # type: ignore
    module_name=module_name,  # type: ignore
    vpc_id=vpc_id,
    private_subnet_ids=private_subnet_ids,
    unique_requirements_file=unique_requirements_file,  # type: ignore
    env=aws_cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
    **optional_args,  # type: ignore
)

CfnOutput(
    scope=stack,
    id="metadata",
    value=stack.to_json_string(
        {
            "DagBucketName": stack.dag_bucket.bucket_name,
            "DagPath": stack.dag_path,
            "MwaaExecRoleArn": stack.mwaa_environment.execution_role_arn,
        }
    ),
)

app.synth(force=True)
