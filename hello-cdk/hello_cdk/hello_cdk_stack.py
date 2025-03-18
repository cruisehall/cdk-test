from enum import Enum
from typing import List, Optional
from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
)
from constructs import Construct


def add_actions(alarm: cloudwatch.Alarm, topic: sns.Topic):
    alarm.add_alarm_action(cloudwatch_actions.SnsAction(topic))
    alarm.add_ok_action(cloudwatch_actions.SnsAction(topic))


class Operator(Enum):
    above = cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
    at_or_above = cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
    below = cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD
    at_or_below = cloudwatch.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD


class Threshold:
    def __init__(
        self,
        operator: Operator,
        threshold: int,
        for_all_mins: Optional[int] = None,
        for_any_mins: Optional[int] = None,
    ):
        self.threshold = threshold
        self.comparison_operator = operator.value
        if for_all_mins:
            self.evaluation_periods = for_all_mins
            self.datapoints_to_alarm = for_all_mins
        elif for_any_mins:
            self.evaluation_periods = for_any_mins
            self.datapoints_to_alarm = 1
        else:
            raise Exception("Must provide either 'for_mins' or 'over_mins'")
        self.period: Duration = Duration.seconds(60)


class Metrics(Enum):
    APPROXIMATE_AGE_OF_OLDEST_MESSAGE = ("AWS/SQS", "ApproximateAgeOfOldestMessage")


class AlarmCollectionBuilder:
    def __init__(self):
        self.thresholds: List[Threshold] = []
        self.metric_name: Optional[str] = None
        self.metric_namespace: Optional[str] = None
        self.dimensions: Optional[dict] = None
        self.sns_topic: Optional[sns.Topic] = None

    def with_sns_topic(self, topic: sns.Topic):
        self.sns_topic = topic
        return self

    def with_metric(self, metric: Metrics):
        self.metric_namespace = metric.value[0]
        self.metric_name = metric.value[1]
        return self

    def with_dimensions(self, **kwargs):
        self.dimensions = kwargs
        return self

    def with_thresholds(self, thresholds: List[Threshold]):
        self.thresholds.extend(thresholds)
        return self

    def build(self, scope: Construct):
        alarms = []
        for threshold in self.thresholds:
            alarm = cloudwatch.Alarm(
                scope=scope,
                id=f"{self.metric_namespace}_{self.metric_name}_{threshold.comparison_operator.name}_{threshold.period.seconds}_{threshold.threshold}_{threshold.datapoints_to_alarm}_{threshold.evaluation_periods}".replace(
                    "/", "_"
                ),
                metric=cloudwatch.Metric(
                    metric_name=self.metric_name,
                    namespace=self.metric_namespace,
                    period=threshold.period,
                    dimensions_map=self.dimensions,
                ),
                comparison_operator=threshold.comparison_operator,
                threshold=threshold.threshold,
                datapoints_to_alarm=threshold.datapoints_to_alarm,
                evaluation_periods=threshold.evaluation_periods,
            )
            alarms.append(alarm)
            if self.sns_topic:
                alarm.add_alarm_action(cloudwatch_actions.SnsAction(sns))
                alarm.add_ok_action(cloudwatch_actions.SnsAction(sns))
        return alarms


class HelloCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        queue = sqs.Queue(
            self,
            "HelloCdkQueue",
            visibility_timeout=Duration.seconds(300),
        )
        # Optional: create alarms as you create resources
        urgent_alert_topic = sns.Topic(self, "UrgentAlerts")

        alarm = cloudwatch.Alarm(
            self,
            "QueueLengthAlarm",
            alarm_name="Old messages are sitting on the HelloCdkQueue",
            metric=cloudwatch.Metric(
                metric_name="ApproximateAgeOfOldestMessage",
                namespace="AWS/SQS",
                period=Duration.seconds(60),
                dimensions_map=dict(QueueName=queue.queue_name),
            ),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            threshold=10,
            treat_missing_data=cloudwatch.TreatMissingData.MISSING,
            datapoints_to_alarm=5,
            evaluation_periods=5,
        )
        add_actions(alarm=alarm, topic=urgent_alert_topic)

        # Optional: Define higher-order constructs with simpler interface, advanced features
        AlarmCollectionBuilder().with_metric(
            metric=Metrics.APPROXIMATE_AGE_OF_OLDEST_MESSAGE
        ).with_dimensions(QueueName=queue.queue_name).with_thresholds(
            # advanced feature: threshold "sloping"
            [
                # no single message should be older than 10 minutes
                Threshold(operator=Operator.at_or_above, threshold=10, for_any_mins=1),
                # the queue should be draining messages at least once every 10min
                Threshold(operator=Operator.above, threshold=0, for_all_mins=10),
            ]
        ).with_sns_topic(
            topic=urgent_alert_topic
        )
        return None
