```bash
ros2 launch trailblazer_bringup camera_robot.launch.py 
ros2 launch trailblazer_nav2 dual_ekf_navsat.launch.py 
ros2 topic pub --rate 10 /gps/fix sensor_msgs/NavSatFix "{
  header: { stamp: { sec: $(date +%s), nanosec: 0 }, frame_id: 'base_link' },
  latitude: 0.0411,
  longitude: 0.0001,
  altitude: 0.0,
  status: { status: 1, service: 1 }
}"
ros2 run trailblazer_nav2 logged_waypoint_follower 

```

# new version
```bash
ros2 launch trailblazer_bringup camera_robot.launch.py 
ros2 launch trailblazer_bringup all.launch.py 
ros2 launch trailblazer_nav2 dual_ekf_navsat.launch.py 
ros2 run trailblazer_gps rtk_gps --ros-args --param port:=/dev/ttyUSB0
sudo docker run -p 8080:8080 -d -t -v ~/mapproxy:/mapproxy danielsnider/mapproxy
ros2 launch trailblazer_nav2 mapviz.launch.py
ros2 topic echo /diff_drive_controller/cmd_vel 
ros2 topic echo /diff_drive_controller/cmd_vel geometry_msgs/msg/Twist 
ros2 run trailblazer_nav2 interactive_waypoint_follower 
ros2 run trailblazer_nav2 logged_waypoint_follower 

```

# actual version
```bash
ros2 topic pub /gps/fix sensor_msgs/msg/NavSatFix '{header: {frame_id: "map"}, latitude: 51.1079, longitude: 17.0385, altitude: 120.0, position_covariance_type: 0}' 

```
```bash
ros2 launch trailblazer_bringup all.launch.py 
ros2 run trailblazer_gps rtk_gps --ros-args --param port:=/dev/ttyUSB0
sudo docker run -p 8080:8080 -d -t -v ~/mapproxy:/mapproxy danielsnider/mapproxy
ros2 launch trailblazer_nav2 mapviz.launch.py
ros2 topic echo /diff_drive_controller/cmd_vel geometry_msgs/msg/Twist 
ros2 run trailblazer_nav2 interactive_waypoint_follower 
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_drive_controller/cmd_vel --param stamped:=true
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/cmd_vel_nav
```

# to install additionally
```bash
sudo apt install ros-humble-rqt-tf-tree 
sudo apt install ros-humble-nav2-bringup
```

# fast start

```bash
ros2 launch trailblazer_bringup all.launch.py 
ros2 launch trailblazer_bringup trailblazer_viz.launch.py 
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/cmd_vel_nav
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888

```

# test urdf

### with gui

```bash
ros2 launch trailblazer_bringup urdf_robot.launch.py
```

### without gui
```bash
ros2 launch trailblazer_bringup urdf_robot_no_viz.launch.py
```