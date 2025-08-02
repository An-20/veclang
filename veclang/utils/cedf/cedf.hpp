#ifndef AU_CEDF_HPP
#define AU_CEDF_HPP

#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <stdexcept>
#include <fstream>

#pragma pack(push, 1)
struct CEDFHeader
{
    char magic[4]; // Must be "CEDF"
    uint32_t version;
    uint32_t sedf_id;
    uint32_t flags;
    uint64_t json_len;
    uint64_t data_len;
};
#pragma pack(pop)

namespace au_cedf
{
    constexpr const char *CEDF_MAGIC = "CEDF";
    constexpr uint32_t CEDF_VERSION = 0x00010000;

    std::vector<uint8_t> encode_cedf_to_bytes(uint32_t sedf_id,
                                              const std::string &json_header,
                                              const std::vector<uint8_t> &binary_payload)
    {
        CEDFHeader header;
        std::memcpy(header.magic, CEDF_MAGIC, 4);
        header.version = CEDF_VERSION;
        header.sedf_id = sedf_id;
        header.flags = 0;
        header.json_len = json_header.size();
        header.data_len = binary_payload.size();

        std::vector<uint8_t> out(sizeof(CEDFHeader) + header.json_len + header.data_len);
        std::memcpy(out.data(), &header, sizeof(header));
        std::memcpy(out.data() + sizeof(header), json_header.data(), json_header.size());
        std::memcpy(out.data() + sizeof(header) + json_header.size(),
                    binary_payload.data(), binary_payload.size());
        return out;
    }

    void decode_cedf_from_bytes(const std::vector<uint8_t> &data,
                                uint32_t &out_sedf_id,
                                std::string &out_json_header,
                                std::vector<uint8_t> &out_binary_payload)
    {
        if (data.size() < sizeof(CEDFHeader))
            throw std::runtime_error("Data too small to contain header");

        const CEDFHeader *header = reinterpret_cast<const CEDFHeader *>(data.data());
        if (std::memcmp(header->magic, CEDF_MAGIC, 4) != 0)
            throw std::runtime_error("Invalid CEDF magic");

        if (header->version != CEDF_VERSION)
            throw std::runtime_error("Unsupported CEDF version, got " + std::to_string(header->version) +
                                     ", expected " + std::to_string(CEDF_VERSION));

        size_t json_offset = sizeof(CEDFHeader);
        size_t binary_offset = json_offset + header->json_len;

        if (data.size() < binary_offset + header->data_len)
            throw std::runtime_error("Data too small for declared sizes");

        out_sedf_id = header->sedf_id;
        out_json_header = std::string(reinterpret_cast<const char *>(data.data() + json_offset), header->json_len);
        out_binary_payload = std::vector<uint8_t>(data.begin() + binary_offset, data.begin() + binary_offset + header->data_len);
    }

    void write_file(const std::string &filepath,
                    uint32_t sedf_id,
                    const std::string &json_header,
                    const std::vector<uint8_t> &binary_payload)
    {
        std::vector<uint8_t> bin = encode_cedf_to_bytes(sedf_id, json_header, binary_payload);
        std::ofstream out(filepath, std::ios::binary);
        if (!out)
            throw std::runtime_error("Failed to open file for writing");
        out.write(reinterpret_cast<const char *>(bin.data()), bin.size());
    }

    void read_file(const std::string &filepath,
                   uint32_t &out_sedf_id,
                   std::string &out_json_header,
                   std::vector<uint8_t> &out_binary_payload)
    {
        std::ifstream in(filepath, std::ios::binary);
        if (!in)
            throw std::runtime_error("Failed to open file for reading");
        std::vector<uint8_t> data((std::istreambuf_iterator<char>(in)), {});
        decode_cedf_from_bytes(data, out_sedf_id, out_json_header, out_binary_payload);
    }

    std::vector<uint8_t> loadf(const std::string &filepath)
    {
        std::ifstream in(filepath, std::ios::binary);
        if (!in)
            throw std::runtime_error("Failed to open file for reading");
        return std::vector<uint8_t>((std::istreambuf_iterator<char>(in)), {});
    }

    void dumpf(const std::string &filepath, const std::vector<uint8_t> &data)
    {
        std::ofstream out(filepath, std::ios::binary);
        if (!out)
            throw std::runtime_error("Failed to open file for writing");
        out.write(reinterpret_cast<const char *>(data.data()), data.size());
    }
};

#endif // AU_CEDF_HPP
