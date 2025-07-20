cmake_minimum_required(VERSION 3.16)
project(trailblazer_controller LANGUAGES CXX)

if(CMAKE_CXX_COMPILER_ID MATCHES "(GNU|Clang)")
  add_compile_options(-Wall -Wextra)
endif()

# set the same behavior for windows as it is on linux
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

# find dependencies
set(THIS_PACKAGE_INCLUDE_DEPENDS
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
)

# find dependencies
find_package(backward_ros REQUIRED)
find_package(ament_cmake REQUIRED)
foreach(Dependency IN ITEMS ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

## COMPILE
add_library(
  trailblazer_controller
  SHARED
  hardware/trailblazer_system.cpp
)
target_compile_features(trailblazer_controller PUBLIC cxx_std_17)
target_include_directories(trailblazer_controller PUBLIC
$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/hardware/include>
$<INSTALL_INTERFACE:include/trailblazer_controller>
)
ament_target_dependencies(
  trailblazer_controller PUBLIC
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

# Export hardware plugins
pluginlib_export_plugin_description_file(hardware_interface trailblazer_controller.xml)

# INSTALL
install(
  DIRECTORY hardware/include/
  DESTINATION include/trailblazer_controller
)
install(
  DIRECTORY launch config
  DESTINATION share/trailblazer_controller
)

install(TARGETS trailblazer_controller
  EXPORT trailblazer_controller
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

## EXPORTS
ament_export_targets(trailblazer_controller HAS_LIBRARY_TARGET)
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()