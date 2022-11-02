cmake_minimum_required(VERSION 3.0.0)
project(cpp_app_demo VERSION 0.1.0)

include(CTest)
enable_testing()
option(STAMP "stamp")

add_executable(cpp_app_demo main.cpp out.cpp)
target_compile_options(cpp_app_demo PUBLIC -fsanitize=address)
target_link_libraries(cpp_app_demo asan)
target_include_directories(cpp_app_demo PUBLIC "bla")


if (${STAMP})
# get all cmake veriables
# https://stackoverflow.com/questions/9298278/cmake-print-out-all-accessible-variables-in-a-script
# get_cmake_property(_variableNames VARIABLES)
# list (SORT _variableNames)
# foreach (_variableName ${_variableNames})
#     message(STATUS "${_variableName}=${${_variableName}}")
# endforeach()
set(MYTGT cpp_app_demo)
execute_process(COMMAND bash -c "awk -F '=' '/DISTRIB_RELEASE/ { print $2}' /etc/lsb-release" OUTPUT_VARIABLE DISTRIB_RELEASE OUTPUT_STRIP_TRAILING_WHITESPACE)

set(BUILD_METADATA "ubuntu-${DISTRIB_RELEASE}")
    add_custom_target(stamp
        BYPRODUCTS out.cpp
        COMMAND echo stamping cpp_app_demo
        COMMAND vmn stamp cpp_app_demo -r patch
        COMMAND vmn show cpp_app_demo > cpp_app_demo_version.txt
        COMMAND rm cpp_app_demo_buildmeta.txt
        COMMAND echo build_type: ${CMAKE_BUILD_TYPE} >> cpp_app_demo_buildmeta.txt
        COMMAND echo build_flags: $<IF:$<CONFIG:Debug>,${CMAKE_CXX_FLAGS_DEBUG},${CMAKE_CXX_FLAGS_RELEASE}> >> cpp_app_demo_buildmeta.txt
        COMMAND bash -c "echo compile_flags: $(awk -F '=' '/CXX_FLAGS/ { print $2}' CMakeFiles/${MYTGT}.dir/flags.cmake | tr -d '\\t ') >> cpp_app_demo_buildmeta.txt"
        COMMAND bash -c "vmn $<$<BOOL:$VERBOSE>:--debug> add -v $(cat cpp_app_demo_version.txt) --vmp cpp_app_demo_buildmeta.txt --bm ${BUILD_METADATA} cpp_app_demo"
        COMMAND bash -c "vmn $<$<BOOL:$VERBOSE>:--debug> gen -v $(cat cpp_app_demo_version.txt)+${BUILD_METADATA} -t /home/danielc/test_vmn/local/ver_template.j2 -o out.cpp cpp_app_demo"
        COMMAND_EXPAND_LISTS
        VERBATIM)

    add_dependencies(cpp_app_demo stamp)
else()
    add_custom_target(dev
    BYPRODUCTS out.cpp
    COMMAND echo dev mode
    COMMAND echo ${TGT_CXX_FLAGS}
    COMMAND echo build_flags: ${CMAKE_CXX_FLAGS_DEBUG} > cpp_app_demo_buildmeta.txt
    COMMAND echo build_type: ${CMAKE_BUILD_TYPE} >> cpp_app_demo_buildmeta.txt
    COMMAND bash -c "vmn $<$<BOOL:$VERBOSE>:--debug> gen -t /home/danielc/test_vmn/local/dev.j2 -o out.cpp cpp_app_demo"
    VERBATIM)

    add_dependencies(cpp_app_demo dev)
endif()

set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
include(CPack)
