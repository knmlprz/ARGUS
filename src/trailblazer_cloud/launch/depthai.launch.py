# Source: https://github.com/introlab/rtabmap_ros/blob/ros2/rtabmap_demos/launch/turtlebot3/turtlebot3_rgbd.launch.py
# Requirements:
#   A OAK-D camera
#   Install depthai-ros package (https://github.com/luxonis/depthai-ros)
# Example:
#   $ ros2 launch trailblazer_cloud depthai.launch.py camera_model:=OAK-D

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, SetEnvironmentVariable, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    # Definiowanie argumentu launch dla pliku parametrów
    declared_arguments = [
        DeclareLaunchArgument("name", default_value="oak"),
        DeclareLaunchArgument("mxId", default_value="x"),
    ]

    return LaunchDescription(
        declared_arguments +[OpaqueFunction(function=launch_setup)]
    )

def launch_setup(context, *args, **kwargs):
    # Launch camera driver z parametrami z YAML
    name = LaunchConfiguration("name").perform(context)
    # Parametry dla RTAB-Map
    parameters = [{
        'frame_id': 'base_link', #base_link
        'subscribe_rgbd': True,
        'subscribe_odom_info': True,
        #'approx_sync': False,
        #'approx_sync_max_interval': "0.1",
        'wait_imu_to_init': True,
        'use_action_for_goal': True,
        'Reg/Force3DoF': 'true',
        'Odom/ResetCountdown': '1', #def 0
        'guess_frame_id': 'odom',

        # 'Grid/RayTracing': 'true',  # Fill empty space
        # 'Grid/NormalsSegmentation': 'false',  # Use passthrough filter to detect obstacles
        # 'Grid/MaxGroundHeight': '0.5',  # All points above 5 cm are obstacles
        # 'Grid/MaxObstacleHeight': '2.0',  # All points over 1 meter are ignored
        # 'Optimizer/GravitySigma': '0',  # Disable imu constraints (we are already in 2D)
        # 'Odom/Strategy': '0', #def 0
        # 'Vis/MaxFeatures': '3000', #def 1000
        # 'GFTT/MinDistance': '7', #def 7
        # 'Grid/NoiseFilteringMinNeighbors': '5', #def 5
        # 'Grid/NoiseFilteringRadius': '0.1', #def 0
        #'Grid/MinClusterSize': '20', #def 10

        'Grid/3D': 'false',  # Use 2D occupancy

        'wait_for_transform': 0.5,
        # RTAB-Map's parameters should be strings
        'Grid/DepthDecimation': '1',
        'Grid/RangeMax': '2',
        'GridGlobal/MinSize': '20',
        'Grid/MinClusterSize': '20',
        'Grid/MaxObstacleHeight': '5',
        'Grid/MaxGroundHeight': '0.9',
        'Grid/RayTracing': 'true',  # Fill empty space
        'Grid/NormalsSegmentation': 'true',  # Use passthrough filter to detect obstacles
        'Grid/NoiseFilteringMinNeighbors': '5', #def 5
        'Optimizer/GravitySigma':'0',
        #'Grid/NormalK': '200',
        #'Grid/NoiseFilteringRadius': '0.1', #def 0

        #'Rtabmap/StartNewMapOnLoopClosure': 'true', #def false (set to true for navigating)
        # 'Grid/RangeMax': '3',
        # 'Vis/CorType': '1', #def 0
        #'OdomF2M/MaxSize': '3000', #def 2000
        #'RGBD/StartAtOrigin': 'true', #def false
        #'Odom/FilteringStrategy': '0', #def 0 (1=kalman)
        #'guess_frame_id': 'odom',
        #'Kp/RoiRatios': '0.0 0.0 0.4 0.0',
    }]

    remappings = [('imu', '/imu/data'),
                  ('odom', 'vo')
                  ]

    return [
    IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('trailblazer_cloud'), 'launch'),
            '/stereo_inertial_node.launch.py']),
            launch_arguments={
                'name': name,
                'depth_aligned': 'false',
                'enableDotProjector': 'true',
                'enableFloodLight': 'true',
                'monoResolution': '400p',
                #'mxId': '18443010814D3AF500',
                # 'LRchecktresh': '5',
                # 'angularVelCovariance': '0.0',
                # 'confidence': '200',
                # 'detectionClassesCount': '80',
                # 'dotProjectorIntensity': '0.5',
                # 'enableRosBaseTimeUpdate': 'false',
                # 'enableSpatialDetection': 'true',
                # 'expTime': '20000',
                # 'extended': 'false',
                # 'floodLightIntensity': '0.5',
                # 'imuMode': '1',
                # 'linearAccelCovariance': '0.0',
                # 'lrcheck': 'true',
                # 'manualExposure': 'false',
                # 'mode': 'depth',
                # 'mxId': 'x',
                #'nnName': 'yolov4_tiny_coco_416x416_openvino_2021.4_6shave_bgr.blob',
                # 'poeMode': 'false',
                # 'previewHeight': '416',
                # 'previewWidth': '416',
                # 'rectify': 'true',
                # 'resourceBaseFolder': 'x',
                # 'rgbResolution': '1080p',
                # 'rgbScaleDinominator': '3',
                # 'rgbScaleNumerator': '2',
                # 'sensIso': '800',
                # 'stereo_fps': '30', #def 30
                # 'subpixel': 'true',
                # 'syncNN': 'true',
                # 'tf_prefix': 'oak',
                # 'usb2Mode': 'false',
                # 'use_sim_time': 'false',
            }.items(),
    ),

    # Sync RGB/depth/camera_info together
    Node(
        package='rtabmap_sync',
        executable='rgbd_sync',
        output='screen',
        parameters=parameters,
        remappings=[
            ('rgb/image', '/color/image' ),
            ('rgb/camera_info', '/color/camera_info' ),
            ('depth/image', '/stereo/depth')
        ],
        condition=IfCondition(LaunchConfiguration('depth_aligned'))
    ),

    Node(
        package='rtabmap_sync',
        executable='rgbd_sync',
        output='screen',
        parameters=parameters,
        remappings=[
            ('rgb/image', '/right/image_rect'),
            ('rgb/camera_info', '/right/camera_info'),
            ('depth/image', '/stereo/depth')
        ],
        condition=UnlessCondition(LaunchConfiguration('depth_aligned'))
    ),

    # Compute quaternion of the IMU
    Node(
        package='imu_filter_madgwick', executable='imu_filter_madgwick_node', output='screen',
        parameters=[{'use_mag': True,
                        'world_frame': 'enu',
                        'publish_tf': False,
                        #'fixed_frame': 'vo',
                        }],
        remappings=[
            ('imu/data_raw', name + '/imu'),
            ('imu/mag', name + '/magnetic_field')
            ]),

    # Visual odometry
    Node(
        package='rtabmap_odom', executable='rgbd_odometry', output='screen',
        parameters=parameters + [{
            'publish_tf': True,
            #'guess_frame_id': 'odom',
            'odom_frame_id': 'vo',
            #'approx_sync': True,
            #'approx_sync_max_interval': 0.1,  # Maksymalny odstęp czasowy: 0.1 sekundy
            }],
        remappings=remappings),

    # VSLAM
    Node(
        package='rtabmap_slam', executable='rtabmap', output='screen',
        parameters=parameters,
        remappings=remappings + [
                        # ('cloud_obstacles', '/camera/obstacles'),
                        # ('cloud_ground', '/camera/ground')
                        ],
        arguments=['-d'],
        
        ),

    # Node(
    #     package='rtabmap_slam', executable='rtabmap', output='screen',
    #     parameters=parameters + [ 
    #         {'Mem/IncrementalMemory':'False',
    #         'Mem/InitWMWithAllNodes':'True'}],
    #     remappings=remappings),

    # Visualization
    # Node(
    #     package='rtabmap_viz', executable='rtabmap_viz', output='screen',
    #     parameters=parameters,
    #     remappings=remappings),

    Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'oak_imu_frame']
    ),
    Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'vo', 'base_link']
    ),
    Node(
            package='rtabmap_util', executable='point_cloud_xyz', output='screen',
            parameters=[{'decimation': 2,
                         'max_depth': 3.0,
                         'voxel_size': 0.02,
                         #'roi_ratios': "0.0 0.0 0.4 0.0"
                         }],
            remappings=[('depth/image', '/stereo/depth'),
                        ('depth/camera_info', '/stereo/camera_info'),
                        ('cloud', '/camera/cloud')]),
    Node(
            package='rtabmap_util', executable='obstacles_detection', output='screen',
            parameters=parameters,
            remappings=[('cloud', '/camera/cloud'),
                        ('obstacles', '/camera/obstacles'),
                        ('ground', '/camera/ground')]),
    ]