# CMakeLists.txt file for larbatch

#  This simply copies files into an install directory - there is no build

cmake_minimum_required(VERSION 3.19 FATAL_ERROR)

project(larbatch VERSION 01.56.02 LANGUAGES NONE)

# cetbuildtools contains our cmake modules
set( CETBUILDTOOLS_VERSION $ENV{CETBUILDTOOLS_VERSION} )
if( NOT CETBUILDTOOLS_VERSION )
  message( FATAL_ERROR "ERROR: setup cetbuildtools to get the cmake modules" )
endif()
set( CMAKE_MODULE_PATH $ENV{CETBUILDTOOLS_DIR}/Modules ${CMAKE_MODULE_PATH} )

include(CetCMakeEnv)

# larbatch has no architecture dependence
cet_cmake_env( noarch )

# Make sure cetbuildtools is set up (version is minimum)
find_ups_product(cetbuildtools v4_09_00)

# source code
add_subdirectory(ups)
add_subdirectory(scripts)
add_subdirectory(python)

# packaging utility
include(UseCPack)
