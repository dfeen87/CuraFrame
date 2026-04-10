cmake_minimum_required(VERSION 3.14)
project(CuraFrame VERSION 3.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# All constraint-bundle translation units
set(BUNDLE_SOURCES
    constraints/anti_infective/AntiInfectiveBundle.cpp
    constraints/cardiac/CardiacBundle.cpp
    constraints/cns/CNSBundle.cpp
    constraints/formulation/FormulationBundle.cpp
    constraints/hepatic/HepaticBundle.cpp
    constraints/immunologic/ImmunologicBundle.cpp
    constraints/metabolic/MetabolicBundle.cpp
    constraints/oncology/OncologyBundle.cpp
    constraints/pkpd/PKPDBundle.cpp
    constraints/renal/RenalBundle.cpp
    constraints/safety/SafetyBundle.cpp
    constraints/systemic_exposure/SystemicExposureBundle.cpp
)

# Scoring subsystem translation units
set(SCORING_SOURCES
    scoring/WeightProfile.cpp
    scoring/WeightedScoringEngine.cpp
    scoring/ScoringPipeline.cpp
)

# Static library bundling all C++ constraint and scoring logic.
# The repository root is exposed as the include root so that all relative
# includes (e.g. "constraint_core/Candidate.hpp" or "../scoring/...") resolve
# correctly regardless of which translation unit is being compiled.
add_library(curaframe_cpp STATIC
    ${BUNDLE_SOURCES}
    ${SCORING_SOURCES}
)

target_include_directories(curaframe_cpp PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

target_compile_options(curaframe_cpp PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
)

# NOTE: Each bundle uses the REGISTER_CONSTRAINT_BUNDLE self-registration macro,
# which installs a static initialiser in its own translation unit.  When linking
# this library into an executable, force the linker to include every object file
# so that all initialisers run, even those with no externally referenced symbols:
#
#   GCC / Clang (Linux):
#     target_link_libraries(my_app PRIVATE
#         -Wl,--whole-archive curaframe_cpp -Wl,--no-whole-archive)
#
#   Clang (macOS):
#     target_link_libraries(my_app PRIVATE
#         -Wl,-force_load,$<TARGET_FILE:curaframe_cpp>)
#
#   MSVC:
#     target_link_libraries(my_app PRIVATE /WHOLEARCHIVE:curaframe_cpp)
