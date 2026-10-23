// Minimal Speech Dispatcher C API header for the hermetic QtTextToSpeech
// SpeechDispatcher plugin build. Written for this overlay rather than copied,
// but it reproduces declarations from speechd 0.11.5's public API
// (src/api/c/libspeechd.h and include/speechd_types.h): the enum values,
// SPDVoice, and the public callback fields at the start of SPDConnection
// (the private fields are omitted; Qt only writes the callbacks). It is
// therefore licensed like upstream, LGPL-2.1-or-later. libspeechd.so.2 is
// resolved at runtime (see qtexttospeech_speechd_symbolloader.cpp).
#ifndef LIBSPEECHD_H
#define LIBSPEECHD_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define LIBSPEECHD_MAJOR_VERSION 0
#define LIBSPEECHD_MINOR_VERSION 11
#define LIBSPEECHD_MICRO_VERSION 0

typedef enum {
    SPD_MODE_SINGLE = 0,
    SPD_MODE_THREADED = 1
} SPDConnectionMode;

typedef enum {
    SPD_IMPORTANT = 1,
    SPD_MESSAGE = 2,
    SPD_TEXT = 3,
    SPD_NOTIFICATION = 4,
    SPD_PROGRESS = 5
} SPDPriority;

typedef enum {
    SPD_BEGIN = 1,
    SPD_END = 2,
    SPD_INDEX_MARKS = 4,
    SPD_CANCEL = 8,
    SPD_PAUSE = 16,
    SPD_RESUME = 32,
    SPD_ALL = 0x3f
} SPDNotification;

typedef enum {
    SPD_EVENT_BEGIN,
    SPD_EVENT_END,
    SPD_EVENT_INDEX_MARK,
    SPD_EVENT_CANCEL,
    SPD_EVENT_PAUSE,
    SPD_EVENT_RESUME
} SPDNotificationType;

typedef struct {
    char *name;
    char *language;
    char *variant;
} SPDVoice;

typedef void (*SPDCallback)(size_t msg_id, size_t client_id, SPDNotificationType state);
typedef void (*SPDCallbackIM)(size_t msg_id, size_t client_id, SPDNotificationType state, char *index_mark);

typedef struct {
    SPDCallback callback_begin;
    SPDCallback callback_end;
    SPDCallback callback_cancel;
    SPDCallback callback_pause;
    SPDCallback callback_resume;
    SPDCallbackIM callback_im;
    int socket;
    void *stream;
    SPDConnectionMode mode;
    void *td;
    void *reply;
} SPDConnection;

SPDConnection *spd_open(const char *client_name, const char *connection_name, const char *user_name, SPDConnectionMode mode);
void spd_close(SPDConnection *connection);
int spd_say(SPDConnection *connection, SPDPriority priority, const char *text);
int spd_cancel_all(SPDConnection *connection);
int spd_pause_all(SPDConnection *connection);
int spd_resume_all(SPDConnection *connection);
int spd_set_notification_on(SPDConnection *connection, SPDNotification notification);
int spd_set_voice_pitch(SPDConnection *connection, signed int pitch);
int spd_get_voice_pitch(SPDConnection *connection);
int spd_set_voice_rate(SPDConnection *connection, signed int rate);
int spd_get_voice_rate(SPDConnection *connection);
int spd_set_volume(SPDConnection *connection, signed int volume);
int spd_get_volume(SPDConnection *connection);
int spd_set_language(SPDConnection *connection, const char *language);
int spd_set_output_module(SPDConnection *connection, const char *output_module);
char *spd_get_output_module(SPDConnection *connection);
int spd_set_synthesis_voice(SPDConnection *connection, const char *voice_name);
char **spd_list_modules(SPDConnection *connection);
SPDVoice **spd_list_synthesis_voices(SPDConnection *connection);
void free_spd_voices(SPDVoice **voices);
void free_spd_modules(char **modules);

#ifdef __cplusplus
}
#endif

#endif // LIBSPEECHD_H
