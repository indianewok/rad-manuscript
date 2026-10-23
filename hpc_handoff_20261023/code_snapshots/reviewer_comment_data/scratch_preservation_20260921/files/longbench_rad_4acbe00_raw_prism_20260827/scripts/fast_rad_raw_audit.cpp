#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include <zlib.h>

namespace fs = std::filesystem;

enum Flag : unsigned {
    ALL = 0,
    NATIVE_EXACT,
    ALL_CORRECTED,
    SELECTED_SOURCE_CHANGED,
    MISSED_CELLRANGER_TO_SELECTED,
    CELLRANGER_TO_DIFFERENT_CELLRANGER,
    CONSENSUS_CROSS_LINE,
    CONSENSUS_SAME_LINE_DIFFERENT_CELL,
    CONSENSUS_LABEL_INCOMPLETE,
    CELLRANGER_TO_NONCELLRANGER_SELECTED,
    CATALOG_NONCELL_TO_SELECTED,
    NONCATALOG_TO_SELECTED,
    RAW_SOURCE_UNAVAILABLE,
    TARGET_OUTSIDE_SELECTED,
    TARGET_INVALID_BARCODE,
    NFLAGS
};

using Mask = std::uint32_t;
using Counts = std::array<std::uint64_t, NFLAGS>;

static constexpr Mask bit(Flag f) { return Mask{1} << static_cast<unsigned>(f); }

struct Args {
    std::string dataset;
    fs::path selected;
    fs::path cellranger;
    fs::path catalog_u32;
    fs::path label_dir;
    fs::path outdir;
    bool exclude_ct = false;
    bool check_reentry = false;
    std::uint64_t expected_groups = 0;
};

struct Uuid128 {
    std::uint64_t high = 0;
    std::uint64_t low = 0;
    bool operator==(const Uuid128 &other) const { return high == other.high && low == other.low; }
};

struct Uuid128Hash {
    std::size_t operator()(const Uuid128 &value) const {
        std::uint64_t x = value.high ^ (value.low + 0x9e3779b97f4a7c15ULL + (value.high << 6U) + (value.high >> 2U));
        x ^= x >> 30U; x *= 0xbf58476d1ce4e5b9ULL;
        x ^= x >> 27U; x *= 0x94d049bb133111ebULL;
        x ^= x >> 31U;
        return static_cast<std::size_t>(x);
    }
};

[[noreturn]] static void fail(const std::string &message) {
    throw std::runtime_error(message);
}

static bool ends_with(const std::string &value, const std::string &suffix) {
    return value.size() >= suffix.size() &&
           value.compare(value.size() - suffix.size(), suffix.size(), suffix) == 0;
}

static std::string trim_normalize(std::string value) {
    std::size_t left = 0;
    while (left < value.size() && std::isspace(static_cast<unsigned char>(value[left]))) ++left;
    std::size_t right = value.size();
    while (right > left && std::isspace(static_cast<unsigned char>(value[right - 1]))) --right;
    value = value.substr(left, right - left);
    while (!value.empty() && (value.front() == '\'' || value.front() == '"')) value.erase(value.begin());
    while (!value.empty() && (value.back() == '\'' || value.back() == '"')) value.pop_back();
    for (char &ch : value) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    const std::size_t dash = value.rfind('-');
    if (dash != std::string::npos && dash + 1 < value.size()) {
        bool digits = true;
        for (std::size_t i = dash + 1; i < value.size(); ++i) {
            if (!std::isdigit(static_cast<unsigned char>(value[i]))) { digits = false; break; }
        }
        if (digits) value.resize(dash);
    }
    return value;
}

static bool barcode_code(const std::string &value, std::uint32_t &code) {
    if (value.size() != 16) return false;
    std::uint32_t out = 0;
    for (char ch : value) {
        out <<= 2;
        switch (ch) {
            case 'A': break;
            case 'C': out |= 1; break;
            case 'G': out |= 2; break;
            case 'T': out |= 3; break;
            default: return false;
        }
    }
    code = out;
    return true;
}

