cmake_minimum_required(VERSION 3.8)
project(dome_control)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Announcement.msg"
  "msg/Telemetry.msg"
  DEPENDENCIES builtin_interfaces std_msgs
)

install(DIRECTORY dome_control
  DESTINATION ${PYTHON_INSTALL_DIR}
  FILES_MATCHING PATTERN "*.py"
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/behavior_manager
  scripts/describe_scene_stub
  scripts/run
  scripts/speech_output
  scripts/voice_input
  scripts/spin_survey_node
  scripts/telemetry_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
