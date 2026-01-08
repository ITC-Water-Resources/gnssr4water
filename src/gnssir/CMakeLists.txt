cmake_minimum_required(VERSION 3.10.0)
project(gnssir)

#be a nasty jerk when an in-source build is attempted
if(${CMAKE_SOURCE_DIR} STREQUAL ${CMAKE_CURRENT_BINARY_DIR})
   message(FATAL_ERROR "You're not making an out-of-source build. This is a bad idea" )
endif(${CMAKE_SOURCE_DIR} STREQUAL ${CMAKE_CURRENT_BINARY_DIR})

include_directories( ${CMAKE_CURRENT_SOURCE_DIR}/src )

option(USE_LZ4 "ENABLE LZ4 STREAM compression" ON)
option(USE_GZIP "ENABLE GZIP STREAM compression" ON)

option(LOGWARNING "LOG Warnings" OFF)

if (USE_LZ4)
    add_definitions(-DUSE_LZ4)
    include_directories( ${cmake_current_source_dir}/src/lz4static )
endif()

if (USE_GZIP)
    add_definitions(-DUSE_GZIP)
    find_package(ZLIB)
endif()

if (LOGWARNING)
    add_definitions(-DLOGWARNING)
endif()

enable_language(C)


# make sure that the default is a RELEASE
if (NOT CMAKE_BUILD_TYPE)
  set (CMAKE_BUILD_TYPE RELEASE CACHE STRING   "Choose the type of build, options are: None Debug Release." FORCE)
endif (NOT CMAKE_BUILD_TYPE)



#basic compiler flags
set(CMAKE_C_FLAGS_RELEASE "-march=native -O3")
set(CMAKE_C_FLAGS_DEBUG "-O0 -g -Wall") 


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
LIST(APPEND COBJS src/gnssir.c src/nmea.c src/stream.c src/arcs.c src/timeutil.c src/position.c src/skymask.c)

if (USE_LZ4)
    LIST(APPEND COBJS src/lz4stream.c src/lz4static/lz4file.c src/lz4static/lz4.c src/lz4static/lz4hc.c src/lz4static/xxhash.c src/lz4static/lz4frame.c )
endif()

add_library( ${GNSSIRLIB} STATIC ${COBJS} )

set_target_properties( ${GNSSIRLIB} PROPERTIES PUBLIC_HEADER "src/gnssir.h;src/timeutil.h;src/position.h;src/stream.h;src/skymask.h")

INSTALL(TARGETS ${GNSSIRLIB} LIBRARY DESTINATION lib PUBLIC_HEADER DESTINATION include)


# add command line programs
set(GNSSIR_EXEC arcxtract)  
foreach(prog  ${GNSSIR_EXEC})
add_executable(${prog} src/cli/${prog}.c)
target_link_libraries(${prog} PRIVATE ${GNSSIRLIB} )
target_link_libraries( ${prog} PUBLIC ZLIB::ZLIB m )

#target_include_directories( ${prog} ${CMAKE_CURRENT_SOURCE_DIR}/src )
install(TARGETS ${prog} DESTINATION bin)
endforeach(prog in ${GNSSIR_EXEC})