static std::string code_barcode(std::uint32_t code) {
    static const char alphabet[] = "ACGT";
    std::string value(16, 'A');
    for (int i = 15; i >= 0; --i) {
        value[static_cast<std::size_t>(i)] = alphabet[code & 3U];
        code >>= 2U;
    }
    return value;
}

static std::string revcomp(const std::string &value) {
    std::string out;
    out.reserve(value.size());
    for (auto it = value.rbegin(); it != value.rend(); ++it) {
        switch (*it) {
            case 'A': out.push_back('T'); break;
            case 'C': out.push_back('G'); break;
            case 'G': out.push_back('C'); break;
            case 'T': out.push_back('A'); break;
            default: out.push_back(*it); break;
        }
    }
    return out;
}

static std::string first_barcode_in_line(const std::string &line) {
    std::size_t start = 0;
    while (start < line.size()) {
        while (start < line.size() &&
               (std::isspace(static_cast<unsigned char>(line[start])) || line[start] == ',')) ++start;
        std::size_t end = start;
        while (end < line.size() &&
               !(std::isspace(static_cast<unsigned char>(line[end])) || line[end] == ',')) ++end;
        if (end > start) {
            std::string candidate = trim_normalize(line.substr(start, end - start));
            std::uint32_t ignored = 0;
            if (barcode_code(candidate, ignored)) return candidate;
        }
        start = end + 1;
    }
    return {};
}

