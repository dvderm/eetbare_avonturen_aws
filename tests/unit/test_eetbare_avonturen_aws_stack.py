import aws_cdk as core
import aws_cdk.assertions as assertions

from eetbare_avonturen_aws.eetbare_avonturen_aws_stack import EetbareAvonturenAwsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in eetbare_avonturen_aws/eetbare_avonturen_aws_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EetbareAvonturenAwsStack(app, "eetbare-avonturen-aws")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
