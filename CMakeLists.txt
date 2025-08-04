cmake_minimum_required(VERSION 3.15)

project(veclang LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Recursively find all .cpp source files in src/ and lib/utils/
file(GLOB_RECURSE ALL_SOURCES 
    CONFIGURE_DEPENDS
    veclang/*.cpp
    veclang/utils/*.cpp
)

# Filter out those starting with "test_"
set(SOURCES "")
foreach(FILE IN LISTS ALL_SOURCES)
    get_filename_component(FILENAME ${FILE} NAME)
    if(NOT FILENAME MATCHES "^test_")
        list(APPEND SOURCES ${FILE})
    endif()
endforeach()


# Add executable
add_executable(veclang ${SOURCES})

# Add include directories (recursive headers)
target_include_directories(veclang
    PRIVATE
    veclang/utils  # This includes all headers like veclang/utils/math/*.hpp
)

if(EMSCRIPTEN)
  target_link_options(veclang PRIVATE -sNO_DISABLE_EXCEPTION_CATCHING=1)
endif()

target_compile_options(veclang PRIVATE -Wall -O3 -g)
