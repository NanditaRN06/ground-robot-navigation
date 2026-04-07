# Ground Robot Autonomous Indoor Navigation - Simulation Based

## Authors
- PES2UG23CS366 - [Likhith Chandra N S](https://github.com/PES2UG23CS366-NSLC)
- PES2UG23CS365 - [Nandita R Nadig](https://github.com/NanditaRN06)
- PES2UG23CS369 - [Naveen S](https://github.com/nh-44)
- PES2UG23CS913 - [Nandana Mathew](https://github.com/nandana-mathew)

## Person 2 — SLAM & Localization

Branch: `feat/slam-localization`

### What was added
- SLAM Toolbox mapping parameters for generating a map from `/scan` and `/odom`.
- AMCL localization parameters for publishing `/amcl_pose` against a saved map.
- map_server configuration for serving the saved map as `/map`.
- A dedicated maps note explaining where the generated map files should live.

### Files added for this work
- [src/robot_navigation/config/localization/slam_toolbox_mapping.yaml](src/robot_navigation/config/localization/slam_toolbox_mapping.yaml)
- [src/robot_navigation/config/localization/amcl.yaml](src/robot_navigation/config/localization/amcl.yaml)
- [src/robot_navigation/config/localization/map_server.yaml](src/robot_navigation/config/localization/map_server.yaml)
- [src/robot_navigation/launch/slam_mapping.launch.py](src/robot_navigation/launch/slam_mapping.launch.py)
- [src/robot_navigation/launch/localization.launch.py](src/robot_navigation/launch/localization.launch.py)
- [src/robot_navigation/maps/README.md](src/robot_navigation/maps/README.md)

### Integration contract for the team
- **Input topics expected from Person 1:** `/scan`, `/odom`, and TF between `odom` and `base_link`.
- **Localization output expected by Person 3 and Person 4:** `/map` from map_server and `/amcl_pose` from AMCL.
- **Map file naming convention:** keep the saved map pair in `src/robot_navigation/maps/` using the placeholder name referenced by `map_server.yaml`, or update that YAML to the final map file name when the map is saved.

### Usage notes
- The SLAM config is for map creation runs.
- The AMCL and map_server configs are for localization runs after the map has been saved.
- `use_sim_time` is enabled in all configs so they work with Gazebo-based simulation.

### Suggested workflow
1. Run the robot in simulation and collect `/scan` and `/odom`.
2. Use [src/robot_navigation/launch/slam_mapping.launch.py](src/robot_navigation/launch/slam_mapping.launch.py) or the SLAM Toolbox mapping config to build the map.
3. Save the generated map into `src/robot_navigation/maps/`.
4. Launch [src/robot_navigation/launch/localization.launch.py](src/robot_navigation/launch/localization.launch.py) with the saved map to start map_server and AMCL.

### Team note
These additions do not modify the existing source code. They only provide ROS 2 configuration files and documentation so the other branches can plug them into their bringup and Nav2 launch files without dependency conflicts.
