// Build-time helper for @qtbase: gzip-compresses the freedesktop.org shared
// MIME database XML and emits it as a C array, replacing the Python one-liner
// that Qt's CMake build (QtMimeDatabase.cmake) uses for the same purpose.
//
// Usage: qt_mime_database_gen <input.xml> <output.cpp>
//
// The output matches what src/corelib/mimetypes/qmimeprovider.cpp expects:
//   #define MIME_DATABASE_IS_GZIP
//   static const unsigned char mimetype_database[] = { ... };
//   static constexpr size_t MimeTypeDatabaseOriginalSize = <uncompressed size>;
//
// Deterministic: fixed gzip header (mtime 0, no name, OS = unknown) so the
// generated source is byte-identical across hosts.

#include <zlib.h>

#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

namespace {

bool gzipCompress(const std::vector<unsigned char> &in, std::vector<unsigned char> *out)
{
    z_stream strm;
    std::memset(&strm, 0, sizeof(strm));
    // 15 + 16 = gzip container; memLevel 8 (zlib's DEF_MEM_LEVEL, also what
    // Python's gzip module uses) so the stream matches Qt's CMake-generated one.
    if (deflateInit2(&strm, Z_BEST_COMPRESSION, Z_DEFLATED, 15 + 16, 8, Z_DEFAULT_STRATEGY) != Z_OK)
        return false;

    gz_header header;
    std::memset(&header, 0, sizeof(header));
    header.time = 0;
    header.os = 255; // "unknown", same as Python's gzip.compress(mtime=0)
    if (deflateSetHeader(&strm, &header) != Z_OK) {
        deflateEnd(&strm);
        return false;
    }

    out->resize(deflateBound(&strm, static_cast<uLong>(in.size())) + 32);
    strm.next_in = const_cast<Bytef *>(in.data());
    strm.avail_in = static_cast<uInt>(in.size());
    strm.next_out = out->data();
    strm.avail_out = static_cast<uInt>(out->size());

    const int rc = deflate(&strm, Z_FINISH);
    const bool ok = (rc == Z_STREAM_END);
    out->resize(strm.total_out);
    deflateEnd(&strm);
    return ok;
}

} // namespace

int main(int argc, char **argv)
{
    if (argc != 3) {
        std::fprintf(stderr, "usage: %s <input.xml> <output.cpp>\n", argv[0]);
        return 2;
    }

    std::ifstream in(argv[1], std::ios::binary);
    if (!in) {
        std::fprintf(stderr, "cannot read %s\n", argv[1]);
        return 1;
    }
    std::vector<unsigned char> raw((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());

    std::vector<unsigned char> compressed;
    if (!gzipCompress(raw, &compressed)) {
        std::fprintf(stderr, "gzip compression failed\n");
        return 1;
    }

    std::FILE *out = std::fopen(argv[2], "wb");
    if (!out) {
        std::fprintf(stderr, "cannot write %s\n", argv[2]);
        return 1;
    }
    std::fputs("#define MIME_DATABASE_IS_GZIP\n", out);
    std::fputs("static const unsigned char mimetype_database[] = {\n", out);
    for (size_t i = 0; i < compressed.size(); i += 12) {
        std::fputc(' ', out);
        for (size_t j = i; j < i + 12 && j < compressed.size(); ++j)
            std::fprintf(out, "%s0x%02x", j == i ? "" : ", ", compressed[j]);
        std::fputs(",\n", out);
    }
    std::fputs("};\n", out);
    std::fprintf(out, "static constexpr size_t MimeTypeDatabaseOriginalSize = %zu;\n", raw.size());
    std::fclose(out);
    return 0;
}
