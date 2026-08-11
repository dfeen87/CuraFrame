// Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
#ifndef CURAFRAME_CONSTRAINT_REGISTRY_HPP
#define CURAFRAME_CONSTRAINT_REGISTRY_HPP

#include "ConstraintBundle.hpp"
#include <string>
#include <map>
#include <memory>
#include <functional>

// Registry for constraint bundles
class ConstraintRegistry {
public:
    using BundleCreator = std::function<std::unique_ptr<ConstraintBundle>()>;

    static ConstraintRegistry& instance() {
        static ConstraintRegistry inst;
        return inst;
    }

    void register_bundle(const std::string& name, BundleCreator creator) {
        creators[name] = creator;
    }

    std::map<std::string, std::unique_ptr<ConstraintBundle>> create_all_bundles() const {
        std::map<std::string, std::unique_ptr<ConstraintBundle>> bundles;
        for (const auto& pair : creators) {
            bundles[pair.first] = pair.second();
        }
        return bundles;
    }

private:
    ConstraintRegistry() = default;
    std::map<std::string, BundleCreator> creators;
};

// Helper macro for auto-registering bundles
#define REGISTER_CONSTRAINT_BUNDLE(Name, Class) \
    namespace { \
        struct Class##_Register { \
            Class##_Register() { \
                ConstraintRegistry::instance().register_bundle(Name, []() { return std::make_unique<Class>(); }); \
            } \
        }; \
        static Class##_Register global_##Class##_register; \
    }

#endif // CURAFRAME_CONSTRAINT_REGISTRY_HPP
