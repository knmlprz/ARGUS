import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    fake_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
    )
    # Environment variables
    set_env_vars = [
        SetEnvironmentVariable('RCUTILS_COLORIZED_OUTPUT', '1'),
    ]

    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('trailblazer_description'), 'launch', 'rsp.launch.py'
        )]), launch_arguments={'use_sim_time': 'true', 'use_ros2_control': 'false'}.items()
    )

    # World configuration
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(
            get_package_share_directory('trailblazer_gazebo'),
            'worlds',
            'office.world'
        ),
        description='Path to world file to load in Gazebo'
    )

    # Gazebo configuration
    gazebo_params_file = os.path.join(
        get_package_share_directory('trailblazer_gazebo'),
        'config',
        'gazebo_params.yaml'
    )

    # Gazebo launch with world file
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
        launch_arguments={
            'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file,
            'world': LaunchConfiguration('world')
        }.items()
    )

    # Spawn entity
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'rover_legendary'],
        output='screen'
    )

    # Joystick control
    joy_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('trailblazer_joystick'), 'launch', 'joy_control.launch.py')
        ),
        launch_arguments={
            'cmd_vel_topic': '/cmd_vel'
        }.items()
    )

    # RViz configuration
    rviz_config_path = os.path.join(
        get_package_share_directory('trailblazer_rviz'), 'config', 'simulation.rviz'
    )
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('trailblazer_rviz'), 'launch', 'rviz.launch.py')
        ),
        launch_arguments={'rviz_config': rviz_config_path}.items()
    )

    # RTAB-Map and Navigation arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    localization = LaunchConfiguration('localization', default='false')

    # RTAB-Map parameters
    parameters = {
        'frame_id': 'base_footprint',
        'use_sim_time': use_sim_time,
        'subscribe_depth': True,
        'use_action_for_goal': True,
        'Reg/Force3DoF': 'true',
        'Grid/RayTracing': 'true',
        'Grid/3D': 'false',
        'Grid/RangeMax': '3',
        'Grid/NormalsSegmentation': 'false',
        'Grid/MaxGroundHeight': '0.05',
        'Grid/MaxObstacleHeight': '0.4',
        'Optimizer/GravitySigma': '0'
    }

    # RTAB-Map remappings (adjust these to match your robot's topics)
    remappings = [
        ('rgb/image', '/camera/image_raw'),
        ('rgb/camera_info', '/camera/camera_info'),
        ('depth/image', '/camera/depth/image_raw'),
        ('odom', '/odom')
    ]

    # Nav2 configuration
    nav2_params_file = PathJoinSubstitution(
        [FindPackageShare('trailblazer_nav2'), 'config', 'rgbd_nav2_params.yaml']
    )

    # Nav2 launch
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': nav2_params_file
        }.items()
    )

    return LaunchDescription(set_env_vars + [
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulation (Gazebo) clock if true'),
        DeclareLaunchArgument(
            'localization', default_value='false',
            description='Launch in localization mode.'),
        world_arg,

        # Core systems
        rsp,
        gazebo,
        spawn_entity,
        joy_control_launch,

        # RTAB-Map nodes
        # SLAM mode:
        Node(
            condition=UnlessCondition(localization),
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=[parameters],
            remappings=remappings,
            arguments=['-d']),  # This will delete the previous database (~/.ros/rtabmap.db)

        # Localization mode:
        Node(
            condition=IfCondition(localization),
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=[parameters,
                        {'Mem/IncrementalMemory': 'False',
                         'Mem/InitWMWithAllNodes': 'True'}],
            remappings=remappings),

        Node(
            package='rtabmap_viz', executable='rtabmap_viz', output='screen',
            parameters=[parameters],
            remappings=remappings),

        # Obstacle detection for Nav2
        Node(
            package='rtabmap_util', executable='point_cloud_xyz', output='screen',
            parameters=[{'decimation': 2,
                         'max_depth': 3.0,
                         'voxel_size': 0.02}],
            remappings=[('depth/image', '/camera/depth/image_raw'),
                        ('depth/camera_info', '/camera/camera_info'),
                        ('cloud', '/camera/cloud')]),

        Node(
            package='rtabmap_util', executable='obstacles_detection', output='screen',
            parameters=[parameters],
            remappings=[('cloud', '/camera/cloud'),
                        ('obstacles', '/camera/obstacles'),
                        ('ground', '/camera/ground')]),

        # Navigation
        nav2_launch,
        rviz_launch
    ])