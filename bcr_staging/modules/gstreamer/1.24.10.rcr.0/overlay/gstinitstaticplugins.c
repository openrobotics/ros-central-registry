#include <gst/gst.h>

extern void gst_plugin_coreelements_register (void);
extern void gst_plugin_app_register (void);
extern void gst_plugin_videotestsrc_register (void);
extern void gst_plugin_videoconvertscale_register (void);
extern void gst_plugin_audioconvert_register (void);
extern void gst_plugin_audioresample_register (void);
extern void gst_plugin_playback_register (void);
extern void gst_plugin_typefindfunctions_register (void);
extern void gst_plugin_jpeg_register (void);
extern void gst_plugin_png_register (void);
extern void gst_plugin_wavenc_register (void);
#ifdef __linux__
extern void gst_plugin_alsa_register (void);
#endif

void
gst_init_static_plugins (void)
{
  gst_plugin_coreelements_register ();
  gst_plugin_app_register ();
  gst_plugin_videotestsrc_register ();
  gst_plugin_videoconvertscale_register ();
  gst_plugin_audioconvert_register ();
  gst_plugin_audioresample_register ();
  gst_plugin_playback_register ();
  gst_plugin_typefindfunctions_register ();
  gst_plugin_jpeg_register ();
  gst_plugin_png_register ();
  gst_plugin_wavenc_register ();
#ifdef __linux__
  gst_plugin_alsa_register ();
#endif
  gst_registry_fork_set_enabled (FALSE);
  gst_registry_scan_path (gst_registry_get (), "lib/gstreamer-1.0-plugins");
}

