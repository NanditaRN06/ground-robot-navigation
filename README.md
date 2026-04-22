# MAR Project – Ground Robot Autonomous Indoor Navigation
## ROS 2 Jazzy + Gazebo Harmonic

A complete simulation stack for an autonomous indoor ground robot.  
The robot can **map**, **localize**, **plan paths**, **avoid obstacles**, and **autonomously navigate** to goal positions.

---

## Project Architecture

```
ros2_ws/
├── src/
│   ├── robot_description/       # URDF/XACRO model + Gazebo launch + bridge
│   │   ├── urdf/robot.xacro     # Differential drive robot with LiDAR + IMU
│   │   ├── launch/robot_gazebo.launch.py
│   │   └── config/
│   │       ├── gz_bridge.yaml   # Gazebo ↔ ROS 2 topic bridge
│   │       ├── slam.rviz        # RViz2 config for SLAM phase
│   │       └── robot.rviz       # RViz2 config for navigation phase
│   │
│   ├── robot_navigation/        # SLAM + Nav2 configuration
│   │   ├── config/
│   │   │   ├── slam_toolbox_params.yaml
│   │   │   └── nav2_params.yaml
│   │   ├── launch/
│   │   │   ├── slam_launch.py        # Online async SLAM (LifecycleNode)
│   │   │   └── navigation_launch.py  # Nav2 + AMCL localization
│   │   └── maps/                     # Saved maps (after SLAM phase)
│   │
│   └── robot_bringup/           # Umbrella launchers + goal sender scripts
│       ├── launch/
│       │   ├── slam_bringup.launch.py   # Phase 1: Simulation + SLAM
│       │   └── nav_bringup.launch.py    # Phase 2: Simulation + Nav2
│       └── scripts/
│           ├── send_goal.py             # Single goal sender
│           └── waypoint_navigator.py   # Multi-room waypoint demo
│
└── worlds/
    ├── house.sdf    # Indoor house world (living room + kitchen + bedroom)
    └── office.sdf   # Open-plan office world
```

---

## Robot Specifications

| Feature | Value |
|---|---|
| Type | Differential drive |
| Chassis | 0.40 m × 0.30 m × 0.12 m |
| Wheel separation | 0.34 m |
| Wheel radius | 0.06 m |
| Max velocity | 0.5 m/s linear, 1.0 rad/s angular |
| LiDAR | 360° GPU LiDAR, 5 Hz, range 0.12–10.0 m |
| IMU | 100 Hz, Gaussian noise |

---

## System Architecture

```
Gazebo Harmonic
    │
    ▼
Robot Model (URDF/XACRO)
    │  LiDAR /scan  │  /odom  │  /imu  │  /tf  │  /clock
    ▼
ros_gz_bridge  ←──────────────→  ROS 2 Topics
    │
    ▼
ROS 2 Nodes
 ├── static_transform_publisher  (immediate fixed TF: base_footprint→lidar_link)
 ├── robot_state_publisher       (full TF tree from URDF)
 ├── joint_state_publisher       (wheel joint positions for visualization)
 ├── slam_toolbox                (LifecycleNode: builds occupancy grid map)
 ├── AMCL                        (Localization on saved map)
 ├── Nav2 planner_server         (Global path: A* via NavFn)
 ├── Nav2 controller_server      (Local path: DWB controller)
 ├── Nav2 behavior_server        (Recovery: spin, backup)
 └── Nav2 bt_navigator           (Behavior Tree orchestration)
    │
    ▼
/cmd_vel  →  ros_gz_bridge  →  Gazebo DiffDrive plugin  →  Robot Motion
```

---

## Prerequisites

Install on Ubuntu 24.04 / WSL2 with ROS 2 Jazzy:

