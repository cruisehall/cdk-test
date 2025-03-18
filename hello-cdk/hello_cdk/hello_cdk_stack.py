from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_cloudwatch as cloudwatch
)
from constructs import Construct

class HelloCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        queue = sqs.Queue(
            self, "HelloCdkQueue",
            visibility_timeout=Duration.seconds(300),
        )

        alarm = cloudwatch.Alarm(
            self, "QueueLengthAlarm",
            metric=cloudwatch.Metric(
                metric_name="ApproximateAgeOfOldestMessage",
                namespace="AWS/SQS",
                period=Duration.seconds(60),
                dimensions_map=dict(QueueName=queue.queue_name)
            ),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            threshold=10,
            treat_missing_data=cloudwatch.TreatMissingData.MISSING,
            datapoints_to_alarm=5,
            evaluation_periods=5,
        )