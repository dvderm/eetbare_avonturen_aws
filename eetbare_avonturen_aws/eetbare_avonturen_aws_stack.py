from aws_cdk import (
    Stack,
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
            public_read_access=True,  # Make the bucket publicly accessible
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            removal_policy=RemovalPolicy.DESTROY,  # Delete the bucket on stack removal
            auto_delete_objects=True,  # Automatically delete bucket objects on removal
        )

         # Deploy website files from the local 'site' directory to the root of the S3 bucket
        s3deploy.BucketDeployment(self, "DeployWebsite",
            sources=[s3deploy.Source.asset("./site")],
            destination_bucket=website_bucket,
            destination_key_prefix=""  # Ensure files are placed in the root of the bucket
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
            handler="reservation_handler.lambda_handler",  # Entry point in the code file
            code=lambda_.Code.from_asset("lambda"),  # Directory where the code is located
            environment={
                'TABLE_NAME': appointment_table.table_name
            }
        )

        # Create an API Gateway REST API to expose the Lambda function as an endpoint
        api = apigateway.RestApi(self, "ReservationApi",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,      # Instead of ALL_ORIGINS it should have only the origin of my website
                allow_methods=apigateway.Cors.ALL_METHODS       # Instead of ALL_METHODS it should probably only have POST, according to perplexity this would be: allow_methods=["POST"]
            ),
            rest_api_name="Reservation Service",
            description="This service handles reservation submissions.",
        )

        # Create an endpoint that triggers the Lambda function
        reservations = api.root.add_resource("reservations")
        reservations_lambda_integration = apigateway.LambdaIntegration(reservation_lambda)
        reservations.add_method("POST", reservations_lambda_integration)  # POST /reservations

        # Grant the Lambda function permissions to write to the DynamoDB table
        appointment_table.grant_write_data(reservation_lambda)

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