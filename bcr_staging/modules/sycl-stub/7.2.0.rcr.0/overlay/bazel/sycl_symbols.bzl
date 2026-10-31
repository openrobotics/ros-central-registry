"""The libsycl symbols that @libtorch's XPU backend links (mangled for libc++).

Every one aborts when called (see //:sycl): without SYCL platforms, PyTorch
calls none of them. Update with the undefined sycl::_V1 symbols of
@libtorch//:c10_xpu and @libtorch//:torch_xpu, less those that
bazel/sycl_stub.cc defines.
"""

SYCL_STUB_SYMBOLS = [
    "_ZN4sycl3_V118aligned_alloc_hostEmmRKNS0_7contextERKNS0_6detail13code_locationE",  # sycl::_V1::aligned_alloc_host(unsigned long, unsigned long,
    "_ZN4sycl3_V118get_pointer_deviceEPKvRKNS0_7contextE",  # sycl::_V1::get_pointer_device(void const*, sycl::_V1::contex
    "_ZN4sycl3_V120aligned_alloc_deviceEmmRKNS0_6deviceERKNS0_7contextERKNS0_6detail13code_locationE",  # sycl::_V1::aligned_alloc_device(unsigned long, unsigned long
    "_ZN4sycl3_V135submit_graph_direct_with_event_implERKNS0_5queueERNS0_3ext6oneapi12experimental13command_graphILNS6_11graph_stateE1EEENS0_4spanIKNS0_5eventELm18446744073709551615EEERKNS0_6detail13code_locationE",  # sycl::_V1::submit_graph_direct_with_event_impl(sycl::_V1::qu
    "_ZN4sycl3_V13ext6oneapi12experimental10ipc_memory3getEPvRKNS0_7contextE",  # sycl::_V1::ext::oneapi::experimental::ipc_memory::get(void*,
    "_ZN4sycl3_V13ext6oneapi12experimental10ipc_memory5closeEPvRKNS0_7contextE",  # sycl::_V1::ext::oneapi::experimental::ipc_memory::close(void
    "_ZN4sycl3_V13ext6oneapi12experimental12physical_memC1ERKNS0_6deviceERKNS0_7contextEm",  # sycl::_V1::ext::oneapi::experimental::physical_mem::physical
    "_ZN4sycl3_V13ext6oneapi12experimental16free_virtual_memEmmRKNS0_7contextE",  # sycl::_V1::ext::oneapi::experimental::free_virtual_mem(unsig
    "_ZN4sycl3_V13ext6oneapi12experimental19get_mem_granularityERKNS0_6deviceERKNS0_7contextENS3_16granularity_modeE",  # sycl::_V1::ext::oneapi::experimental::get_mem_granularity(sy
    "_ZN4sycl3_V13ext6oneapi12experimental19reserve_virtual_memEmmRKNS0_7contextE",  # sycl::_V1::ext::oneapi::experimental::reserve_virtual_mem(un
    "_ZN4sycl3_V13ext6oneapi12experimental20enqueue_signal_eventENS0_5queueERNS0_5eventE",  # sycl::_V1::ext::oneapi::experimental::enqueue_signal_event(s
    "_ZN4sycl3_V13ext6oneapi12experimental5unmapEPKvmRKNS0_7contextE",  # sycl::_V1::ext::oneapi::experimental::unmap(void const*, uns
    "_ZN4sycl3_V13ext6oneapi12experimental6detail10make_eventERKNS0_7contextEj",  # sycl::_V1::ext::oneapi::experimental::detail::make_event(syc
    "_ZN4sycl3_V13ext6oneapi12experimental6detail24modifiable_command_graph13end_recordingEv",  # sycl::_V1::ext::oneapi::experimental::detail::modifiable_com
    "_ZN4sycl3_V13ext6oneapi12experimental6detail24modifiable_command_graph15begin_recordingERNS0_5queueERKNS0_13property_listE",  # sycl::_V1::ext::oneapi::experimental::detail::modifiable_com
    "_ZN4sycl3_V13ext6oneapi12experimental6detail24modifiable_command_graphC2ERKNS0_5queueERKNS0_13property_listE",  # sycl::_V1::ext::oneapi::experimental::detail::modifiable_com
    "_ZN4sycl3_V14freeEPvRKNS0_7contextERKNS0_6detail13code_locationE",  # sycl::_V1::free(void*, sycl::_V1::context const&, sycl::_V1:
    "_ZN4sycl3_V15event14wait_and_throwEv",  # sycl::_V1::event::wait_and_throw()
    "_ZN4sycl3_V15event4waitEv",  # sycl::_V1::event::wait()
    "_ZN4sycl3_V15queue10wait_proxyERKNS0_6detail13code_locationE",  # sycl::_V1::queue::wait_proxy(sycl::_V1::detail::code_locatio
    "_ZN4sycl3_V15queue20wait_and_throw_proxyERKNS0_6detail13code_locationE",  # sycl::_V1::queue::wait_and_throw_proxy(sycl::_V1::detail::co
    "_ZN4sycl3_V15queue25ext_oneapi_submit_barrierERKNS0_6detail13code_locationE",  # sycl::_V1::queue::ext_oneapi_submit_barrier(sycl::_V1::detai
    "_ZN4sycl3_V15queue25ext_oneapi_submit_barrierERKNSt3__16vectorINS0_5eventENS2_9allocatorIS4_EEEERKNS0_6detail13code_locationE",  # sycl::_V1::queue::ext_oneapi_submit_barrier(std::vector<sycl
    "_ZN4sycl3_V15queue6memcpyEPvPKvmRKNS0_6detail13code_locationE",  # sycl::_V1::queue::memcpy(void*, void const*, unsigned long,
    "_ZN4sycl3_V15queueC1ERKNS0_7contextERKNS0_6deviceERKNSt3__18functionIFvNS0_14exception_listEEEERKNS0_13property_listE",  # sycl::_V1::queue::queue(sycl::_V1::context const&, sycl::_V1
    "_ZN4sycl3_V16detail14tls_code_loc_t5queryEv",  # sycl::_V1::detail::tls_code_loc_t::query()
    "_ZN4sycl3_V16detail14tls_code_loc_tC1ERKNS1_13code_locationE",  # sycl::_V1::detail::tls_code_loc_t::tls_code_loc_t(sycl::_V1:
    "_ZN4sycl3_V16detail14tls_code_loc_tD1Ev",  # sycl::_V1::detail::tls_code_loc_t::~tls_code_loc_t()
    "_ZN4sycl3_V16detail16get_pointer_typeEPKvRNS1_12context_implE",  # sycl::_V1::detail::get_pointer_type(void const*, sycl::_V1::
    "_ZN4sycl3_V16detail16openIPCMemHandleEPKSt4bytemRKNS0_7contextERKNS0_6deviceE",  # sycl::_V1::detail::openIPCMemHandle(std::byte const*, unsign
    "_ZN4sycl3_V16device15ext_oneapi_waitEv",  # sycl::_V1::device::ext_oneapi_wait()
    "_ZN4sycl3_V16device26ext_oneapi_can_access_peerERKS1_NS0_3ext6oneapi11peer_accessE",  # sycl::_V1::device::ext_oneapi_can_access_peer(sycl::_V1::dev
    "_ZN4sycl3_V16device29ext_oneapi_enable_peer_accessERKS1_",  # sycl::_V1::device::ext_oneapi_enable_peer_access(sycl::_V1::
    "_ZN4sycl3_V16device29ext_oneapi_throw_asynchronousEv",  # sycl::_V1::device::ext_oneapi_throw_asynchronous()
    "_ZN4sycl3_V16deviceC1ERKS1_",  # sycl::_V1::device::device(sycl::_V1::device const&)
    "_ZN4sycl3_V17handler7setTypeENS0_6detail6CGTypeE",  # sycl::_V1::handler::setType(sycl::_V1::detail::CGType)
    "_ZNK4sycl3_V13ext6oneapi12experimental12physical_mem3mapEmmNS3_19address_access_modeEm",  # sycl::_V1::ext::oneapi::experimental::physical_mem::map(unsi
    "_ZNK4sycl3_V13ext6oneapi12experimental6detail24modifiable_command_graph11print_graphENS0_6detail11string_viewEb",  # sycl::_V1::ext::oneapi::experimental::detail::modifiable_com
    "_ZNK4sycl3_V13ext6oneapi12experimental6detail24modifiable_command_graph5emptyEv",  # sycl::_V1::ext::oneapi::experimental::detail::modifiable_com
    "_ZNK4sycl3_V13ext6oneapi12experimental6detail24modifiable_command_graph8finalizeERKNS0_13property_listE",  # sycl::_V1::ext::oneapi::experimental::detail::modifiable_com
    "_ZNK4sycl3_V15event18get_profiling_infoINS0_4info15event_profiling11command_endEEENS0_6detail28is_event_profiling_info_descIT_E11return_typeEv",  # sycl::_V1::detail::is_event_profiling_info_desc<sycl::_V1::i
    "_ZNK4sycl3_V15event8get_infoINS0_4info5event24command_execution_statusEEENS0_6detail18is_event_info_descIT_E11return_typeEv",  # sycl::_V1::detail::is_event_info_desc<sycl::_V1::info::event
    "_ZNK4sycl3_V15queue10get_deviceEv",  # sycl::_V1::queue::get_device() const
    "_ZNK4sycl3_V15queue11getPropListEv",  # sycl::_V1::queue::getPropList() const
    "_ZNK4sycl3_V15queue11get_contextEv",  # sycl::_V1::queue::get_context() const
    "_ZNK4sycl3_V15queue11is_in_orderEv",  # sycl::_V1::queue::is_in_order() const
    "_ZNK4sycl3_V15queue16ext_oneapi_emptyEv",  # sycl::_V1::queue::ext_oneapi_empty() const
    "_ZNK4sycl3_V15queue20ext_oneapi_get_stateEv",  # sycl::_V1::queue::ext_oneapi_get_state() const
    "_ZNK4sycl3_V15queue22submit_with_event_implERKNS0_6detail19type_erased_cgfo_tyERKNS2_3_V114SubmissionInfoERKNS2_13code_locationEb",  # sycl::_V1::queue::submit_with_event_impl(sycl::_V1::detail::
    "_ZNK4sycl3_V16device12get_platformEv",  # sycl::_V1::device::get_platform() const
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device11free_memoryEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device12gpu_eu_countEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device14xe_stack_countEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device15eus_per_xe_coreEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device16memory_bus_widthEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device17gpu_eu_simd_widthEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device17memory_clock_rateEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device20xe_cores_per_clusterEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device20xe_regions_per_stackEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device21gpu_hw_threads_per_euEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device22xe_clusters_per_regionEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device23max_lanes_per_hw_threadEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device25gpu_eu_count_per_subsliceEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device4uuidEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext5intel4info6device9device_idEEENS0_6detail11ABINeutralTINS8_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_3ext6oneapi12experimental4info6device12architectureEEENS0_6detail11ABINeutralTINS9_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device11device_typeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device12address_bitsEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device12is_availableEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device14driver_versionEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device14half_fp_configEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device14local_mem_sizeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device14local_mem_typeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device15global_mem_sizeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device15sub_group_sizesEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device16double_fp_configEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device16single_fp_configEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device17max_compute_unitsEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device18max_mem_alloc_sizeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device18max_num_sub_groupsEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device18max_parameter_sizeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device19max_clock_frequencyEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device19max_work_group_sizeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device19mem_base_addr_alignEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device21global_mem_cache_sizeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device21global_mem_cache_typeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device23native_vector_width_intEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device24max_work_item_dimensionsEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device24native_vector_width_charEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device24native_vector_width_halfEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device24native_vector_width_longEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device25native_vector_width_floatEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device25native_vector_width_shortEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device25partition_max_sub_devicesEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device26global_mem_cache_line_sizeEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device26native_vector_width_doubleEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device26preferred_vector_width_intEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device26profiling_timer_resolutionEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device27preferred_vector_width_charEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device27preferred_vector_width_halfEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device27preferred_vector_width_longEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device28preferred_vector_width_floatEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device28preferred_vector_width_shortEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device29preferred_vector_width_doubleEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device4nameEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device6vendorEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device7versionEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device13get_info_implINS0_4info6device8platformEEENS0_6detail11ABINeutralTINS6_19is_device_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_device_
    "_ZNK4sycl3_V16device32ext_oneapi_supports_cl_extensionENS0_6detail11string_viewEPNS0_3ext6oneapi12experimental10cl_versionE",  # sycl::_V1::device::ext_oneapi_supports_cl_extension(sycl::_V
    "_ZNK4sycl3_V16device3hasENS0_6aspectE",  # sycl::_V1::device::has(sycl::_V1::aspect) const
    "_ZNK4sycl3_V16device6is_gpuEv",  # sycl::_V1::device::is_gpu() const
    "_ZNK4sycl3_V17handler7getTypeEv",  # sycl::_V1::handler::getType() const
    "_ZNK4sycl3_V18platform11get_backendEv",  # sycl::_V1::platform::get_backend() const
    "_ZNK4sycl3_V18platform11get_devicesENS0_4info11device_typeE",  # sycl::_V1::platform::get_devices(sycl::_V1::info::device_typ
    "_ZNK4sycl3_V18platform13get_info_implINS0_4info8platform4nameEEENS0_6detail11ABINeutralTINS6_21is_platform_info_descIT_E11return_typeEE4typeEv",  # sycl::_V1::detail::ABINeutralT<sycl::_V1::detail::is_platfor
    "_ZNK4sycl3_V18platform23khr_get_default_contextEv",  # sycl::_V1::platform::khr_get_default_context() const
]
