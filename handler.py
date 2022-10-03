"""Lambda Function handlers for the Serverless Live To VOD use case"""

import json
import os
import time

import boto3

PACKAGING_GROUP_ID = os.environ['PACKAGING_GROUP_ID']
CLIPS_ORIGIN_ENDPOINT_ID = os.environ['CLIPS_ORIGIN_ENDPOINT_ID']

CLIPS_BUCKET = os.environ['CLIPS_BUCKET']
CLIPS_TABLE = os.environ['CLIPS_TABLE']
MEDIA_PACKAGE_S3_ROLE_ARN = os.environ['MEDIA_PACKAGE_S3_ROLE_ARN']

COMPETITION_ID = "100m-dash"

mediapackage = boto3.client('mediapackage')
mediapackage_vod = boto3.client('mediapackage-vod')
dynamodb = boto3.resource('dynamodb')


def create_new_clip(event, context):
    """Creates a new clip on every invocation for the given parameters"""
    clip_end = int(time.time())
    clip_start = clip_end - 60

    clip_id = f"{clip_start}_{clip_end}"
    mediapackage.create_harvest_job(
        StartTime=str(clip_start),
        EndTime=str(clip_end),
        Id=clip_id,
        OriginEndpointId=CLIPS_ORIGIN_ENDPOINT_ID,
        S3Destination={
            'BucketName': CLIPS_BUCKET,
            'ManifestKey': f"{clip_id}.m3u8",
            'RoleArn': MEDIA_PACKAGE_S3_ROLE_ARN
        },
    )

    return {
        "statusCode": 200,
        "headers": {
            'Content-Type': 'application/json'
        }
    }


def process_harvested_clip(event, context):
    """Processes a harvested clip to make it available for VOD consumption"""
    table = dynamodb.Table(CLIPS_TABLE)

    harvest_job = event['detail']['harvest_job']
    destination_bucket_name = harvest_job['s3_destination']['bucket_name']
    manifest_key = harvest_job['s3_destination']['manifest_key']

    if harvest_job['status'] == "SUCCEEDED":
        asset = mediapackage_vod.create_asset(
            Id=harvest_job['id'],
            PackagingGroupId=PACKAGING_GROUP_ID,
            SourceArn=f"arn:aws:s3:::{destination_bucket_name}/{manifest_key}",
            SourceRoleArn=MEDIA_PACKAGE_S3_ROLE_ARN
        )

        table.put_item(Item={
            "competition": COMPETITION_ID,
            "clip": asset['Id'],
            "meta": {
                "id": asset['Id'],
                "title": f"Clip: ${asset['Id']}"
            },
            "manifests": asset['EgressEndpoints']
        })


def get_all_clips_for_competition(event, context):
    """Gets all clips for a given competition"""
    competition_id = event['pathParameters']['competitionId']
    table = dynamodb.Table(CLIPS_TABLE)

    clips = table.query(
        KeyConditionExpression='competition = :id',
        ExpressionAttributeValues={
            ':id': competition_id
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps(clips.get('Items', []))
    }
