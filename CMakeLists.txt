################################################################################
# Copyright (C) 2020, NextGIS <info@nextgis.com>
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
endif()

set(PACKAGE_NAME ${PROJECT_NAME})
string(TOUPPER ${PACKAGE_NAME} PACKAGE_UPPER_NAME)

set(LIB_NAME ${PROJECT_NAME})
set(TARGETS ${LIB_NAME})

include(util)

check_version(MAJOR_VER MINOR_VER REL_VER FIX_VER)
set(VERSION ${MAJOR_VER}.${MINOR_VER}.${REL_VER})
report_version(${PROJECT_NAME} ${VERSION})

include(GenerateExportHeader)
include(FindAnyProject)

if(CMAKE_SYSTEM_NAME STREQUAL Android)
    set(ANDROID 1)
endif()

if (WIN32)
    option(USE_CREDENTIAL_STORE "Build with windows CredentialStore support" ON)

    if (USE_CREDENTIAL_STORE)
        add_definitions(-DUSE_CREDENTIAL_STORE=1)
    endif()
endif()

set(QT_COMPONENTS Core)
if(UNIX AND NOT APPLE AND NOT ANDROID)
    set(QT_COMPONENTS ${QT_COMPONENTS} DBus)
endif()

find_anyproject(Qt5 REQUIRED COMPONENTS ${QT_COMPONENTS})

string(SUBSTRING ${QT5_VERSION} 0 1 Qt5Core_VERSION_MAJOR)
set(CMAKE_AUTOMOC ON)

if (NOT Qt5Core_VERSION VERSION_LESS "5.7.0")
    if (CMAKE_COMPILER_IS_GNUCXX)
      if ((NOT CMAKE_CXX_COMPILER_VERSION VERSION_LESS "4.7.0") AND (CMAKE_CXX_COMPILER_VERSION VERSION_LESS "6.1.0"))
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
      elseif(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "4.7.0")
        message(FATAL_ERROR "Can't build QtKeychain using g++-${CMAKE_CXX_COMPILER_VERSION} and Qt ${Qt5Core_VERSION}: compiler supporting C++11 is required")
      endif()
    elseif (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
      if (NOT ${CMAKE_CXX_COMPILER_VERSION} VERSION_LESS 3.3)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
      else()
        message(FATAL_ERROR "Can't build QtKeychain using clang++-${CMAKE_CXX_COMPILER_VERSION} and Qt ${Qt5Core_VERSION}: compiler supporting C++11 is required")
      endif()
    elseif ((CMAKE_CXX_COMPILER_ID MATCHES "MSVC") AND (MSVC_VERSION LESS 1700))
      message(FATAL_ERROR "Can't build QtKeychain using VC++-${MSVC_VERSION} and Qt ${Qt5Core_VERSION}: compiler supporting C++11 is required")
    endif()
endif()


include_directories(${CMAKE_CURRENT_BINARY_DIR})

list(APPEND qtkeychain_LIBRARIES Qt5::Core)
set(qtkeychain_SOURCES
    keychain.cpp
    qkeychain_export.h
    keychain.h
)

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
    if(IOS)
        list(APPEND qtkeychain_SOURCES keychain_ios.cpp)
    else()
        list(APPEND qtkeychain_SOURCES keychain_mac.cpp)
    endif()

    find_library(COREFOUNDATION_LIBRARY CoreFoundation REQUIRED)
    list(APPEND qtkeychain_LIBRARIES ${COREFOUNDATION_LIBRARY})

    find_library(SECURITY_LIBRARY Security REQUIRED)
    list(APPEND qtkeychain_LIBRARIES ${SECURITY_LIBRARY})
endif()

if(UNIX AND NOT APPLE AND NOT ANDROID)
    option(LIBSECRET_SUPPORT "Build with libsecret support" ON)

    if(LIBSECRET_SUPPORT)
        pkg_check_modules(LIBSECRET libsecret-1)

        if (LIBSECRET_FOUND)
            add_definitions(-DHAVE_LIBSECRET=1)
        endif()
        INCLUDE_DIRECTORIES(${LIBSECRET_INCLUDE_DIRS})
        list(APPEND qtkeychain_LIBRARIES ${LIBSECRET_LIBRARIES})
    endif()

    list(APPEND qtkeychain_SOURCES keychain_unix.cpp gnomekeyring.cpp libsecret.cpp plaintextstore.cpp)
    qt5_add_dbus_interface(qtkeychain_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/org.kde.KWallet.xml kwallet_interface KWalletInterface)
    list(APPEND qtkeychain_LIBRARIES Qt5::DBus )
endif()

if(BUILD_SHARED_LIBS)
    add_library(${LIB_NAME} SHARED ${qtkeychain_SOURCES})
else()
    add_library(${LIB_NAME} STATIC ${qtkeychain_SOURCES})
endif()

target_link_libraries(${LIB_NAME} PUBLIC ${qtkeychain_LIBRARIES})

generate_export_header(${LIB_NAME}
  EXPORT_FILE_NAME qkeychain_export.h
  EXPORT_MACRO_NAME QKEYCHAIN_EXPORT
)

add_custom_target(uninstall COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake)

# Export package ===============================================================

# Add path to includes to build-tree export
target_include_directories(${TARGETS} PUBLIC
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

if(NOT SKIP_INSTALL_LIBRARIES AND NOT SKIP_INSTALL_ALL)
    install(TARGETS ${TARGETS} 
        EXPORT ${PACKAGE_UPPER_NAME}Targets
        RUNTIME DESTINATION ${INSTALL_BIN_DIR}
        ARCHIVE DESTINATION ${INSTALL_LIB_DIR}
        LIBRARY DESTINATION ${INSTALL_LIB_DIR}
        INCLUDES DESTINATION ${INSTALL_INC_DIR}
        FRAMEWORK DESTINATION ${INSTALL_LIB_DIR}
    )

    install(FILES keychain.h ${CMAKE_CURRENT_BINARY_DIR}/qkeychain_export.h
        DESTINATION ${INSTALL_INC_DIR}
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
