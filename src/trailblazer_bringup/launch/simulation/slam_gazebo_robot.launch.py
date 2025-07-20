import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # Ścieżki do plików konfiguracyjnych
    pkg_nav2 = get_package_share_directory('trailblazer_nav2')
    pkg_rviz = get_package_share_directory('trailblazer_rviz')

    navsat_config_path = PathJoinSubstitution([
        pkg_nav2, 'config', 'navsat.yaml'
    ])

    ekf_config_path = PathJoinSubstitution([
        pkg_nav2, 'config', 'ekf_gazebo.yaml'
    ])

    rviz_config_path = PathJoinSubstitution([
        pkg_rviz, 'config', 'slam.rviz'
    ])

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    gazebo_params_file = os.path.join(get_package_share_directory("trailblazer_gazebo"), 'config', 'gazebo_params.yaml')
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time'
        ),

        # Include the robot_state_publisher
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory("trailblazer_description"), 'launch', 'rsp.launch.py'
            )]), launch_arguments={'use_sim_time': 'true', 'use_ros2_control': 'false'}.items()
        ),

        # Include Gazebo launch file
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
        ),

        # Spawn the robot in Gazebo
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', 'legendary_rover',
                '-topic', 'robot_description',
            ],
            output='screen'
        ),

        # # # EKF
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config_path],

        ),

        # # # NavSat
        Node(
            package='robot_localization',
            executable='navsat_transform_node',
            name='navsat_transform_node',
            parameters=[navsat_config_path],
            arguments=['--ros-args', '--log-level', 'WARN'],
            remappings=[
                ('imu/data', '/imu/data'),
                ('gps/fix', '/gps/fix'),
                ('odometry/gps', '/odometry/gps')
            ]
        ),

        # # # SLAM
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('trailblazer_slam'), 'launch', 'slam.launch.py')
            )
        ),

        # Joystick
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    get_package_share_directory('trailblazer_joystick'),
                    'launch',
                    'joy_control.launch.py'
                ])
            ]),
            launch_arguments={
                'cmd_vel_topic': '/cmd_vel',
                'use_sim_time': use_sim_time
            }.items()
        ),

        # RViz
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    get_package_share_directory('trailblazer_rviz'),
                    'launch',
                    'rviz.launch.py'
                ])
            ]),
            launch_arguments={
                'rviz_config': rviz_config_path,
                'use_sim_time': use_sim_time
            }.items()
        )
    ])