// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Construct, RemovalPolicy } from '@aws-cdk/core';
import { AttributeType, BillingMode, Table, TableEncryption } from '@aws-cdk/aws-dynamodb';
import { Bucket, BucketEncryption, BlockPublicAccess} from '@aws-cdk/aws-s3';
import { PolicyStatement, AnyPrincipal, Effect } from '@aws-cdk/aws-iam';

/**,
 * @interface StorageContructProps
 * StorageContruct props
 */
export interface StorageContructProps {
  readonly solutionId: string;
  readonly s3LogsBucket: Bucket
}

/**
 * IoT Device Simulator storage construct
 * Creates an S3 bucket to store test scenarios and 
 * a DynamoDB table to store tests and test configuration
 */
export class StorageContruct extends Construct {
  public simulationsTable: Table;
  public deviceTypesTable: Table;
  public routesBucket: Bucket

  constructor(scope: Construct, id: string, props: StorageContructProps) {
    super(scope, id);

    this.simulationsTable = new Table(this, 'IDS-Simulations-Table', {
      billingMode: BillingMode.PAY_PER_REQUEST,
      encryption: TableEncryption.AWS_MANAGED,
      partitionKey: { name: 'simId', type: AttributeType.STRING },
      pointInTimeRecovery: true
    });

    this.deviceTypesTable = new Table(this, 'IDS-Device-Types-Table', {
      billingMode: BillingMode.PAY_PER_REQUEST,
      encryption: TableEncryption.AWS_MANAGED,
      partitionKey: { name: 'typeId', type: AttributeType.STRING },
      pointInTimeRecovery: true
    });

    this.routesBucket = new Bucket(this, 'RoutesBucket', {
      removalPolicy: RemovalPolicy.RETAIN,
      serverAccessLogsBucket: props.s3LogsBucket,
      serverAccessLogsPrefix: 'routes-bucket-access/',
      encryption: BucketEncryption.S3_MANAGED,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
    });

    this.routesBucket.addToResourcePolicy(
      new PolicyStatement({
        sid: 'HttpsOnly',
        resources: [
          `${this.routesBucket.bucketArn}/*`,
          `${this.routesBucket.bucketArn}`
        ],
        actions: ['*'],
        principals: [new AnyPrincipal()],
        effect: Effect.DENY,
        conditions:
        {
          Bool: {
            'aws:SecureTransport': 'false'
          }
        }
      })
    );
  }
}