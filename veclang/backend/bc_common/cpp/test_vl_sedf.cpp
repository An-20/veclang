#include "vl_sedf.h"

// int main()
// {
//     // // Create dummy data
//     // std::string json = R"({"name": "test", "value": 123})";
//     // std::vector<uint8_t> payload = {1, 2, 3, 4, 5};

//     // // Write file
//     // au_cedf::write_file("test.sedf", 42, json, payload);
//     // std::cout << "Wrote test.sedf\n";

//     // Read file
//     // uint32_t sedf_id;
//     // std::string json_out;
//     // std::vector<uint8_t> payload_out;

//     // au_cedf::read_file("C:\\Users\\xiada\\Documents\\veclang\\veclang\\tests\\out2.sedf", sedf_id, json_out, payload_out);

//     // std::cout << "Read SEDF ID: " << sedf_id << "\n";
//     // std::cout << "JSON: " << json_out << "\n";
//     // std::cout << "Payload bytes:";
//     // for (auto b : payload_out)
//     //     std::cout << " " << (int)b;
//     // std::cout << "\n";

//     vl_sedf::VlProgram program = vl_sedf::load("C:\\Users\\xiada\\Documents\\veclang\\veclang\\tests\\out2.sedf");
//     std::cout << "Loaded VL SEDF program with magic: " << program.header.magic << "\n";
//     std::cout << "Version: " << program.header.version << "\n";
//     std::cout << "Functions:\n";
//     for (const auto &func : program.header.functions)
//     {
//         std::cout << "  Name: " << func.name << ", Stack Size: " << func.stack_size
//                   << ", Instruction Offset: " << func.instruction_offset
//                   << ", Arg Types: ";
//         for (auto type : func.arg_types)
//             std::cout << (int)type << " ";
//         std::cout << ", Return Type: " << (int)func.return_type << "\n";
//     }
//     std::cout << "Constants size: " << program.constants.size() << "\n";
//     std::cout << "Instructions size: " << program.instructions.size() << "\n";
//     // print constants bytes and instructions bytes
//     std::cout << "Constants bytes: ";
//     for (auto byte : program.constants)
//         std::cout << (int)byte << " ";
//     std::cout << "\n";

//     std::cout << "Instructions bytes: ";
//     for (auto byte : program.instructions)
//         std::cout << (int)byte << " ";
//     std::cout << "\n";
//     return 0;
// }