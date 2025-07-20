# TrailblazerML ROS2 Project

This repository contains a ROS2-based project using the `humble` distribution. The project integrates simulation, visualization, teleoperation, and machine learning for autonomous robot navigation and control.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
   - [Install ROS2 Humble](#install-ros2-humble)
   - [Setup the Workspace](#setup-the-workspace)
3. [Running the Project](#running-the-project)
   - [Launching Simulation](#launching-simulation)
   - [Teleoperation](#teleoperation)
4. [Project Structure](#project-structure)

---

## Prerequisites
Ensure the following are installed on your system:
- Ubuntu 22.04
- Python 3.10+
- [ROS2 Humble](https://docs.ros.org/en/humble/index.html)
- `colcon` build tools
- Gazebo simulation environment

---

## Installation

### Install ROS2 Humble
Follow the official [ROS2 Humble installation guide](https://docs.ros.org/en/humble/Installation.html).

### Setup the Workspace
1. Clone this repository:
    ```bash
    git clone https://github.com/knmlprz/TrailblazerML.git
    cd TrailblazerML
    ```
2. Install dependencies:
    ```bash
    sudo apt update && sudo apt install -y \
      python3-colcon-common-extensions \
      ros-humble-gazebo-ros-pkgs \
      ros-humble-ros2-control \
      ros-humble-ros2-controllers \
      ros-humble-gazebo-ros2-control \
      ros-humble-position-controllers \
      ros-humble-xacro \
      joystick \
      jstest-gtk \
      evtest \
      ros-humble-twist-mux \
      ros-humble-rviz2
    ```
3. To store your model create a folder in the root directory of the project:
    ```bash
    mkdir ~/.gazebo/models
    ```
4. Build the workspace:
    ```bash
    colcon build --symlink-install
    source install/setup.bash
    ```

---

## Running the Project

## Add meshes to Gazebo
1. Go to gazebo folder:
```bash
   cd ~/.gazebo/models
   mkdir gazebo_viz
```
2. Add meshes:
```bash
  cp -r <Path_to_project>/TrailblazerML/src/gazebo_viz/meshes ./gazebo_viz
```

### Launching Simulation
1. Launch the Gazebo simulator with the robot:
    ```bash
    ros2 launch gazebo_viz launch_sim.launch.py
    ```
2. To visualize the robot in RViz:
    ```bash
    ros2 launch gazebo_viz rsp.launch.py
    ```

### Teleoperation
To control the robot manually:
1. Connect your joystick or set up keyboard teleoperation.
2. Launch the teleoperation node:
    ```bash
    ros2 launch rover_teleop_twist_joy teleop_twist_launch.py
    ```
### Test gazebo wheels 

   ```bash
    ros2 topic pub /diff_drive_controller_right/cmd_vel_unstamped geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
    ros2 topic pub /diff_drive_controller_left/cmd_vel_unstamped geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
   ```
   
---

## Project Structure
```plaintext
src
├── gazebo_viz                 # Core visualization and simulation package
│   ├── config                 # Configuration files (RViz, controllers, etc.)
│   ├── description            # Robot URDF and XACRO files
│   ├── launch                 # Launch files for simulation
│   ├── meshes                 # Robot 3D models
│   ├── worlds                 # Gazebo simulation worlds
├── rover_teleop_twist_joy     # Teleoperation package
│   ├── launch                 # Launch files for teleop
│   ├── rover_teleop_twist_joy # Teleop control scripts
├── trailblazerml              # Main robot dir
