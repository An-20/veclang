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

# set(PYBIND11_FINDPYTHON ON)
# find_package(pybind11 REQUIRED)

# Filter out those starting with "test_"
set(SOURCES "")
foreach(FILE IN LISTS ALL_SOURCES)
    get_filename_component(FILENAME ${FILE} NAME)
    if(NOT FILENAME MATCHES "^test_" AND NOT FILENAME MATCHES "^main" AND NOT FILENAME MATCHES "bindings")
        list(APPEND SOURCES ${FILE})
    endif()
endforeach()

# if (NOT EMSCRIPTEN)
#     list(APPEND SOURCES "veclang/backend/bc_interpreter/main.cpp")
# endif()

# Add include directories (recursive headers)
include_directories(veclang/utils)

# Native build
if (EMSCRIPTEN)
    list(APPEND SOURCES "veclang/backend/bc_interpreter/main_bindings.cpp")
endif()

add_executable(veclang veclang/backend/bc_interpreter/main.cpp ${SOURCES})
target_compile_options(veclang PRIVATE -Wall -O3 -g)
if (EMSCRIPTEN)
    target_link_options(veclang PRIVATE --bind -lembind)
endif()

# set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
# pybind11_add_module(_bc_interpreter_core ${SOURCES})
# set_target_properties(_bc_interpreter_core PROPERTIES
#     LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/veclang/backend/bc_interpreter"
# )

# if(EMSCRIPTEN)
#   add_executable(veclang_wasm veclang/backend/bc_interpreter/bindings.cpp ${SOURCES})

#   target_compile_options(veclang_wasm PRIVATE -Wall -O3 -g)

#   target_link_options(veclang_wasm PRIVATE --bind -lembind)
# endif()