```bash
# Core ROS 2 Jazzy
sudo apt install ros-jazzy-desktop

# Gazebo Harmonic + ROS-Gazebo bridge
sudo apt install ros-jazzy-ros-gz

# SLAM Toolbox
sudo apt install ros-jazzy-slam-toolbox

# Nav2 + Collision Monitor
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-nav2-collision-monitor

# Additional tools
sudo apt install ros-jazzy-xacro
sudo apt install ros-jazzy-robot-state-publisher
sudo apt install ros-jazzy-joint-state-publisher
sudo apt install ros-jazzy-teleop-twist-keyboard
sudo apt install ros-jazzy-tf-transformations
sudo apt install ros-jazzy-nav2-rviz-plugins

pip install catkin_pkg empy lark transforms3d
```

---

## Core Features

- **Autonomous Navigation**: Full Nav2 stack integration (A* Global Planner, DWB Local Planner).
- **Emergency Safety**: `nav2_collision_monitor` provides a "slowdown" and "stop" zone around the robot to prevent collisions even during autonomous flight.
- **Automated Waypoint Tour**: Custom Python navigator that executes a pre-planned tour of the house (Living Room → Kitchen → Bedroom).
- **Gazebo Harmonic Integration**: High-fidelity simulation with GPU-accelerated LiDAR and IMU noise modeling.
- **Dual-Phase Logic**: Unified launch system for Phase 1 (Mapping) and Phase 2 (Navigation).

> **Build environment**: Always build in a plain terminal with only
> `source /opt/ros/jazzy/setup.bash` — never inside a Python venv.
> Run the simulation from any terminal after sourcing `install/setup.bash`.

---

## Step-by-Step Workflow

### Step 1 – Build the Workspace

```bash
# Source ROS 2 (NOT inside a venv)
source /opt/ros/jazzy/setup.bash

cd ground-robot-navigation  # Stay in this path for the rest of the project
colcon build --symlink-install
source install/setup.bash
```

---

### Step 2 – Phase 1: SLAM (Build the Map)

Open **4 separate terminals**, all with `source install/setup.bash`.

**Terminal 1 — Gazebo + SLAM** (no RViz, reduces GPU load):
```bash
source install/setup.bash
ros2 launch robot_bringup slam_bringup.launch.py world:=house # or world:=office
```

Wait ~5 seconds for Gazebo to fully load and SLAM to activate, then:

**Terminal 2 — RViz2** (launch after Gazebo is up):
```bash
source install/setup.bash
rviz2 -d src/robot_description/config/slam.rviz
```

**Terminal 3 — Teleop** (drive the robot to build the map):
```bash
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/cmd_vel
```

| Key | Action |
|-----|--------|
| `i` | Forward |
| `,` | Backward |
| `j` | Rotate left |
| `l` | Rotate right |
| `k` | Stop |
| `u` / `o` | Forward + turn |

Drive around all rooms until the occupancy grid fills in.

**Terminal 4 — Save the map** (when mapping is complete):
```bash
source install/setup.bash
mkdir src/robot_navigation/maps # Create the folder if it does not exist
ros2 run nav2_map_server map_saver_cli \
  -f src/robot_navigation/maps/<file_name> \
  --ros-args -p use_sim_time:=true
```

Saves `src/robot_navigation/maps/<file_name>.yaml` + `src/robot_navigation/maps/<file_name>.pgm`.

---

### Step 3 – Phase 2: Autonomous Navigation

> Make sure to have stopped the previous terminals before running this step.

**Terminal 1 — Gazebo + Nav2** (uses the saved map):
```bash
source install/setup.bash
ros2 launch robot_bringup nav_bringup.launch.py \
  world:=<world_name> \
  map:=src/robot_navigation/maps/<map_name>.yaml
```

**Terminal 2 — RViz2**:
```bash
source install/setup.bash
rviz2 -d src/robot_description/config/robot.rviz
```

In RViz2:
1. Click **"2D Pose Estimate"** → click + drag on the robot's actual position on the map
2. Click **"Nav2 Goal"** → click the destination

