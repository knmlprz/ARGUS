# Trailblazer Detections

This package provides a ROS 2-based object detection node integrating YOLO and ArUco marker detection. It is designed to work with the DepthAI ROS Driver camera and publish results in a unified format for further processing or visualization (e.g., in RViz2).

> ⚠️ **Important:** To ensure the package runs correctly, you **must create** the directory:
>
> ```
> TrailblazerML/src/trailblazer_detections/models
> ```
>
> and place your YOLO `.pt` model file inside it.

---

## Specified ArUco Markers

* Dictionary: `DICT_4X4_50`
* Marker size: **20x20 cm**

---

## Build

To build the workspace, run:

```sh
cd ~/TrailblazerML
colcon build
```

---

## Dependencies

Make sure to install all required dependencies:

```sh
rosdep update
rosdep install --from-paths src -y --ignore-src
```

---

## Launch

### 1. Launch the DepthAI ROS Driver camera:

```sh
ros2 launch depthai_ros_driver camera.launch.py
```

### 2. Source the environment and launch the detection node:

```sh
source install/setup.bash
ros2 launch trailblazer_detections yolo_node.launch.py
```

---

## Used Topics

### Main Output Topic

Data is published on:

```
/detections
```

The message format is structured as follows:

```yaml
detections:
- type: (aruco | yolo)
  label: <string>
  confidence: <float>
  center:
    x: <float>
    y: <float>
    z: <float>
  width: <float>
  height: <float>
  pose:
    position:
      x: <float>
      y: <float>
      z: <float>
    orientation:
      x: <float>
      y: <float>
      z: <float>
      w: <float>
  distance: <float>
```

### Visualization Topic

For visual inspection in RViz2 or other tools, image overlays are published on:

```
/detections/image
```

---

## Notes

* Ensure that your DepthAI-compatible device is connected and detected properly.
* The detection node combines YOLO object detection and ArUco marker tracking into a single output format for streamlined processing.
