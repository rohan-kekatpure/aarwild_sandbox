cmake_minimum_required(VERSION 3.12)

project(OCCMesher)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake ${CMAKE_MODULE_PATH})

# Force C++ 11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
message(STATUS " ${CMAKE_CXX_FLAGS}") 

set(BUILD_SHARED_LIBS ON)
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

add_executable(${PROJECT_NAME} src/main.cpp)

################################
# OCE include and lib location #
################################
if(OCE_HIDE_DEPRECATED)
  message(STATUS "Disabled deprecation warnings for oce")
  add_definitions(-DOCCT_NO_DEPRECATED)
endif(OCE_HIDE_DEPRECATED)

find_package(OpenCASCADE 7.5.0 REQUIRED)

if(OpenCASCADE_FOUND)
  message(STATUS "OpenCASCADE version found: " ${OpenCASCADE_MAJOR_VERSION} "." ${OpenCASCADE_MINOR_VERSION} "." ${OpenCASCADE_MAINTENANCE_VERSION})
  message(STATUS "OpenCASCADE include directory: " ${OpenCASCADE_INCLUDE_DIR})
  message(STATUS "OpenCASCADE binary directory: " ${OpenCASCADE_BINARY_DIR})
  include_directories(${OpenCASCADE_INCLUDE_DIR})
  link_directories(${OpenCASCADE_LIBRARY_DIR})
else(OpenCASCADE_FOUND)
  message(FATAL_ERROR "Open cascade libraries not found")
endif(OpenCASCADE_FOUND)

# After the OCC paths are properly set up,
find_file(GP_PNT_HEADER_LOCATION "gp_Pnt.hxx" PATHS ${OpenCASCADE_INCLUDE_DIR})
if(${GP_PNT_HEADER_LOCATION} STREQUAL "GP_PNT_HEADER_LOCATION-NOTFOUND")
    message(FATAL_ERROR "gp_Pnt.hxx not be found.")
endif()


target_link_libraries(${PROJECT_NAME} TKernel TKMath TKBRep TKG2d TKG3d TKGeomBase TKBO
                        TKBool TKFeat TKFillet TKGeomAlgo TKHLR TKMesh TKOffset
                        TKPrim TKShHealing TKTopAlgo TKXMesh)

target_link_libraries(${PROJECT_NAME} TKService TKV3d TKOpenGl TKMeshVS)

target_link_libraries(${PROJECT_NAME} TKBinXCAF TKIGES TKRWMesh TKSTEP TKSTEP209 TKSTEPAttr
                               TKSTEPBase TKSTL TKVRML TKXCAF TKXDEIGES TKXDESTEP TKXSBase
                               TKXmlXCAF)

target_link_libraries(${PROJECT_NAME} TKCDF TKLCAF TKCAF TKBinL TKXmlL TKBin TKXml TKStdL
                       TKStd TKTObj TKBinTObj TKXmlTObj TKVCAF)                              

                  