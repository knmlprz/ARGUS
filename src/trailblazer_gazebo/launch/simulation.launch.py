import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='',
        description='Path to world file to load in Gazebo'
    )

    gazebo_params_file = os.path.join(get_package_share_directory("trailblazer_gazebo"), 'config', 'gazebo_params.yaml')

    # Include the robot_state_publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory("trailblazer_description"), 'launch', 'rsp.launch.py'
        )]), launch_arguments={'use_sim_time': 'true', 'use_ros2_control': 'false'}.items()
    )

    # Include Gazebo launch file
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
        launch_arguments={
            'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file,
            'world': LaunchConfiguration('world')
        }.items()
    )

    # Spawn the robot in Gazebo
    spawn_entity = Node(
        package='gazebo_ros', executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'rover_legendary'],
        output='screen'
    )

    # Launch them all!
    return LaunchDescription([
        rsp,
        world_arg,
        gazebo,
        spawn_entity
    ])