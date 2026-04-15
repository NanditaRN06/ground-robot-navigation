cmake_minimum_required(VERSION 3.8)
project(robot_navigation)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  scripts/send_goal.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY config launch maps scripts
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
