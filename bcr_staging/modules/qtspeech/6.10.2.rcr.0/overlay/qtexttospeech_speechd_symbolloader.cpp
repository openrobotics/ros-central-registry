// Written for the @qtspeech overlay: resolves libspeechd.so.2 symbols at
// runtime via QLibrary, so the SpeechDispatcher TTS plugin builds hermetically
// without linking a host libspeechd.
#include <libspeechd.h>
#include <QtCore/QLibrary>

namespace {

struct SpeechdSymbols {
    QLibrary lib;
    bool loaded = false;

    decltype(&::spd_open) p_spd_open = nullptr;
    decltype(&::spd_close) p_spd_close = nullptr;
    decltype(&::spd_say) p_spd_say = nullptr;
    decltype(&::spd_cancel_all) p_spd_cancel_all = nullptr;
    decltype(&::spd_pause_all) p_spd_pause_all = nullptr;
    decltype(&::spd_resume_all) p_spd_resume_all = nullptr;
    decltype(&::spd_set_notification_on) p_spd_set_notification_on = nullptr;
    decltype(&::spd_set_voice_pitch) p_spd_set_voice_pitch = nullptr;
    decltype(&::spd_get_voice_pitch) p_spd_get_voice_pitch = nullptr;
    decltype(&::spd_set_voice_rate) p_spd_set_voice_rate = nullptr;
    decltype(&::spd_get_voice_rate) p_spd_get_voice_rate = nullptr;
    decltype(&::spd_set_volume) p_spd_set_volume = nullptr;
    decltype(&::spd_get_volume) p_spd_get_volume = nullptr;
    decltype(&::spd_set_language) p_spd_set_language = nullptr;
    decltype(&::spd_set_output_module) p_spd_set_output_module = nullptr;
    decltype(&::spd_get_output_module) p_spd_get_output_module = nullptr;
    decltype(&::spd_set_synthesis_voice) p_spd_set_synthesis_voice = nullptr;
    decltype(&::spd_list_modules) p_spd_list_modules = nullptr;
    decltype(&::spd_list_synthesis_voices) p_spd_list_synthesis_voices = nullptr;
    decltype(&::free_spd_voices) p_free_spd_voices = nullptr;
    decltype(&::free_spd_modules) p_free_spd_modules = nullptr;

    SpeechdSymbols() : lib(QStringLiteral("speechd"), 2) {
        if (!lib.load()) {
            lib.setFileName(QStringLiteral("libspeechd.so.2"));
            lib.load();
        }
        if (lib.isLoaded()) {
            p_spd_open = reinterpret_cast<decltype(p_spd_open)>(lib.resolve("spd_open"));
            p_spd_close = reinterpret_cast<decltype(p_spd_close)>(lib.resolve("spd_close"));
            p_spd_say = reinterpret_cast<decltype(p_spd_say)>(lib.resolve("spd_say"));
            p_spd_cancel_all = reinterpret_cast<decltype(p_spd_cancel_all)>(lib.resolve("spd_cancel_all"));
            p_spd_pause_all = reinterpret_cast<decltype(p_spd_pause_all)>(lib.resolve("spd_pause_all"));
            p_spd_resume_all = reinterpret_cast<decltype(p_spd_resume_all)>(lib.resolve("spd_resume_all"));
            p_spd_set_notification_on = reinterpret_cast<decltype(p_spd_set_notification_on)>(lib.resolve("spd_set_notification_on"));
            p_spd_set_voice_pitch = reinterpret_cast<decltype(p_spd_set_voice_pitch)>(lib.resolve("spd_set_voice_pitch"));
            p_spd_get_voice_pitch = reinterpret_cast<decltype(p_spd_get_voice_pitch)>(lib.resolve("spd_get_voice_pitch"));
            p_spd_set_voice_rate = reinterpret_cast<decltype(p_spd_set_voice_rate)>(lib.resolve("spd_set_voice_rate"));
            p_spd_get_voice_rate = reinterpret_cast<decltype(p_spd_get_voice_rate)>(lib.resolve("spd_get_voice_rate"));
            p_spd_set_volume = reinterpret_cast<decltype(p_spd_set_volume)>(lib.resolve("spd_set_volume"));
            p_spd_get_volume = reinterpret_cast<decltype(p_spd_get_volume)>(lib.resolve("spd_get_volume"));
            p_spd_set_language = reinterpret_cast<decltype(p_spd_set_language)>(lib.resolve("spd_set_language"));
            p_spd_set_output_module = reinterpret_cast<decltype(p_spd_set_output_module)>(lib.resolve("spd_set_output_module"));
            p_spd_get_output_module = reinterpret_cast<decltype(p_spd_get_output_module)>(lib.resolve("spd_get_output_module"));
            p_spd_set_synthesis_voice = reinterpret_cast<decltype(p_spd_set_synthesis_voice)>(lib.resolve("spd_set_synthesis_voice"));
            p_spd_list_modules = reinterpret_cast<decltype(p_spd_list_modules)>(lib.resolve("spd_list_modules"));
            p_spd_list_synthesis_voices = reinterpret_cast<decltype(p_spd_list_synthesis_voices)>(lib.resolve("spd_list_synthesis_voices"));
            p_free_spd_voices = reinterpret_cast<decltype(p_free_spd_voices)>(lib.resolve("free_spd_voices"));
            p_free_spd_modules = reinterpret_cast<decltype(p_free_spd_modules)>(lib.resolve("free_spd_modules"));
            loaded = p_spd_open && p_spd_close && p_spd_say;
        }
    }
};

SpeechdSymbols &syms() {
    static SpeechdSymbols s;
    return s;
}

} // namespace

