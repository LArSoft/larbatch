# CMakeLists.txt file for larbatch

#  This simply copies files into an install directory - there is no build

cmake_minimum_required(VERSION 3.20 FATAL_ERROR)

find_package(cetmodules REQUIRED)
project(larbatch VERSION 01.56.02 LANGUAGES NONE)

include(CetCMakeEnv)

# larbatch has no architecture dependence
cet_cmake_env( noarch )

# Make sure cetbuildtools is set up (version is minimum)

# source code
add_subdirectory(scripts)
add_subdirectory(python)

cet_cmake_config(NO_CMAKE_CONFIG)
