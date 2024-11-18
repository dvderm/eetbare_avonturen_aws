from aws_cdk import (
    Stack,
    aws_ses as ses,
    aws_ses_actions as ses_actions,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct

class EetbareAvonturenAwsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an S3 bucket for hosting the website
        website_bucket = s3.Bucket(self, "WebsiteBucket",
            website_index_document="index.html",
            # website_error_document="error.html",
            public_read_access=True,                                # Make the bucket publicly accessible
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            removal_policy=RemovalPolicy.DESTROY,                   # Delete the bucket on stack removal
            auto_delete_objects=True,                               # Automatically delete bucket objects on removal
        )

         # Deploy website files from the local 'site' directory to the root of the S3 bucket
        s3deploy.BucketDeployment(self, "DeployWebsite",
            sources=[s3deploy.Source.asset("./site")],
            destination_bucket=website_bucket,
            destination_key_prefix=""                       # Ensure files are placed in the root of the bucket
        )

        # Create the DynamoDB table for the appointments
        appointment_table = dynamodb.Table(self, "AppointmentsTable",
                                           partition_key=dynamodb.Attribute(
                                               name='id',
                                               type=dynamodb.AttributeType.STRING
                                           ),
                                           billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                                           removal_policy=RemovalPolicy.DESTROY)
        
        # Create a Lambda function to handle reservation submissions
        reservation_lambda = lambda_.Function(self, "ReservationFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="reservation_handler.lambda_handler",               # Entry point in the code file
            code=lambda_.Code.from_asset("lambda_reservation"),         # Directory where the code is located
            environment={                                               # Setting environment variables that are used in script reservation_handler.py
                'TABLE_NAME': appointment_table.table_name,
                'SENDER_EMAIL': "info@eetbareavonturen.nl"
            }
        )

        # Grant the Lambda function permissions to send emails via SES
        reservation_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["ses:SendEmail", "ses:SendRawEmail"],
            resources=["*"]
        ))

        # Create an API Gateway REST API to expose the Lambda function as an endpoint
        api = apigateway.RestApi(self, "ReservationApi",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=[website_bucket.bucket_website_url],      # "website_bucket.bucket_website_url" gives a string. Property "allow_origins" only allows strings in array, which is why the brackets are used around the website url. 
                allow_methods=["POST"]                                  # Only allow POST API calls
            ),
            rest_api_name="Reservation Service",
            description="This service handles reservation submissions.",
        )

        # Create an endpoint that triggers the Lambda function
        reservations = api.root.add_resource("reservations")
        reservations_lambda_integration = apigateway.LambdaIntegration(reservation_lambda)
        reservations.add_method("POST", reservations_lambda_integration)

        # Grant the Lambda function permissions to write to the DynamoDB table
        appointment_table.grant_write_data(reservation_lambda)

        # Create an SES email identity
        email_identity = ses.EmailIdentity(self, "SenderEmailIdentity",
            identity=ses.Identity.email("info@eetbareavonturen.nl")  
        )

        # Create a Lambda function to remind customers one day before reservationdate
        # reminder_lambda = lambda_.Function(self, "ReminderFunction",
        #     runtime=lambda_.Runtime.PYTHON_3_9,
        #     code=
        # )

        # Output the S3 website URL
        CfnOutput(self, "WebsiteURL",
            value=website_bucket.bucket_website_url,
            description="The URL of the static website"
        )

        # Output the API Endpoint
        CfnOutput(self, "ApiEndpoint",
            value=api.url + "reservations",
            description="The API endpoint for reservation submissions"
        )