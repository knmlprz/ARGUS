import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
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
    )

    # Spawn the robot in Gazebo
    spawn_entity = Node(
        package='gazebo_ros', executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'my_bot'],
        output='screen'
    )

    # Path to the xacro file
    pkg_path = os.path.join(get_package_share_directory('trailblazer_description'))
    xacro_file = os.path.join(pkg_path, 'urdf', 'rover.urdf.xacro')

    # Generate robot_description from the xacro file
    robot_description_config = Command(['xacro ', xacro_file])
    params = {'robot_description': robot_description_config}

    # Load and start the controller_manager node
    load_controllers = Node(
        package='controller_manager',
        executable='ros2_control_node',
        output='screen',
        parameters=[params],
    )

    # Start the diff_drive_controller using the spawner
    spawn_diff_drive_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller'],
        output='screen',
    )

    return LaunchDescription([
        rsp,
        gazebo,
        spawn_entity,
        load_controllers,
        spawn_diff_drive_controller,
    ])