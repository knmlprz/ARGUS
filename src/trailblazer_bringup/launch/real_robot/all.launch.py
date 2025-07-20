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

    # nav2

    # nav2_launch = PathJoinSubstitution(
    #     [pkg_nav2_bringup, 'launch', 'navigation_launch.py'])
    nav2_launch = PathJoinSubstitution(
        [pkg_trailblazer_nav2, 'launch', 'navigation_launch.py'])
    # nav2_params_file = PathJoinSubstitution(
    #     [FindPackageShare('trailblazer_cloud'), 'params', 'trailblazer_rgbd_nav2_params.yaml']
    # )

    # nav2_params_file = PathJoinSubstitution(
    #     [FindPackageShare('trailblazer_nav2'), 'config', 'trailblazer_rgbd_nav2_params.yaml']
    # )
    nav2_params_file = PathJoinSubstitution(
        [FindPackageShare('trailblazer_cloud'), 'params', 'champ_nav2_params.yaml']
    )
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([nav2_launch]),
        launch_arguments=[
            ('use_sim_time', 'false'),
            ('params_file', nav2_params_file)
        ]
    )

    # rtabmap
    rtabmap_launch = PathJoinSubstitution(
        [pkg_trailblazer_cloud, 'launch', 'depthai.launch.py'])
    rtabmap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([rtabmap_launch]),
        launch_arguments=[
            ('localization', LaunchConfiguration('localization')),
            ('use_sim_time', 'false'),
            ('use_ros2_control', 'true')
        ]
    )

    # navsat
    navsat_launch_path = PathJoinSubstitution(
        [pkg_trailblazer_nav2, 'launch', 'dual_ekf_navsat.launch.py'])
    navsat_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([navsat_launch_path]))
    
    # gps
    gps_node = Node(
        package='trailblazer_gps',
        executable="rtk_gps",
        name='gps_node',
        parameters=[{
            'port': "/dev/ttyUSB0",
        }]
    )
    
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
    
    
    return [
        # Nodes to launch
        nav2,
        rtabmap,
        rsp,
        controller_launch,
        #navsat_launch,
        #gps_node
    ]

def generate_launch_description():
    return LaunchDescription([
        
        # Launch arguments
        DeclareLaunchArgument(
            'localization', default_value='false',
            description='Launch in localization mode.'),
        OpaqueFunction(function=launch_setup)
    ])