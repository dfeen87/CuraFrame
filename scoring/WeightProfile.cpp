// Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
#include "WeightProfile.hpp"

// All WeightProfile methods are implemented inline in WeightProfile.hpp because
// the class relies entirely on virtual dispatch with small, default-valued
// implementations that benefit from inlining.  This translation unit exists to
// compile the header as part of the curaframe_cpp static library, ensuring that
// the vtable and RTTI for WeightProfile, DefaultResearchProfile, and
// HighSafetyProfile are emitted exactly once.
