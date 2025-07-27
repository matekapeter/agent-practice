import * as cdk from 'aws-cdk-lib';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as opensearch from 'aws-cdk-lib/aws-opensearchserverless';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export interface BedrockKnowledgeBaseStackProps extends cdk.StackProps {
  guardrailArn: string;
}

export class BedrockKnowledgeBaseStack extends cdk.Stack {
  public readonly knowledgeBaseId: string;
  public readonly knowledgeBaseArn: string;
  public readonly dataBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: BedrockKnowledgeBaseStackProps) {
    super(scope, id, props);

    // Create S3 bucket for knowledge base documents
    this.dataBucket = new s3.Bucket(this, 'KnowledgeBaseBucket', {
      bucketName: `bedrock-kb-data-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          id: 'DeleteIncompleteMultipartUploads',
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(7),
        },
      ],
    });

    // Deploy sample documents to S3
    new s3deploy.BucketDeployment(this, 'SampleDocuments', {
      sources: [s3deploy.Source.asset('./assets/sample-documents')],
      destinationBucket: this.dataBucket,
      destinationKeyPrefix: 'documents/',
    });

    // Create OpenSearch Serverless collection for vector storage
    const collectionName = 'bedrock-knowledge-base';

    // Encryption policy for OpenSearch Serverless
    const encryptionPolicy = new opensearch.CfnSecurityPolicy(this, 'EncryptionPolicy', {
      name: `${collectionName}-encryption-policy`,
      type: 'encryption',
      policy: JSON.stringify({
        Rules: [
          {
            ResourceType: 'collection',
            Resource: [`collection/${collectionName}`],
          },
        ],
        AWSOwnedKey: true,
      }),
    });

    // Network policy for OpenSearch Serverless
    const networkPolicy = new opensearch.CfnSecurityPolicy(this, 'NetworkPolicy', {
      name: `${collectionName}-network-policy`,
      type: 'network',
      policy: JSON.stringify([
        {
          Description: 'Public access for collection',
          Rules: [
            {
              ResourceType: 'collection',
              Resource: [`collection/${collectionName}`],
            },
            {
              ResourceType: 'dashboard',
              Resource: [`collection/${collectionName}`],
            },
          ],
          AllowFromPublic: true,
        },
      ]),
    });

    // Create OpenSearch Serverless collection
    const collection = new opensearch.CfnCollection(this, 'KnowledgeBaseCollection', {
      name: collectionName,
      description: 'OpenSearch Serverless collection for Bedrock Knowledge Base',
      type: 'VECTORSEARCH',
      standbyReplicas: 'DISABLED',
    });

    collection.addDependency(encryptionPolicy);
    collection.addDependency(networkPolicy);

    // Create IAM role for Bedrock Knowledge Base
    const knowledgeBaseRole = new iam.Role(this, 'KnowledgeBaseRole', {
      roleName: `BedrockKnowledgeBaseRole-${this.region}`,
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'IAM role for Bedrock Knowledge Base to access OpenSearch and S3',
    });

    // Add policies to the knowledge base role
    knowledgeBaseRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock:InvokeModel',
          'bedrock:InvokeModelWithResponseStream',
        ],
        resources: [
          `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v1`,
          `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v2:0`,
        ],
      })
    );

    knowledgeBaseRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          's3:GetObject',
          's3:ListBucket',
        ],
        resources: [
          this.dataBucket.bucketArn,
          `${this.dataBucket.bucketArn}/*`,
        ],
      })
    );

    knowledgeBaseRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'aoss:APIAccessAll',
        ],
        resources: [collection.attrArn],
      })
    );

    // Data access policy for OpenSearch Serverless
    const dataAccessPolicy = new opensearch.CfnAccessPolicy(this, 'DataAccessPolicy', {
      name: `${collectionName}-data-policy`,
      type: 'data',
      policy: JSON.stringify([
        {
          Description: 'Access for Bedrock Knowledge Base',
          Rules: [
            {
              ResourceType: 'index',
              Resource: [`index/${collectionName}/*`],
              Permission: [
                'aoss:CreateIndex',
                'aoss:DeleteIndex',
                'aoss:UpdateIndex',
                'aoss:DescribeIndex',
                'aoss:ReadDocument',
                'aoss:WriteDocument',
              ],
            },
            {
              ResourceType: 'collection',
              Resource: [`collection/${collectionName}`],
              Permission: ['aoss:CreateCollectionItems'],
            },
          ],
          Principal: [knowledgeBaseRole.roleArn],
        },
      ]),
    });

    dataAccessPolicy.addDependency(collection);

    // Lambda function to create OpenSearch index
    const indexCreationFunction = new lambda.Function(this, 'IndexCreationFunction', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import json
import boto3
import urllib3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import os

def handler(event, context):
    collection_endpoint = event['CollectionEndpoint']
    index_name = event['IndexName']
    
    # Create the index mapping for vector search
    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512,
                "knn.algo_param.ef_construction": 512
            }
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "engine": "nmslib",
                        "space_type": "cosinesimil",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {
                    "type": "text"
                },
                "AMAZON_BEDROCK_METADATA": {
                    "type": "text"
                }
            }
        }
    }
    
    # Sign the request
    session = boto3.Session()
    credentials = session.get_credentials()
    region = session.region_name or 'us-east-1'
    
    url = f"{collection_endpoint}/{index_name}"
    
    request = AWSRequest(
        method='PUT',
        url=url,
        data=json.dumps(index_body),
        headers={'Content-Type': 'application/json'}
    )
    
    SigV4Auth(credentials, 'aoss', region).add_auth(request)
    
    http = urllib3.PoolManager()
    response = http.urlopen(
        request.method,
        request.url,
        body=request.body,
        headers=dict(request.headers)
    )
    
    return {
        'statusCode': response.status,
        'body': response.data.decode('utf-8')
    }
      `),
      timeout: cdk.Duration.minutes(5),
    });

    // Grant permissions to the Lambda function
    indexCreationFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['aoss:APIAccessAll'],
        resources: [collection.attrArn],
      })
    );

    // Custom resource to create the index
    const indexCreation = new cr.AwsCustomResource(this, 'CreateIndex', {
      onCreate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: indexCreationFunction.functionName,
          Payload: JSON.stringify({
            CollectionEndpoint: collection.attrCollectionEndpoint,
            IndexName: 'bedrock-knowledge-base-index',
          }),
        },
        physicalResourceId: cr.PhysicalResourceId.of('CreateIndex'),
      },
      policy: cr.AwsCustomResourcePolicy.fromSdkCalls({
        resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE,
      }),
    });

    indexCreation.node.addDependency(dataAccessPolicy);

    // Create Bedrock Knowledge Base
    const knowledgeBase = new bedrock.CfnKnowledgeBase(this, 'KnowledgeBase', {
      name: 'comprehensive-knowledge-base',
      description: 'Knowledge base for AI agent with comprehensive document understanding',
      roleArn: knowledgeBaseRole.roleArn,
      knowledgeBaseConfiguration: {
        type: 'VECTOR',
        vectorKnowledgeBaseConfiguration: {
          embeddingModelArn: `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v2:0`,
          embeddingModelConfiguration: {
            bedrockEmbeddingModelConfiguration: {
              dimensions: 1536,
            },
          },
        },
      },
      storageConfiguration: {
        type: 'OPENSEARCH_SERVERLESS',
        opensearchServerlessConfiguration: {
          collectionArn: collection.attrArn,
          vectorIndexName: 'bedrock-knowledge-base-index',
          fieldMapping: {
            vectorField: 'bedrock-knowledge-base-default-vector',
            textField: 'AMAZON_BEDROCK_TEXT_CHUNK',
            metadataField: 'AMAZON_BEDROCK_METADATA',
          },
        },
      },
    });

    knowledgeBase.addDependency(indexCreation);

    // Create data source
    const dataSource = new bedrock.CfnDataSource(this, 'DataSource', {
      knowledgeBaseId: knowledgeBase.attrKnowledgeBaseId,
      name: 'comprehensive-data-source',
      description: 'S3 data source for knowledge base documents',
      dataSourceConfiguration: {
        type: 'S3',
        s3Configuration: {
          bucketArn: this.dataBucket.bucketArn,
          inclusionPrefixes: ['documents/'],
        },
      },
      vectorIngestionConfiguration: {
        chunkingConfiguration: {
          chunkingStrategy: 'FIXED_SIZE',
          fixedSizeChunkingConfiguration: {
            maxTokens: 300,
            overlapPercentage: 20,
          },
        },
      },
    });

    // Store outputs for use in other stacks
    this.knowledgeBaseId = knowledgeBase.attrKnowledgeBaseId;
    this.knowledgeBaseArn = knowledgeBase.attrKnowledgeBaseArn;

    // Export values for cross-stack references
    new cdk.CfnOutput(this, 'KnowledgeBaseId', {
      value: this.knowledgeBaseId,
      description: 'ID of the Bedrock Knowledge Base',
      exportName: `${this.stackName}-KnowledgeBaseId`,
    });

    new cdk.CfnOutput(this, 'KnowledgeBaseArn', {
      value: this.knowledgeBaseArn,
      description: 'ARN of the Bedrock Knowledge Base',
      exportName: `${this.stackName}-KnowledgeBaseArn`,
    });

    new cdk.CfnOutput(this, 'DataBucketName', {
      value: this.dataBucket.bucketName,
      description: 'Name of the S3 bucket for knowledge base documents',
      exportName: `${this.stackName}-DataBucketName`,
    });

    // Tag resources
    cdk.Tags.of(this).add('Component', 'KnowledgeBase');
    cdk.Tags.of(this).add('Purpose', 'VectorStore');
  }
}