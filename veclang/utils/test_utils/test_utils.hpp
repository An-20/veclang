#ifndef AU_TEST_UTILS_HPP
#define AU_TEST_UTILS_HPP

#include <random>
#include <string>
#include <vector>
#include <sstream>
#include <fstream>
#include <iostream>
#include <filesystem>

namespace fs = std::filesystem;

namespace au_test_utils
{
    std::string generate_random_string(size_t length = 32)
    {
        static const std::string chars =
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789";

        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> distrib(0, chars.size() - 1);

        std::string result;
        result.reserve(length);
        for (size_t i = 0; i < length; ++i)
            result += chars[distrib(gen)];

        return result;
    }

    std::string get_test_file_path()
    {
        fs::path base_path = fs::temp_directory_path() / "AUREUS_TESTS";

        // Ensure directory exists
        if (!fs::exists(base_path))
            fs::create_directories(base_path);

        std::string filename = generate_random_string() + ".TESTFILE";
        fs::path full_path = base_path / filename;

        // Ensure file doesn't exist
        if (fs::exists(full_path))
            fs::remove(full_path);

        return full_path.string();
    }
}

#endif // AU_TEST_UTILS_HPP
