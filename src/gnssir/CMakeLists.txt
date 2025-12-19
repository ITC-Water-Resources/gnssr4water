cmake_minimum_required(VERSION 3.10.0)
project(gnssir)

#be a nasty jerk when an in-source build is attempted
if(${CMAKE_SOURCE_DIR} STREQUAL ${CMAKE_CURRENT_BINARY_DIR})
   message(FATAL_ERROR "You're not making an out-of-source build. This is a bad idea" )
endif(${CMAKE_SOURCE_DIR} STREQUAL ${CMAKE_CURRENT_BINARY_DIR})

option(USE_LZ4 "ENABLE LZ4 STREAM compression" ON)
option(USE_GZIP "ENABLE GZIP STREAM compression" ON)

if (USE_LZ4)
    add_definitions(-DUSE_LZ4)
endif()

if (USE_GZIP)
    add_definitions(-DUSE_GZIP)
endif()

enable_language(C)


# make sure that the default is a RELEASE
if (NOT CMAKE_BUILD_TYPE)
  set (CMAKE_BUILD_TYPE RELEASE CACHE STRING   "Choose the type of build, options are: None Debug Release." FORCE)
endif (NOT CMAKE_BUILD_TYPE)



#basic compiler flags
set(CMAKE_C_FLAGS_RELEASE "-march=native -O3")
set(CMAKE_C_FLAGS_DEBUG "-march=native -O3 -g -fdump-core -fbacktrace -Wall") 


#add make info
set(CMAKE_VERBOSE_MAKEFILE on)


#set the name of the library to be build
set(GNSSIRLIB "gnssir")
set(GNSSIRLIBMAJORVERSION 0)
set(GNSSIRLIBMINORVERSION 1)

#where to put build executables
SET(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/bin)

#where to put archives and the libraries
SET(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/lib)
SET(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/lib)


#make sure shared libraries in the installed executables point to the correct ones (may be non-standard locations)
SET(CMAKE_SKIP_BUILD_RPATH  FALSE)
SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)


#Cfiles 
LIST(APPEND COBJS src/gnssir.c src/nmea.c src/stream.c )


add_library(${GNSSRLIB} STATIC ${COBJS} )

set_target_properties( ${GNSSRLIB} PROPERTIES PUBLIC_HEADER "src/nmea.h;src/gnssir.h")

INSTALL(TARGETS ${GNSSRLIB} LIBRARY DESTINATION lib PUBLIC_HEADER DESTINATION include)