template <typename Fn>
static void for_each_line(const fs::path &path, Fn fn) {
    if (path.extension() == ".gz") {
        gzFile handle = gzopen(path.c_str(), "rb");
        if (!handle) fail("cannot open gzip reference: " + path.string());
        std::vector<char> buffer(1U << 16U);
        std::string line;
        while (true) {
            char *got = gzgets(handle, buffer.data(), static_cast<int>(buffer.size()));
            if (!got) break;
            line.assign(got);
            while (!line.empty() && line.back() != '\n' && !gzeof(handle)) {
                got = gzgets(handle, buffer.data(), static_cast<int>(buffer.size()));
                if (!got) break;
                line.append(got);
            }
            if (!line.empty() && line.back() == '\n') line.pop_back();
            if (!line.empty() && line.back() == '\r') line.pop_back();
            fn(line);
        }
        int errnum = Z_OK;
        const char *msg = gzerror(handle, &errnum);
        if (errnum != Z_OK && errnum != Z_STREAM_END) {
            std::string detail = msg ? msg : "unknown gzip error";
            gzclose(handle);
            fail("gzip read failed for " + path.string() + ": " + detail);
        }
        gzclose(handle);
    } else {
        std::ifstream handle(path);
        if (!handle) fail("cannot open reference: " + path.string());
        std::string line;
        while (std::getline(handle, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            fn(line);
        }
        if (!handle.eof()) fail("read failed for reference: " + path.string());
    }
}

static std::unordered_set<std::uint32_t> load_barcode_set(const fs::path &path) {
    std::unordered_set<std::uint32_t> values;
    for_each_line(path, [&](const std::string &line) {
        if (line.find_first_not_of(" \t\r\n") == std::string::npos) return;
        std::string barcode = first_barcode_in_line(line);
        if (barcode.empty()) return;
        std::uint32_t code = 0;
        if (!barcode_code(barcode, code)) fail("invalid barcode in " + path.string());
        values.insert(code);
    });
    if (values.empty()) fail("no valid barcodes in " + path.string());
    return values;
}

static std::vector<std::uint32_t> load_catalog(const fs::path &path) {
    const auto bytes = fs::file_size(path);
    if (bytes % sizeof(std::uint32_t) != 0) fail("catalog u32 size is not divisible by 4");
    std::vector<std::uint32_t> values(static_cast<std::size_t>(bytes / sizeof(std::uint32_t)));
    std::ifstream handle(path, std::ios::binary);
    if (!handle) fail("cannot open catalog cache: " + path.string());
    handle.read(reinterpret_cast<char *>(values.data()), static_cast<std::streamsize>(bytes));
    if (!handle) fail("cannot read complete catalog cache: " + path.string());
    if (!std::is_sorted(values.begin(), values.end())) fail("catalog cache is not sorted");
    return values;
}

static std::unordered_map<std::uint32_t, std::string> load_labels(const fs::path &dir) {
    std::vector<fs::path> paths;
    for (const auto &entry : fs::directory_iterator(dir)) {
        if (entry.is_regular_file() && ends_with(entry.path().filename().string(), "_BC_list.txt")) {
            paths.push_back(entry.path());
        }
    }
    std::sort(paths.begin(), paths.end());
    if (paths.empty()) fail("no *_BC_list.txt files under " + dir.string());
    std::unordered_map<std::uint32_t, std::string> labels;
    for (const auto &path : paths) {
        std::string name = path.filename().string();
        const std::string suffix = "_BC_list.txt";
        std::string label = name.substr(0, name.size() - suffix.size());
        for_each_line(path, [&](const std::string &line) {
            if (line.find_first_not_of(" \t\r\n") == std::string::npos) return;
            std::string barcode = first_barcode_in_line(line);
            if (barcode.empty()) fail("invalid label barcode in " + path.string());
            std::uint32_t code = 0;
            barcode_code(barcode, code);
            auto [it, inserted] = labels.emplace(code, label);
            if (!inserted && it->second != label) fail("conflicting labels for " + barcode);
        });
    }
    return labels;
}

static std::string tag_value(const std::string &header, const char *prefix) {
    const std::size_t pos = header.find(prefix);
    if (pos == std::string::npos) return {};
    const std::size_t begin = pos + std::strlen(prefix);
    std::size_t end = header.find('\t', begin);
    if (end == std::string::npos) end = header.size();
    while (end > begin && (header[end - 1] == '\r' || header[end - 1] == '\n')) --end;
    return header.substr(begin, end - begin);
}

static std::string read_token(const std::string &header) {
    std::size_t begin = (!header.empty() && (header[0] == '@' || header[0] == '>')) ? 1 : 0;
    std::size_t end = header.find_first_of(" \t", begin);
    if (end == std::string::npos) end = header.size();
    return header.substr(begin, end - begin);
}

static std::string physical_id(std::string token) {
    if (ends_with(token, "-F-CT") || ends_with(token, "-R-CT")) token.resize(token.size() - 5);
    else if (ends_with(token, "-F") || ends_with(token, "-R")) token.resize(token.size() - 2);
    return token;
}

static Uuid128 parse_uuid_lossless(const std::string &value) {
    Uuid128 out;
    unsigned digits = 0;
    for (char ch : value) {
        if (ch == '-') continue;
        unsigned nibble = 0;
        if (ch >= '0' && ch <= '9') nibble = static_cast<unsigned>(ch - '0');
        else if (ch >= 'a' && ch <= 'f') nibble = static_cast<unsigned>(ch - 'a' + 10);
        else if (ch >= 'A' && ch <= 'F') nibble = static_cast<unsigned>(ch - 'A' + 10);
        else fail("non-hex character in ONT UUID: " + value);
        if (digits < 16) out.high = (out.high << 4U) | nibble;
        else if (digits < 32) out.low = (out.low << 4U) | nibble;
        else fail("too many hex digits in ONT UUID: " + value);
        ++digits;
    }
    if (digits != 32 || value.size() != 36 || value[8] != '-' || value[13] != '-' ||
        value[18] != '-' || value[23] != '-') fail("invalid ONT UUID shape: " + value);
    return out;
}

static std::string fmt_ratio(std::uint64_t numerator, std::uint64_t denominator) {
    if (denominator == 0) return "NA";
    const double value = static_cast<double>(numerator) / static_cast<double>(denominator);
    char buffer[128];
    std::snprintf(buffer, sizeof(buffer), "%.12g", value);
    return buffer;
}

static std::string fmt_excess(std::uint64_t numerator, std::uint64_t total) {
    const std::int64_t denominator = static_cast<std::int64_t>(total) - static_cast<std::int64_t>(numerator);
    if (denominator == 0) return "NA";
    const double value = static_cast<double>(numerator) / static_cast<double>(denominator);
    char buffer[128];
    std::snprintf(buffer, sizeof(buffer), "%.12g", value);
    return buffer;
}

struct Unit {
    std::uint32_t target = 0;
    Mask flags = 0;
};

class Analyzer {
public:
    explicit Analyzer(const Args &args)
        : args_(args), selected_(load_barcode_set(args.selected)),
          cellranger_(load_barcode_set(args.cellranger)),
          catalog_(load_catalog(args.catalog_u32)), labels_(load_labels(args.label_dir)) {
        ont_ids_ = ends_with(args.dataset, "_ONT");
        selected_codes_.assign(selected_.begin(), selected_.end());
        std::sort(selected_codes_.begin(), selected_codes_.end());
        per_target_.resize(selected_codes_.size());
        per_target_records_.resize(selected_codes_.size());
        target_index_.reserve(selected_codes_.size() * 2);
        for (std::size_t i = 0; i < selected_codes_.size(); ++i) target_index_[selected_codes_[i]] = i;
        for (std::uint32_t code : selected_codes_) if (!in_catalog(code)) ++selected_outside_catalog_;
        for (std::uint32_t code : cellranger_) if (!in_catalog(code)) ++cellranger_outside_catalog_;
        for (const auto &entry : labels_) if (!cellranger_.count(entry.first)) ++labels_outside_cellranger_;
        if (args_.check_reentry) {
            if (ont_ids_) {
                closed_ont_ids_.max_load_factor(0.80F);
                if (args_.expected_groups) closed_ont_ids_.reserve(static_cast<std::size_t>(args_.expected_groups));
            } else {
                closed_pb_ids_.max_load_factor(0.80F);
                if (args_.expected_groups) closed_pb_ids_.reserve(static_cast<std::size_t>(args_.expected_groups));
            }
        }
    }

    void run() {
        std::ios::sync_with_stdio(false);
        std::cin.tie(nullptr);
        std::string header, sequence, plus, quality;
        while (std::getline(std::cin, header)) {
            if (!std::getline(std::cin, sequence) || !std::getline(std::cin, plus) || !std::getline(std::cin, quality)) {
                fail("truncated FASTQ record at input record " + std::to_string(fastq_records_ + 1));
            }
            ++fastq_records_;
            if (header.empty() || header[0] != '@' || plus.empty() || plus[0] != '+') {
                fail("malformed FASTQ record " + std::to_string(fastq_records_));
            }
            if (!sequence.empty() && sequence.back() == '\r') sequence.pop_back();
            if (!quality.empty() && quality.back() == '\r') quality.pop_back();
            if (sequence.size() != quality.size()) fail("sequence/quality length mismatch at record " + std::to_string(fastq_records_));

            std::string token = read_token(header);
            const bool is_ct = ends_with(token, "-CT");
            if (is_ct) {
                ++ct_seen_;
                if (args_.exclude_ct) { ++ct_excluded_; continue; }
            }
            std::string rid = physical_id(token);
            if (rid.empty()) fail("empty physical read ID at record " + std::to_string(fastq_records_));
            if (current_read_.empty()) current_read_ = rid;
            else if (rid != current_read_) {
                flush_read();
                current_read_ = std::move(rid);
            }

            std::string target_text = trim_normalize(tag_value(header, "\tCB:Z:"));
            if (target_text.empty()) fail("RAD header lacks CB at record " + std::to_string(fastq_records_));
            std::uint32_t target = 0;
            const bool target_valid = barcode_code(target_text, target);
            auto target_it = target_index_.find(target);
            const bool target_selected = target_valid && target_it != target_index_.end();

            std::string raw = tag_value(header, "\tCR:Z:");
            std::string source_text;
            if (raw.empty()) source_text = target_text;
            else {
                source_text = trim_normalize(raw);
                if (tag_value(header, "\tTS:A:") == "-") {
                    source_text = revcomp(source_text);
                    ++reverse_raw_normalized_;
                }
            }
            std::uint32_t source = 0;
            const bool source_valid = barcode_code(source_text, source);

            Mask flags = bit(ALL);
            if (!target_valid) flags |= bit(TARGET_INVALID_BARCODE);
            if (!target_selected) { flags |= bit(TARGET_OUTSIDE_SELECTED); ++target_outside_rows_; }
            if (source_text == target_text) {
                flags |= bit(NATIVE_EXACT);
            } else {
                flags |= bit(ALL_CORRECTED);
                if (target_selected && source_valid && selected_.count(source)) flags |= bit(SELECTED_SOURCE_CHANGED);
                if (target_selected && source_valid && cellranger_.count(source)) {
                    flags |= bit(MISSED_CELLRANGER_TO_SELECTED);
                    if (cellranger_.count(target)) {
                        flags |= bit(CELLRANGER_TO_DIFFERENT_CELLRANGER);
                        auto sl = labels_.find(source);
                        auto tl = labels_.find(target);
                        if (sl != labels_.end() && tl != labels_.end()) {
                            flags |= (sl->second != tl->second) ? bit(CONSENSUS_CROSS_LINE)
                                                               : bit(CONSENSUS_SAME_LINE_DIFFERENT_CELL);
                        } else {
                            flags |= bit(CONSENSUS_LABEL_INCOMPLETE);
                        }
                    } else {
                        flags |= bit(CELLRANGER_TO_NONCELLRANGER_SELECTED);
                    }
                } else if (target_selected && source_valid && in_catalog(source)) {
                    flags |= bit(CATALOG_NONCELL_TO_SELECTED);
                } else if (target_selected) {
                    flags |= bit(NONCATALOG_TO_SELECTED);
                }
            }

            ++assignment_records_;
            if (target_selected) ++per_target_records_[target_it->second];
            Unit *unit = nullptr;
            for (auto &candidate : current_units_) {
                if (candidate.target == target) { unit = &candidate; break; }
            }
            if (!unit) {
                current_units_.push_back(Unit{target, 0});
                unit = &current_units_.back();
            }
            unit->flags |= flags;
        }
        flush_read();
        if (!std::cin.eof()) fail("input FASTQ stream failed before EOF");
        write_outputs();
    }

private:
    bool in_catalog(std::uint32_t code) const {
        return std::binary_search(catalog_.begin(), catalog_.end(), code);
    }

    void flush_read() {
        if (current_read_.empty()) return;
        if (args_.check_reentry) {
            bool inserted = false;
            if (ont_ids_) inserted = closed_ont_ids_.insert(parse_uuid_lossless(current_read_)).second;
            else inserted = closed_pb_ids_.insert(current_read_).second;
            if (!inserted) {
                ++grouping_reentries_;
                fail("physical read ID re-entered after its contiguous group ended: " + current_read_);
            }
        }
        ++unique_reads_;
        if (current_units_.size() > 1) ++multi_target_reads_;
        for (const Unit &unit : current_units_) {
            auto it = target_index_.find(unit.target);
            for (unsigned f = 0; f < NFLAGS; ++f) {
                if (unit.flags & (Mask{1} << f)) {
                    ++unit_counts_[f];
                    if (it != target_index_.end()) ++per_target_[it->second][f];
                }
            }
        }
        current_units_.clear();
        current_read_.clear();
    }

    static void write_header(std::ofstream &out) {
        out << "dataset\ttool\tscope\tassignment_records\tunique_physical_reads\tmulti_target_physical_reads"
            << "\tunique_read_target_assignments_O\tnative_exact\tall_corrected\tselected_source_changed"
            << "\tmissed_cellranger_to_selected\tcellranger_to_different_cellranger_K\tconsensus_cross_line_X"
            << "\tconsensus_same_line_different_cell\tconsensus_label_incomplete\tcatalog_noncell_to_selected_A"
            << "\tnoncatalog_to_selected\traw_source_unavailable\tK_over_O\tX_over_O\tK_plus_A_over_O"
            << "\tX_excess_over_guarded\tK_excess_over_guarded\tK_plus_A_excess_over_guarded\n";
    }

    void write_outputs() {
        fs::create_directories(args_.outdir);
        {
            std::ofstream out(args_.outdir / "summary.tsv");
            if (!out) fail("cannot write summary.tsv");
            write_header(out);
            const auto O = unit_counts_[ALL], K = unit_counts_[CELLRANGER_TO_DIFFERENT_CELLRANGER];
            const auto X = unit_counts_[CONSENSUS_CROSS_LINE], A = unit_counts_[CATALOG_NONCELL_TO_SELECTED];
            out << args_.dataset << "\trad\tcomplete_input\t" << assignment_records_ << '\t' << unique_reads_ << '\t'
                << multi_target_reads_ << '\t' << O << '\t' << unit_counts_[NATIVE_EXACT] << '\t'
                << unit_counts_[ALL_CORRECTED] << '\t' << unit_counts_[SELECTED_SOURCE_CHANGED] << '\t'
                << unit_counts_[MISSED_CELLRANGER_TO_SELECTED] << '\t' << K << '\t' << X << '\t'
                << unit_counts_[CONSENSUS_SAME_LINE_DIFFERENT_CELL] << '\t' << unit_counts_[CONSENSUS_LABEL_INCOMPLETE] << '\t'
                << A << '\t' << unit_counts_[NONCATALOG_TO_SELECTED] << '\t' << unit_counts_[RAW_SOURCE_UNAVAILABLE] << '\t'
                << fmt_ratio(K, O) << '\t' << fmt_ratio(X, O) << '\t' << fmt_ratio(K + A, O) << '\t'
                << fmt_excess(X, O) << '\t' << fmt_excess(K, O) << '\t' << fmt_excess(K + A, O) << '\n';
        }
        {
            std::ofstream out(args_.outdir / "per_target.tsv");
            if (!out) fail("cannot write per_target.tsv");
            out << "target_barcode\ttarget_consensus_label\tassignment_records\tunique_read_target_assignments_O"
                << "\tnative_exact\tall_corrected\tmissed_cellranger_to_selected\tcellranger_to_different_cellranger_K"
                << "\tconsensus_same_line_different_cell\tconsensus_cross_line_X\tconsensus_label_incomplete"
                << "\tcatalog_noncell_to_selected_A\tnoncatalog_to_selected\traw_source_unavailable"
                << "\tK_over_O\tX_over_O\tK_plus_A_over_O\tX_excess_over_guarded\tK_excess_over_guarded"
                << "\tK_plus_A_excess_over_guarded\n";
            for (std::size_t i = 0; i < selected_codes_.size(); ++i) {
                const std::uint32_t code = selected_codes_[i];
                const Counts &c = per_target_[i];
                const auto O = c[ALL], K = c[CELLRANGER_TO_DIFFERENT_CELLRANGER];
                const auto X = c[CONSENSUS_CROSS_LINE], A = c[CATALOG_NONCELL_TO_SELECTED];
                auto label = labels_.find(code);
                out << code_barcode(code) << '\t' << (label == labels_.end() ? "UNLABELED" : label->second) << '\t'
                    << per_target_records_[i] << '\t' << O << '\t' << c[NATIVE_EXACT] << '\t' << c[ALL_CORRECTED] << '\t'
                    << c[MISSED_CELLRANGER_TO_SELECTED] << '\t' << K << '\t'
                    << c[CONSENSUS_SAME_LINE_DIFFERENT_CELL] << '\t' << X << '\t' << c[CONSENSUS_LABEL_INCOMPLETE] << '\t'
                    << A << '\t' << c[NONCATALOG_TO_SELECTED] << '\t' << c[RAW_SOURCE_UNAVAILABLE] << '\t'
                    << fmt_ratio(K, O) << '\t' << fmt_ratio(X, O) << '\t' << fmt_ratio(K + A, O) << '\t'
                    << fmt_excess(X, O) << '\t' << fmt_excess(K, O) << '\t' << fmt_excess(K + A, O) << '\n';
            }
        }
        {
            std::ofstream out(args_.outdir / "ct_filter_counts.tsv");
            out << "fastq_records_read\trad_ct_records_seen\trad_ct_records_excluded\tassignment_rows_yielded\trad_reverse_raw_normalized_records\n"
                << fastq_records_ << '\t' << ct_seen_ << '\t' << ct_excluded_ << '\t' << assignment_records_ << '\t'
                << reverse_raw_normalized_ << '\n';
        }
        {
            std::ofstream out(args_.outdir / "invariants.tsv");
            out << "invariant\tstatus\tobserved\texpected\tnote\n";
            auto emit = [&](const std::string &name, bool pass, std::uint64_t observed, const std::string &expected, const std::string &note) {
                out << name << '\t' << (pass ? "PASS" : "FAIL") << '\t' << observed << '\t' << expected << '\t' << note << '\n';
            };
            emit("all_emitted_targets_in_selected_whitelist", target_outside_rows_ == 0, target_outside_rows_, "0", "Every output target must belong to the tool-selected whitelist.");
            emit("selected_source_never_changed", unit_counts_[SELECTED_SOURCE_CHANGED] == 0, unit_counts_[SELECTED_SOURCE_CHANGED], "0", "An exact source already selected by the tool must remain unchanged.");
            emit("selected_whitelist_subset_global_catalog", selected_outside_catalog_ == 0, selected_outside_catalog_, "0", "Selected targets should be valid manufacturer-catalog barcodes.");
            emit("cellranger_filtered_subset_global_catalog", cellranger_outside_catalog_ == 0, cellranger_outside_catalog_, "0", "CellRanger filtered cells should be valid manufacturer barcodes.");
            emit("consensus_labels_subset_cellranger_filtered", labels_outside_cellranger_ == 0, labels_outside_cellranger_, "0", "Consensus labels are only interpreted for filtered cells.");
            emit("unique_read_target_assignments_not_above_records", unit_counts_[ALL] <= assignment_records_, unit_counts_[ALL], "<=" + std::to_string(assignment_records_), "The primary unique unit cannot exceed assignment records.");
            std::uint64_t target_O = 0, target_K = 0;
            for (const Counts &c : per_target_) { target_O += c[ALL]; target_K += c[CELLRANGER_TO_DIFFERENT_CELLRANGER]; }
            emit("target_unique_marginal_reproduces_O", target_O == unit_counts_[ALL], target_O, std::to_string(unit_counts_[ALL]), "Per-target unique counts reproduce global O.");
            emit("target_unique_marginal_reproduces_K", target_K == unit_counts_[CELLRANGER_TO_DIFFERENT_CELLRANGER], target_K, std::to_string(unit_counts_[CELLRANGER_TO_DIFFERENT_CELLRANGER]), "Per-target unique counts reproduce global K.");
            if (args_.check_reentry) {
                out << "physical_read_grouping_nonreentry\tPASS\t" << grouping_reentries_
                    << "\t0\tExact in-memory full-identity grouping proof completed.\n";
            } else {
                out << "physical_read_grouping_nonreentry\tNOT_CHECKED\tASSUMED_CONTIGUOUS\tNOT_APPLICABLE\tExact SQLite jobs independently prove non-reentry.\n";
            }
        }
        {
            std::ofstream out(args_.outdir / "fast_run_metadata.tsv");
            out << "key\tvalue\n"
                << "dataset\t" << args_.dataset << "\nexclude_rad_ct\t" << (args_.exclude_ct ? 1 : 0)
                << "\nfastq_records_read\t" << fastq_records_ << "\nassignment_records\t" << assignment_records_
                << "\nprimary_unit\t(physical_read_id,target_barcode)"
                << "\ngrouping_check\t" << (args_.check_reentry ? "exact_in_memory" : "assume_contiguous")
                << "\ngrouping_identity\t" << (ont_ids_ ? "lossless_uuid128" : "exact_full_string") << '\n';
        }
        const bool passed = target_outside_rows_ == 0 && unit_counts_[SELECTED_SOURCE_CHANGED] == 0 &&
                            selected_outside_catalog_ == 0 && cellranger_outside_catalog_ == 0 &&
                            labels_outside_cellranger_ == 0 && unit_counts_[ALL] <= assignment_records_;
        if (!passed) fail("one or more required invariants failed; outputs retained without DONE");
        std::ofstream(args_.outdir / "DONE") << "complete\n";
    }

    Args args_;
    std::unordered_set<std::uint32_t> selected_;
    std::unordered_set<std::uint32_t> cellranger_;
    std::vector<std::uint32_t> catalog_;
    std::unordered_map<std::uint32_t, std::string> labels_;
    std::vector<std::uint32_t> selected_codes_;
    std::unordered_map<std::uint32_t, std::size_t> target_index_;
    Counts unit_counts_{};
    std::vector<Counts> per_target_;
    std::vector<std::uint64_t> per_target_records_;
    std::string current_read_;
    std::vector<Unit> current_units_;
    std::uint64_t fastq_records_ = 0, ct_seen_ = 0, ct_excluded_ = 0, reverse_raw_normalized_ = 0;
    std::uint64_t assignment_records_ = 0, unique_reads_ = 0, multi_target_reads_ = 0;
    std::uint64_t target_outside_rows_ = 0, selected_outside_catalog_ = 0;
    std::uint64_t cellranger_outside_catalog_ = 0, labels_outside_cellranger_ = 0;
    bool ont_ids_ = false;
    std::unordered_set<Uuid128, Uuid128Hash> closed_ont_ids_;
    std::unordered_set<std::string> closed_pb_ids_;
    std::uint64_t grouping_reentries_ = 0;
};

static Args parse_args(int argc, char **argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        std::string key = argv[i];
        auto value = [&]() -> std::string {
            if (++i >= argc) fail("missing value after " + key);
            return argv[i];
        };
        if (key == "--dataset") args.dataset = value();
        else if (key == "--selected") args.selected = value();
        else if (key == "--cellranger") args.cellranger = value();
        else if (key == "--catalog-u32") args.catalog_u32 = value();
        else if (key == "--label-dir") args.label_dir = value();
        else if (key == "--outdir") args.outdir = value();
        else if (key == "--exclude-ct") args.exclude_ct = true;
        else if (key == "--check-reentry") args.check_reentry = true;
        else if (key == "--expected-groups") args.expected_groups = std::stoull(value());
        else fail("unknown argument: " + key);
    }
    if (args.dataset.empty() || args.selected.empty() || args.cellranger.empty() ||
        args.catalog_u32.empty() || args.label_dir.empty() || args.outdir.empty()) {
        fail("required: --dataset --selected --cellranger --catalog-u32 --label-dir --outdir [--exclude-ct] [--check-reentry --expected-groups N]");
    }
    return args;
}

int main(int argc, char **argv) {
    try {
        Analyzer(parse_args(argc, argv)).run();
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "fast_rad_raw_audit: " << error.what() << '\n';
        return 1;
    }
}
