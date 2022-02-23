# CMakeLists.txt file for larbatch

#  This simply copies files into an install directory - there is no build

cmake_minimum_required(VERSION 3.20 FATAL_ERROR)
# cmake_policy(VERSION 3.19) ### MIGRATE-ACTION-COMPATIBILITY (migrate-3.05.04) - Uncomment to preseve compatibility with older CMake versions

find_package(cetmodules REQUIRED)
project(larbatch VERSION 01.56.02 LANGUAGES NONE)

# cetbuildtools contains our cmake modules
set( CETBUILDTOOLS_VERSION $ENV{CETBUILDTOOLS_VERSION} )
if( NOT CETBUILDTOOLS_VERSION )
  message( FATAL_ERROR "ERROR: setup cetbuildtools to get the cmake modules" )
endif()
set( CMAKE_MODULE_PATH $ENV{CETBUILDTOOLS_DIR}/Modules ${CMAKE_MODULE_PATH} ) ### MIGRATE-ACTION-RECOMMENDED (migrate-3.05.04) - prefer find_package() to find external CMake modules

include(CetCMakeEnv)

# larbatch has no architecture dependence
cet_cmake_env( noarch )

# Make sure cetbuildtools is set up (version is minimum)

# source code
add_subdirectory(scripts)
add_subdirectory(python)

# packaging utility
#include(UseCPack)
cet_cmake_config(NO_CMAKE_CONFIG)
