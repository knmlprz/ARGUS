from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

import os

def launch_setup(context, *args, **kwargs):

    start_autonomy_service = ExecuteProcess(
        cmd=['ros2', 'service', 'call', '/stop_autonomy', 'std_srvs/srv/Trigger', '{}'],
        output='screen'
    )

    # Dodajemy opóźnienie, aby upewnić się, że węzeł wall_follower jest gotowy
    delayed_start_autonomy = TimerAction(
        period=0.1,  # Opóźnienie 5 sekund
        actions=[start_autonomy_service]
    )

    return [
        delayed_start_autonomy
    ]

def generate_launch_description():
    return LaunchDescription([
        
        # Launch arguments
        DeclareLaunchArgument(
            'localization', default_value='false',
            description='Launch in localization mode.'),
        OpaqueFunction(function=launch_setup)
    ])