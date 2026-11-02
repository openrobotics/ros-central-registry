"""gloo/config.h's values (CMakeLists.txt's project version and options)."""

_CONFIG = {
    "GLOO_HAVE_TRANSPORT_IBVERBS": False,
    "GLOO_HAVE_TRANSPORT_TCP_TLS": False,
    "GLOO_USE_AVX": False,
    "GLOO_USE_CUDA": False,
    "GLOO_USE_IBVERBS": False,
    "GLOO_USE_MPI": False,
    "GLOO_USE_NCCL": False,
    "GLOO_USE_RCCL": False,
    "GLOO_USE_REDIS": False,
    "GLOO_USE_ROCM": False,
    # Only gloo's CUDA collectives use PyTorch's types.
    "GLOO_USE_TORCH_DTYPES": False,
}

def gloo_config_substitutions(linux):
    """The substitutions of gloo/config.h.in.

    Args:
        linux: Whether the target is Linux (the TCP transport), or not (the
            libuv transport).

    Returns:
        A dict for expand_template.
    """
    config = _CONFIG | {
        "GLOO_HAVE_TRANSPORT_TCP": linux,
        "GLOO_HAVE_TRANSPORT_UV": not linux,
        "GLOO_USE_LIBUV": not linux,
    }
    return {
        "@GLOO_VERSION_MAJOR@": "0",
        "@GLOO_VERSION_MINOR@": "5",
        "@GLOO_VERSION_PATCH@": "0",
    } | {
        "#cmakedefine01 {}\n".format(name): "#define {} {}\n".format(name, 1 if enabled else 0)
        for name, enabled in config.items()
    }
