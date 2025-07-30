#include "cedf.hpp"
#include "../test_utils/test_utils.hpp"
#include <iostream>

int main()
{
    // Create dummy data
    std::string json = R"({"name": "test", "value": 123})";
    std::vector<uint8_t> payload = {1, 2, 3, 4, 5};

    // Write file
    std::string test_file_path = au_test_utils::get_test_file_path();
    std::cout << "Test file path: " << test_file_path << "\n";
    au_cedf::write_file(test_file_path, 42, json, payload);
    std::cout << "Wrote " << test_file_path << "\n";

    // Read file
    uint32_t sedf_id;
    std::string json_out;
    std::vector<uint8_t> payload_out;

    au_cedf::read_file(test_file_path, sedf_id, json_out, payload_out);

    std::cout << "Read SEDF ID: " << sedf_id << "\n";
    std::cout << "JSON: " << json_out << "\n";
    std::cout << "Payload bytes:";
    for (auto b : payload_out)
        std::cout << " " << (int)b;
    std::cout << "\n";
}
