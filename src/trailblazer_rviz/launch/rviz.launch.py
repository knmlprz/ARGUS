import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # Get package path
    pkg_path = get_package_share_directory('trailblazer_rviz')
    rviz_config_file = LaunchConfiguration('rviz_config')

    # Declare RViz configuration argument
    declare_rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=PathJoinSubstitution([pkg_path, 'config', 'urdf_model.rviz']),
        description='Path to RViz configuration file'
    )

    node_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file]
    )

    # loads the robot model
    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([get_package_share_directory('trailblazer_description'), 'launch', 'rsp.launch.py'])
        )
    )

    return LaunchDescription([
        declare_rviz_config_arg,
        node_rviz,
        description_launch
    ])