---

### **Autonomous Waypoint Tour**

The project includes a custom automation script that drives the robot through a multi-room tour. This starts automatically 30 seconds after `nav_bringup.launch.py`.

To run it manually or restart the tour:
```bash
ros2 run robot_bringup waypoint_navigator.py
```

| Room | Coordinates (x, y) |
|---|---|
| **Living Room** | (3.0, 1.0) |
| **Kitchen** | (3.0, 3.0) |
| **Bedroom** | (1.0, 3.0) |
| **Start/Base** | (1.0, 1.0) |

---

### Step 4 – Send Goals Programmatically

```bash
# Single goal (x=5.0, y=3.0, yaw=0)
ros2 run robot_bringup send_goal.py \
  --ros-args -p x:=<x_coordinate> -p y:=<y_coordinate> -p yaw:=<yaw_orientation_in_radians>

# Multi-room waypoint tour (living room → kitchen → bedroom → start)
ros2 run robot_bringup waypoint_navigator.py
```

---

## Verify SLAM is Working

Run these diagnostics while slam_bringup is active:

```bash
# scan subscription must show count=1 (slam_toolbox subscribed)
ros2 topic info /scan --verbose

# must return True
ros2 param get /slam_toolbox debug_logging

# must show transform values (not "frame does not exist")
ros2 run tf2_ros tf2_echo map odom

# full TF tree
ros2 run tf2_tools view_frames
```

---

## Available Worlds

| World | Description |
|---|---|
| `house` | 10×8 m indoor house: living room, kitchen, bedroom, hallway |
| `office` | 12×10 m open-plan office: cubicles, meeting room, corridor |

---

## Key Topics

| Topic | Type | Direction |
|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | Gazebo → ROS 2 |
| `/odom` | `nav_msgs/Odometry` | Gazebo → ROS 2 |
| `/imu` | `sensor_msgs/Imu` | Gazebo → ROS 2 |
| `/cmd_vel` | `geometry_msgs/Twist` | ROS 2 → Gazebo |
| `/tf` | `tf2_msgs/TFMessage` | Gazebo → ROS 2 |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM → ROS 2 |
| `/plan` | `nav_msgs/Path` | Nav2 → RViz2 |
| `/clock` | `rosgraph_msgs/Clock` | Gazebo → ROS 2 |

---

## Navigation Stack Parameters

- **Global Planner:** NavFn with A* (configurable to Dijkstra)
- **Local Planner:** DWB (Dynamic Window Approach)
- **Localization:** AMCL with differential motion model
- **Recovery:** Spin, BackUp, DriveOnHeading
- **Map Resolution:** 0.05 m/cell
- **Robot Radius:** 0.22 m (inflation: 0.55 m)
- **Max Linear Speed:** 0.5 m/s
- **Max Angular Speed:** 1.0 rad/s

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `frame 'lidar_link' queue is full` in RViz | Wait 10s for startup; static TF publishers fire before Gazebo |
| `Subscription count: 0` on `/scan` | slam_toolbox is a LifecycleNode — bringup auto-activates it |
| `map` frame does not exist | SLAM not yet active; wait for `[LifecycleLaunch] activating` log |
| Robot doesn't move in Gazebo | Check Gazebo isn't paused (▶ button); verify cmd_vel bridge |
| RViz hangs | Launch RViz in a separate terminal, 5s after Gazebo starts |
| `colcon build` fails with catkin_pkg | Build outside virtualenv: `source /opt/ros/jazzy/setup.bash` only |

## Authors

- PES2UG23CS365 - [Nandita R Nadig](https://github.com/NanditaRN06)
- PES2UG23CS913 - [Nandana Mathew](https://github.com/nandana-mathew)
- PES2UG23CS369 - [Naveen S](https://github.com/nh-44)
- PES2UG23CS366 - [Likhith Chandra N S](https://github.com/PES2UG23CS366-NSLC)