extern "C" {

SPDConnection *spd_open(const char *client_name, const char *connection_name, const char *user_name, SPDConnectionMode mode) {
    return syms().p_spd_open ? syms().p_spd_open(client_name, connection_name, user_name, mode) : nullptr;
}

void spd_close(SPDConnection *connection) {
    if (syms().p_spd_close) syms().p_spd_close(connection);
}

int spd_say(SPDConnection *connection, SPDPriority priority, const char *text) {
    return syms().p_spd_say ? syms().p_spd_say(connection, priority, text) : -1;
}

int spd_cancel_all(SPDConnection *connection) {
    return syms().p_spd_cancel_all ? syms().p_spd_cancel_all(connection) : -1;
}

int spd_pause_all(SPDConnection *connection) {
    return syms().p_spd_pause_all ? syms().p_spd_pause_all(connection) : -1;
}

int spd_resume_all(SPDConnection *connection) {
    return syms().p_spd_resume_all ? syms().p_spd_resume_all(connection) : -1;
}

int spd_set_notification_on(SPDConnection *connection, SPDNotification notification) {
    return syms().p_spd_set_notification_on ? syms().p_spd_set_notification_on(connection, notification) : -1;
}

int spd_set_voice_pitch(SPDConnection *connection, signed int pitch) {
    return syms().p_spd_set_voice_pitch ? syms().p_spd_set_voice_pitch(connection, pitch) : -1;
}

int spd_get_voice_pitch(SPDConnection *connection) {
    return syms().p_spd_get_voice_pitch ? syms().p_spd_get_voice_pitch(connection) : 0;
}

int spd_set_voice_rate(SPDConnection *connection, signed int rate) {
    return syms().p_spd_set_voice_rate ? syms().p_spd_set_voice_rate(connection, rate) : -1;
}

int spd_get_voice_rate(SPDConnection *connection) {
    return syms().p_spd_get_voice_rate ? syms().p_spd_get_voice_rate(connection) : 0;
}

int spd_set_volume(SPDConnection *connection, signed int volume) {
    return syms().p_spd_set_volume ? syms().p_spd_set_volume(connection, volume) : -1;
}

int spd_get_volume(SPDConnection *connection) {
    return syms().p_spd_get_volume ? syms().p_spd_get_volume(connection) : 0;
}

int spd_set_language(SPDConnection *connection, const char *language) {
    return syms().p_spd_set_language ? syms().p_spd_set_language(connection, language) : -1;
}

int spd_set_output_module(SPDConnection *connection, const char *output_module) {
    return syms().p_spd_set_output_module ? syms().p_spd_set_output_module(connection, output_module) : -1;
}

char *spd_get_output_module(SPDConnection *connection) {
    return syms().p_spd_get_output_module ? syms().p_spd_get_output_module(connection) : nullptr;
}

int spd_set_synthesis_voice(SPDConnection *connection, const char *voice_name) {
    return syms().p_spd_set_synthesis_voice ? syms().p_spd_set_synthesis_voice(connection, voice_name) : -1;
}

char **spd_list_modules(SPDConnection *connection) {
    return syms().p_spd_list_modules ? syms().p_spd_list_modules(connection) : nullptr;
}

SPDVoice **spd_list_synthesis_voices(SPDConnection *connection) {
    return syms().p_spd_list_synthesis_voices ? syms().p_spd_list_synthesis_voices(connection) : nullptr;
}

void free_spd_voices(SPDVoice **voices) {
    if (syms().p_free_spd_voices) syms().p_free_spd_voices(voices);
}

void free_spd_modules(char **modules) {
    if (syms().p_free_spd_modules) syms().p_free_spd_modules(modules);
}

} // extern "C"
