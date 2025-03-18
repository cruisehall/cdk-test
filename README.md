# CDK Demo

## Setup
_Recommended_: Use GitHub Codespaces (hit `.` when viewing this repo in GitHub)

```sh
pip install -r hello-cdk/requirements.txt
npm install -g aws-cdk
```
## Inspect the stack
Open [hello-cdk/app.py](./hello-cdk/app.py), which acts as the entrypoint (as dictated by the `app` attribute in [cdk.json](./hello-cdk/cdk.json)).
```py
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from hello_cdk.hello_cdk_stack import HelloCdkStack

app = cdk.App()
HelloCdkStack(
    app,
    "HelloCdkStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.
    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.
    # env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */
    # env=cdk.Environment(account='123456789012', region='us-east-1'),
    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
)

app.synth()
```
## Generate the stack

```sh
cd hello-cdk
cdk synth -o dist
```
CloudFormation stacks will be generated and placed in `hello-cdk/dist`.

