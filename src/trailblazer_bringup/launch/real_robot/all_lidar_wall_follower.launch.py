from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

import os

def launch_setup(context, *args, **kwargs):

    #Directories
    pkg_trailblazer_cloud = get_package_share_directory('trailblazer_cloud')
    pkg_trailblazer_description = get_package_share_directory('trailblazer_description')
    pkg_trailblazer_controller = get_package_share_directory('trailblazer_controller')
    pkg_trailblazer_nav2 = get_package_share_directory('trailblazer_nav2')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    # rsp
    rsp_launch = PathJoinSubstitution(
        [pkg_trailblazer_description, 'launch', 'rsp.launch.py'])
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([rsp_launch]),
        launch_arguments=[
            ('use_sim_time', 'false'),
            ('use_ros2_control', 'true')
        ])
    
    # controllers
    controller_launch_path = PathJoinSubstitution(
        [pkg_trailblazer_controller, 'launch', 'controller.launch.py'])
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([controller_launch_path]))

    lc_mgr_config_path = os.path.join(
        get_package_share_directory('ldlidar_node'),
        'params',
        'lifecycle_mgr.yaml'
    )
    laser_to_link_transform = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'laser_frame', 'ldlidar_base']
    )

    # Lifecycle manager node
    lc_mgr_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager',
        output='screen',
        parameters=[
            # YAML files
            lc_mgr_config_path  # Parameters
        ]
    )

    # Include LDLidar launch
    ldlidar_launch = IncludeLaunchDescription(
        launch_description_source=PythonLaunchDescriptionSource([
            get_package_share_directory('trailblazer_bringup'),
            '/launch/real_robot/ldlidar_bringup.launch.py'
        ]),
        launch_arguments={
            'node_name': 'ldlidar_node'
        }.items()
    )

    rviz_config_path_wall_follower = os.path.join(
        get_package_share_directory('ros2_wall_follower'), 'rviz', 'wall_follower.rviz'
    )

    rviz_launch_wall_follower = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('trailblazer_rviz'), 'launch', 'rviz.launch.py')
        ),
        launch_arguments={'rviz_config': rviz_config_path_wall_follower}.items()
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('trailblazer_slam'), 'launch', 'slam.launch.py')
        )
    )

    wall_follower = Node(
        package="ros2_wall_follower",
        executable="wall_follower.py", # py version
        name="wall_follower",
        output="screen",
        emulate_tty=True,
        remappings=[
            ('/scan', '/ldlidar_node/scan'),
            ('/cmd_vel', '/cmd_vel_nav')
        ]
    )

    return [
        rsp,
        controller_launch,
        laser_to_link_transform,
        lc_mgr_node,
        ldlidar_launch,
        #rviz_launch_wall_follower,
        #slam_launch,
        wall_follower,
    ]

def generate_launch_description():
    return LaunchDescription([
        
        # Launch arguments
        DeclareLaunchArgument(
            'localization', default_value='false',
            description='Launch in localization mode.'),
        OpaqueFunction(function=launch_setup)
    ])