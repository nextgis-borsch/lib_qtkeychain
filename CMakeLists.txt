################################################################################
# Copyright (C) 2020-2022, NextGIS <info@nextgis.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################

cmake_minimum_required(VERSION 2.8.12 FATAL_ERROR)
project(qtkeychain)

if(NOT DEFINED PACKAGE_VENDOR)
    set(PACKAGE_VENDOR NextGIS)
endif()

if(NOT DEFINED PACKAGE_BUGREPORT)
    set(PACKAGE_BUGREPORT info@nextgis.com)
endif()

# some init settings
set(CMAKE_COLOR_MAKEFILE ON)
# set path to additional CMake modules
set(CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake ${CMAKE_MODULE_PATH})

if(OSX_FRAMEWORK AND (BUILD_SHARED_LIBS OR BUILD_STATIC_LIBS))
  message(FATAL_ERROR "Only OSX_FRAMEWORK key or any or both BUILD_SHARED_LIBS
                       and BUILD_STATIC_LIBS keys are permitted")
endif()

if(OSX_FRAMEWORK)
    set(INSTALL_BIN_DIR "bin" CACHE INTERNAL "Installation directory for executables" FORCE)
    set(INSTALL_LIB_DIR "Library/Frameworks" CACHE INTERNAL "Installation directory for libraries" FORCE)
    set(INSTALL_CMAKECONF_DIR ${INSTALL_LIB_DIR}/${PROJECT_NAME}.framework/Resources/CMake CACHE INTERNAL "Installation directory for cmake config files" FORCE)
    set(INSTALL_INC_DIR ${INSTALL_LIB_DIR}/${PROJECT_NAME}.framework/Headers CACHE INTERNAL "Installation directory for headers" FORCE)
    set(SKIP_INSTALL_HEADERS ON)
    set(SKIP_INSTALL_EXECUTABLES ON)
    set(SKIP_INSTALL_FILES ON)
    set(SKIP_INSTALL_EXPORT ON)
    set(CMAKE_MACOSX_RPATH ON)
else()
    include(GNUInstallDirs)

    set(INSTALL_BIN_DIR ${CMAKE_INSTALL_BINDIR} CACHE INTERNAL "Installation directory for executables" FORCE)
    set(INSTALL_LIB_DIR ${CMAKE_INSTALL_LIBDIR} CACHE INTERNAL "Installation directory for libraries" FORCE)
    set(INSTALL_INC_DIR ${CMAKE_INSTALL_INCLUDEDIR} CACHE INTERNAL "Installation directory for headers" FORCE)
    set(INSTALL_PKGCONFIG_DIR "${INSTALL_LIB_DIR}/pkgconfig" CACHE INTERNAL "Installation directory for pkgconfig (.pc) files" FORCE)
    set(INSTALL_CMAKECONF_DIR ${CMAKE_INSTALL_DATADIR}/${PROJECT_NAME}/CMake CACHE INTERNAL "Installation directory for cmake config files" FORCE)
    set(INSTALL_TRANSLATIONS_DIR "${CMAKE_INSTALL_DATADIR}/translations" CACHE INTERNAL "Installation directory for translations" FORCE)
endif()

set(PACKAGE_NAME ${PROJECT_NAME})
string(TOUPPER ${PACKAGE_NAME} PACKAGE_UPPER_NAME)

set(LIB_NAME ${PROJECT_NAME})
set(TARGETS ${LIB_NAME})

include(util)

check_version(MAJOR_VER MINOR_VER REL_VER)
set(VERSION ${MAJOR_VER}.${MINOR_VER}.${REL_VER})
set(FRAMEWORK_VERSION "${MAJOR_VER}")
report_version(${PROJECT_NAME} ${VERSION})

include(GenerateExportHeader)
include(FindAnyProject)

option(BUILD_TRANSLATIONS "Build translations" ON)

if (WIN32)
    option(USE_CREDENTIAL_STORE "Build with windows CredentialStore support" ON)

    if (USE_CREDENTIAL_STORE)
        add_definitions(-DUSE_CREDENTIAL_STORE=1)
    endif()
endif()

set(QT_COMPONENTS Core)
# if(UNIX AND NOT APPLE)
#     set(QT_COMPONENTS ${QT_COMPONENTS} DBus)
# endif()
if(BUILD_TRANSLATIONS)
    set(QT_COMPONENTS ${QT_COMPONENTS} LinguistTools)
endif()

find_anyproject(Qt5 REQUIRED COMPONENTS ${QT_COMPONENTS})

string(SUBSTRING ${QT5_VERSION} 0 1 Qt5Core_VERSION_MAJOR)
set(CMAKE_AUTOMOC ON)

include_directories(${CMAKE_CURRENT_BINARY_DIR})

list(APPEND qtkeychain_LIBRARIES Qt5::Core)
set(qtkeychain_SOURCES
    keychain.cpp
    qkeychain_export.h
    keychain.h
)

if(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
    # CMake < 3.15 sneaks in /W# flags for us, so we need a replacement,
    # or we'll get a warning (cf. CMP0092)
    if (CMAKE_CXX_FLAGS MATCHES "/W[0-4]")
        string(REGEX REPLACE "/W[0-4]" "/W4" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    else()
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4")
    endif()
else()
    # MSVC's STL / Qt headers are not MSVC -Wall clean, so don't enable it there
    add_definitions( -Wall -Werror=return-type )
endif()

if(WIN32)
    list(APPEND qtkeychain_SOURCES keychain_win.cpp)
    if (NOT USE_CREDENTIAL_STORE)
        list(APPEND qtkeychain_LIBRARIES crypt32)
        list(APPEND qtkeychain_SOURCES plaintextstore.cpp)
    endif()
    #FIXME: mingw bug; otherwise getting undefined refs to RtlSecureZeroMemory there
    if(MINGW)
        add_definitions( -O2 )
    endif()
endif()

if(APPLE)
    list(APPEND qtkeychain_SOURCES keychain_apple.mm)
    list(APPEND qtkeychain_LIBRARIES "-framework Foundation" "-framework Security")
endif()

set(qtkeychain_HEADERS
    keychain.h ${CMAKE_CURRENT_BINARY_DIR}/qkeychain_export.h
)

set(qtkeychain_TR_FILES
      translations/qtkeychain_de.ts
      translations/qtkeychain_fr.ts
      translations/qtkeychain_ro.ts
      translations/qtkeychain_ru.ts
      translations/qtkeychain_zh.ts
)

if(OSX_FRAMEWORK)
    add_library(${LIB_NAME} SHARED ${qtkeychain_HEADERS} ${qtkeychain_SOURCES} ${QM_FILES})
        set_property(SOURCE ${QM_FILES} PROPERTY MACOSX_PACKAGE_LOCATION "Resources/translations")
        # set_property(SOURCE ${qtkeychain_HEADERS} PROPERTY MACOSX_PACKAGE_LOCATION "Headers/framework")
        set_target_properties(${LIB_NAME} PROPERTIES
            # DEFINE_SYMBOL ${PROJECT_UPPER_NAME}_LIBRARY
            FRAMEWORK TRUE
            FRAMEWORK_VERSION ${FRAMEWORK_VERSION}
            MACOSX_FRAMEWORK_SHORT_VERSION_STRING ${VERSION}
            MACOSX_FRAMEWORK_BUNDLE_VERSION ${VERSION}
            VERSION ${VERSION}
            SOVERSION ${MAJOR_VER}
            MACOSX_FRAMEWORK_IDENTIFIER org.qtkeychain.${LIB_NAME}
            XCODE_ATTRIBUTE_INSTALL_PATH "@rpath"
            PUBLIC_HEADER "${qtkeychain_HEADERS}"
        )
elseif(BUILD_SHARED_LIBS)
    add_library(${LIB_NAME} SHARED ${qtkeychain_SOURCES})
    set_target_properties(${LIB_NAME} PROPERTIES
    VERSION ${VERSION})
else()
    add_library(${LIB_NAME} STATIC ${qtkeychain_SOURCES})
endif()

if(WIN32)
    set_target_properties( ${LIB_NAME} PROPERTIES DEBUG_POSTFIX "d" )
endif()

file(GLOB qtkeychain_TR_SOURCES *.cpp *.h *.ui)
if (BUILD_TRANSLATIONS)
    qt5_create_translation(qtkeychain_MESSAGES ${qtkeychain_TR_SOURCES} ${qtkeychain_TR_FILES})
    qt5_add_translation(QM_FILES ${qtkeychain_TR_FILES})
    add_custom_target(messages DEPENDS ${qtkeychain_MESSAGES})
    add_custom_target(translations DEPENDS ${QM_FILES} messages)
    # https://github.com/frankosterfeld/qtkeychain/issues/185
    add_dependencies(${LIB_NAME} translations)

    if(NOT SKIP_INSTALL_FILES AND NOT SKIP_INSTALL_ALL)
        install(FILES ${QM_FILES} DESTINATION ${QTKEYCHAIN_TRANSLATIONS_DIR})
    endif()
endif()

target_link_libraries(${LIB_NAME} PRIVATE ${qtkeychain_LIBRARIES})

generate_export_header(${LIB_NAME}
    EXPORT_FILE_NAME qkeychain_export.h
    EXPORT_MACRO_NAME QKEYCHAIN_EXPORT
)

add_custom_target(uninstall COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake)

# Export package ===============================================================

# Add path to includes to build-tree export
target_include_directories(${TARGETS} PRIVATE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>
)

# Add all targets to the build-tree export set
export(TARGETS ${TARGETS}
   FILE ${PROJECT_BINARY_DIR}/${PACKAGE_UPPER_NAME}Targets.cmake)

if(REGISTER_PACKAGE)
   # Export the package for use from the build-tree
   # (this registers the build-tree with a global CMake-registry)
   export(PACKAGE ${PACKAGE_UPPER_NAME})
endif()

# Create the ZLIBConfig.cmake file
configure_file(cmake/PackageConfig.cmake.in
   ${PROJECT_BINARY_DIR}/${PACKAGE_UPPER_NAME}Config.cmake @ONLY)

if(NOT SKIP_INSTALL_HEADERS AND NOT SKIP_INSTALL_ALL)   
    install(FILES ${qtkeychain_HEADERS} DESTINATION ${INSTALL_INC_DIR})
endif()

if(NOT SKIP_INSTALL_LIBRARIES AND NOT SKIP_INSTALL_ALL)
    install(TARGETS ${TARGETS} 
        EXPORT ${PACKAGE_UPPER_NAME}Targets
        RUNTIME DESTINATION ${INSTALL_BIN_DIR}
        ARCHIVE DESTINATION ${INSTALL_LIB_DIR}
        LIBRARY DESTINATION ${INSTALL_LIB_DIR}
        INCLUDES DESTINATION ${INSTALL_INC_DIR}
        FRAMEWORK DESTINATION ${INSTALL_LIB_DIR}
    )

    # Install the <Package>Config.cmake
    install(FILES
        ${PROJECT_BINARY_DIR}/${PACKAGE_UPPER_NAME}Config.cmake
        DESTINATION ${INSTALL_CMAKECONF_DIR} COMPONENT dev)

    # Install the export set for use with the install-tree
    install(EXPORT ${PACKAGE_UPPER_NAME}Targets DESTINATION ${INSTALL_CMAKECONF_DIR} COMPONENT dev)
endif()

# Archiving ====================================================================

set(CPACK_PACKAGE_NAME "${PACKAGE_NAME}")
set(CPACK_PACKAGE_VENDOR "${PACKAGE_VENDOR}")
set(CPACK_PACKAGE_VERSION "${VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "${PACKAGE_NAME} Installation")
set(CPACK_PACKAGE_RELOCATABLE TRUE)
set(CPACK_ARCHIVE_COMPONENT_INSTALL ON)
set(CPACK_GENERATOR "ZIP")
set(CPACK_MONOLITHIC_INSTALL ON)
set(CPACK_STRIP_FILES TRUE)

# Get cpack zip archive name
get_cpack_filename(${VERSION} PROJECT_CPACK_FILENAME)
set(CPACK_PACKAGE_FILE_NAME ${PROJECT_CPACK_FILENAME})

include(CPack)
