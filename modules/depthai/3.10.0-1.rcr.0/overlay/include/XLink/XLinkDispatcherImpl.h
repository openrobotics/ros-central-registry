// Copyright (C) 2018-2021 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#ifndef _XLINKDISPATCHERIMPL_H
#define _XLINKDISPATCHERIMPL_H

#include "XLinkPrivateDefines.h"
#include <stdbool.h>

int dispatcherEventSend (xLinkEvent_t*, XLinkTimespec* sendTime);
int dispatcherEventReceive (xLinkEvent_t*);
int dispatcherLocalEventGetResponse (xLinkEvent_t*, xLinkEvent_t*, bool);
int dispatcherRemoteEventGetResponse (xLinkEvent_t*, xLinkEvent_t*, bool);
void dispatcherCloseLink (void* fd, int fullClose);
void dispatcherCloseDeviceFd (xLinkDeviceHandle_t* deviceHandle);

#endif //_XLINKDISPATCHERIMPL_H
