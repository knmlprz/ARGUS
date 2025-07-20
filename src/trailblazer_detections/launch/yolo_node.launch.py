from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='trailblazer_detections',
            executable='yolo_node',
            name='yolo_detection_node',
            output='screen',
        )
    ])
