"""Creates a Packaging Group for HLS"""
import sys

import boto3

mediapackage_vod = boto3.client('mediapackage-vod')


def create_hls_packaging_group(group_id, hls_packaging_config_id):
    """Creates a Packaging Group for HLS"""
    mediapackage_vod.create_packaging_group(Id=group_id)
    mediapackage_vod.create_packaging_configuration(
        HlsPackage={
            'HlsManifests': [
                {
                    'AdMarkers': 'NONE',
                    'ManifestName': 'index',
                    'ProgramDateTimeIntervalSeconds': 60,
                },
            ],
            'SegmentDurationSeconds': 6,
            'UseAudioRenditionGroup': True
        }
        ,
        Id=hls_packaging_config_id,
        PackagingGroupId=group_id
    )
    print(f"[OK] PACKAGING_GROUP_ID={group_id}")


if __name__ == '__main__':
    create_hls_packaging_group(sys.argv[1], sys.argv[2])
