#ifndef PHIDGET22_H
#define PHIDGET22_H
#ifdef __cplusplus
extern "C" {
#endif

#if defined(__stdcall)
 #define CCONV __stdcall
 #define PHIDGET22_API __declspec(dllimport)
#else
 #if defined(__BORLANDC__) || defined(_MSC_VER)
  #define CCONV __stdcall
  #define PHIDGET22_API __declspec(dllimport)
 #else
  #define CCONV
  #define PHIDGET22_API
 #endif
#endif

#include <stdint.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdlib.h>
/*
 * This file is part of libphidget22
 *
 * Copyright (c) 2015-2022 Phidgets Inc.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from
 *    this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
 * THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef _PHIDGET_CONSTANTS_H_
#define _PHIDGET_CONSTANTS_H_

#define PUNK_BOOL	0x02	   /* Unknown Boolean */
#define PUNK_INT8	INT8_MAX   /* Unknown Short   (8-bit) */
#define PUNK_UINT8	UINT8_MAX  /* Unknown Short   (8-bit unsigned) */
#define PUNK_INT16	INT16_MAX  /* Unknown Short   (16-bit) */
#define PUNK_UINT16 UINT16_MAX /* Unknown Short   (16-bit unsigned) */
#define PUNK_INT32	INT32_MAX  /* Unknown Integer (32-bit) */
#define PUNK_UINT32 UINT32_MAX /* Unknown Integer (32-bit unsigned) */
#define PUNK_INT64	INT64_MAX  /* Unknown Integer (64-bit) */
#define PUNK_UINT64 UINT64_MAX /* Unknown Integer (64-bit unsigned) */
#define PUNK_DBL	1e300	   /* Unknown Double */
#define PUNK_FLT	1e30	   /* Unknown Float */
#define PUNK_ENUM	INT32_MAX  /* Unknown Enum */
#define PUNK_SIZE	SIZE_MAX   /* Unknown size_t */

#define PFALSE		0x00 /* False. Used for boolean values. */
#define PTRUE		0x01 /* True. Used for boolean values. */

#define PRIphid		"P" /* mos_printf format string for printing a PhidgetHandle */

#endif /* _PHIDGET_CONSTANTS_H_ */
#ifndef _PHIDGETCONSTANTS_GEN_H_
#define _PHIDGETCONSTANTS_GEN_H_

#define PHIDGET_SERIALNUMBER_ANY -1	// Pass to ${PROPERTY:DeviceSerialNumber:set} to open any serial number.
#define PHIDGET_HUBPORT_ANY -1	// Pass to ${PROPERTY:HubPort:set} to open any hub port.
#define PHIDGET_CHANNEL_ANY -1	// Pass to ${PROPERTY:Channel:set} to open any channel.
#define PHIDGET_LABEL_ANY NULL	// Pass to ${PROPERTY:DeviceLabel:set} to open any label.
#define PHIDGET_TIMEOUT_INFINITE 0x0	// Pass to ${METHOD:openWaitForAttachment} for an infinite timeout.
#define PHIDGET_TIMEOUT_DEFAULT 0x3e8	// Pass to ${METHOD:openWaitForAttachment} for the default timeout.
#define PHIDGET_HUBPORTSPEED_AUTO 0x0	// Pass to ${PROPERTY:HubPortSpeed:set} to set the Hub Port speed automatically when supported by both the hub port and the VINT device.
#define PHIDGETSERVER_AUTHREQUIRED 0x1	// PhidgetServer flag indicating that the server requires a password to authenticate
#define IR_RAWDATA_LONGSPACE 0xffffffff	// The value for a long space in raw data
#define IR_MAX_CODE_BIT_COUNT 0x80	// Maximum bit count for sent / received data
#define IR_MAX_CODE_STR_LENGTH 0x21	// Maximum bit count for sent / received data

#endif /* _PHIDGETCONSTANTS_GEN_H_ */
typedef enum {
 ENCODER_IO_MODE_PUSH_PULL = 0x1,
 ENCODER_IO_MODE_LINE_DRIVER_2K2 = 0x2,
 ENCODER_IO_MODE_LINE_DRIVER_10K = 0x3,
 ENCODER_IO_MODE_OPEN_COLLECTOR_2K2 = 0x4,
 ENCODER_IO_MODE_OPEN_COLLECTOR_10K = 0x5,
} Phidget_EncoderIOMode;
typedef enum {
 EPHIDGET_OK = 0x0,
 EPHIDGET_PERM = 0x1,
 EPHIDGET_NOENT = 0x2,
 EPHIDGET_TIMEOUT = 0x3,
 EPHIDGET_KEEPALIVE = 0x3a,
 EPHIDGET_INTERRUPTED = 0x4,
 EPHIDGET_IO = 0x5,
 EPHIDGET_NOMEMORY = 0x6,
 EPHIDGET_ACCESS = 0x7,
 EPHIDGET_FAULT = 0x8,
 EPHIDGET_BUSY = 0x9,
 EPHIDGET_EXIST = 0xa,
 EPHIDGET_NOTDIR = 0xb,
 EPHIDGET_ISDIR = 0xc,
 EPHIDGET_INVALID = 0xd,
 EPHIDGET_NFILE = 0xe,
 EPHIDGET_MFILE = 0xf,
 EPHIDGET_NOSPC = 0x10,
 EPHIDGET_FBIG = 0x11,
 EPHIDGET_ROFS = 0x12,
 EPHIDGET_RO = 0x13,
 EPHIDGET_UNSUPPORTED = 0x14,
 EPHIDGET_INVALIDARG = 0x15,
 EPHIDGET_AGAIN = 0x16,
 EPHIDGET_NOTEMPTY = 0x1a,
 EPHIDGET_UNEXPECTED = 0x1c,
 EPHIDGET_DUPLICATE = 0x1b,
 EPHIDGET_BADPASSWORD = 0x25,
 EPHIDGET_NETUNAVAIL = 0x2d,
 EPHIDGET_CONNREF = 0x23,
 EPHIDGET_CONNRESET = 0x2e,
 EPHIDGET_HOSTUNREACH = 0x30,
 EPHIDGET_NODEV = 0x28,
 EPHIDGET_WRONGDEVICE = 0x32,
 EPHIDGET_PIPE = 0x29,
 EPHIDGET_RESOLV = 0x2c,
 EPHIDGET_UNKNOWNVAL = 0x33,
 EPHIDGET_NOTATTACHED = 0x34,
 EPHIDGET_INVALIDPACKET = 0x35,
 EPHIDGET_2BIG = 0x36,
 EPHIDGET_BADVERSION = 0x37,
 EPHIDGET_CLOSED = 0x38,
 EPHIDGET_NOTCONFIGURED = 0x39,
 EPHIDGET_EOF = 0x1f,
 EPHIDGET_FAILSAFE = 0x3b,
 EPHIDGET_UNKNOWNVALHIGH = 0x3c,
 EPHIDGET_UNKNOWNVALLOW = 0x3d,
 EPHIDGET_BADPOWER = 0x3e,
 EPHIDGET_POWERCYCLE = 0x3f,
 EPHIDGET_HALLSENSOR = 0x40,
 EPHIDGET_BADCURRENT = 0x41,
} PhidgetReturnCode;
typedef enum {
 EEPHIDGET_BADVERSION = 0x1,
 EEPHIDGET_BUSY = 0x2,
 EEPHIDGET_NETWORK = 0x3,
 EEPHIDGET_DISPATCH = 0x4,
 EEPHIDGET_FAILURE = 0x5,
 EEPHIDGET_OK = 0x1000,
 EEPHIDGET_OVERRUN = 0x1002,
 EEPHIDGET_PACKETLOST = 0x1003,
 EEPHIDGET_WRAP = 0x1004,
 EEPHIDGET_OVERTEMP = 0x1005,
 EEPHIDGET_OVERCURRENT = 0x1006,
 EEPHIDGET_OUTOFRANGE = 0x1007,
 EEPHIDGET_BADPOWER = 0x1008,
 EEPHIDGET_SATURATION = 0x1009,
 EEPHIDGET_OVERVOLTAGE = 0x100b,
 EEPHIDGET_FAILSAFE = 0x100c,
 EEPHIDGET_VOLTAGEERROR = 0x100d,
 EEPHIDGET_ENERGYDUMP = 0x100e,
 EEPHIDGET_MOTORSTALL = 0x100f,
 EEPHIDGET_INVALIDSTATE = 0x1010,
 EEPHIDGET_BADCONNECTION = 0x1011,
 EEPHIDGET_OUTOFRANGEHIGH = 0x1012,
 EEPHIDGET_OUTOFRANGELOW = 0x1013,
 EEPHIDGET_FAULT = 0x1014,
 EEPHIDGET_ESTOP = 0x1015,
} Phidget_ErrorEventCode;
typedef enum {
 PHIDID_NOTHING = 0x0,
 PHIDID_UNKNOWN = 0x7d,
 PHIDID_DIGITALINPUT_PORT = 0x5f,
 PHIDID_DIGITALOUTPUT_PORT = 0x60,
 PHIDID_VOLTAGEINPUT_PORT = 0x61,
 PHIDID_VOLTAGERATIOINPUT_PORT = 0x62,
 PHIDID_DICTIONARY = 0x6f,
 PHIDID_1000 = 0x2,
 PHIDID_1001 = 0x3,
 PHIDID_1002 = 0x4,
 PHIDID_1008 = 0x5,
 PHIDID_1010_1013_1018_1019 = 0x6,
 PHIDID_1011 = 0x7,
 PHIDID_1012 = 0x8,
 PHIDID_1014 = 0x9,
 PHIDID_1015 = 0xa,
 PHIDID_1016 = 0xb,
 PHIDID_1017 = 0xc,
 PHIDID_1023 = 0xd,
 PHIDID_1024 = 0xe,
 PHIDID_1030 = 0xf,
 PHIDID_1031 = 0x10,
 PHIDID_1032 = 0x11,
 PHIDID_1040 = 0x12,
 PHIDID_1041 = 0x13,
 PHIDID_1042 = 0x14,
 PHIDID_1043 = 0x15,
 PHIDID_1044 = 0x16,
 PHIDID_1045 = 0x17,
 PHIDID_1046 = 0x18,
 PHIDID_1047 = 0x19,
 PHIDID_1048 = 0x1a,
 PHIDID_1049 = 0x1b,
 PHIDID_1051 = 0x1c,
 PHIDID_1052 = 0x1d,
 PHIDID_1053 = 0x1e,
 PHIDID_1054 = 0x1f,
 PHIDID_1055 = 0x20,
 PHIDID_1056 = 0x21,
 PHIDID_1057 = 0x22,
 PHIDID_1058 = 0x23,
 PHIDID_1059 = 0x24,
 PHIDID_1060 = 0x25,
 PHIDID_1061 = 0x26,
 PHIDID_1062 = 0x27,
 PHIDID_1063 = 0x28,
 PHIDID_1064 = 0x29,
 PHIDID_1065 = 0x2a,
 PHIDID_1066 = 0x2b,
 PHIDID_1067 = 0x2c,
 PHIDID_1202_1203 = 0x2d,
 PHIDID_1204 = 0x2e,
 PHIDID_1215__1218 = 0x2f,
 PHIDID_1219__1222 = 0x30,
 PHIDID_ADP1000 = 0x31,
 PHIDID_DAQ1000 = 0x33,
 PHIDID_DAQ1200 = 0x34,
 PHIDID_DAQ1300 = 0x35,
 PHIDID_DAQ1301 = 0x36,
 PHIDID_DAQ1400 = 0x37,
 PHIDID_DAQ1500 = 0x38,
 PHIDID_DCC1000 = 0x39,
 PHIDID_DCC1001 = 0x6e,
 PHIDID_DCC1002 = 0x75,
 PHIDID_DCC1003 = 0x78,
 PHIDID_DCC1100 = 0x6c,
 PHIDID_DST1000 = 0x3a,
 PHIDID_DST1001 = 0x79,
 PHIDID_DST1002 = 0x7e,
 PHIDID_DST1200 = 0x3b,
 PHIDID_ENC1000 = 0x3c,
 PHIDID_ENC1001 = 0x9b,
 PHIDID_FIRMWARE_UPGRADE_SPI = 0x68,
 PHIDID_FIRMWARE_UPGRADE_STM32F0 = 0x66,
 PHIDID_FIRMWARE_UPGRADE_STM32F3 = 0x91,
 PHIDID_FIRMWARE_UPGRADE_STM32G0 = 0x8f,
 PHIDID_FIRMWARE_UPGRADE_STM8S = 0x67,
 PHIDID_FIRMWARE_UPGRADE_USB = 0x65,
 PHIDID_HIN1000 = 0x3d,
 PHIDID_HIN1001 = 0x3e,
 PHIDID_HIN1100 = 0x3f,
 PHIDID_HIN1101 = 0x6d,
 PHIDID_HUB0000 = 0x40,
 PHIDID_HUB0001 = 0x8e,
 PHIDID_HUB0002 = 0x93,
 PHIDID_HUB0004 = 0x43,
 PHIDID_HUB0007 = 0x94,
 PHIDID_HUB5000 = 0x7b,
 PHIDID_HUM1000 = 0x45,
 PHIDID_HUM1001 = 0x7f,
 PHIDID_HUM1100 = 0x88,
 PHIDID_INTERFACEKIT_4_8_8 = 0x1,
 PHIDID_LCD1100 = 0x46,
 PHIDID_LED1000 = 0x47,
 PHIDID_LUX1000 = 0x48,
 PHIDID_MOT0100 = 0x92,
 PHIDID_MOT0109 = 0x8c,
 PHIDID_MOT0110 = 0x8d,
 PHIDID_MOT1100 = 0x49,
 PHIDID_MOT1101 = 0x4a,
 PHIDID_MOT1102 = 0x89,
 PHIDID_OUT1000 = 0x4b,
 PHIDID_OUT1001 = 0x4c,
 PHIDID_OUT1002 = 0x4d,
 PHIDID_OUT1100 = 0x4e,
 PHIDID_PRE1000 = 0x4f,
 PHIDID_RCC0004 = 0x7c,
 PHIDID_RCC1000 = 0x50,
 PHIDID_REL1000 = 0x51,
 PHIDID_REL1100 = 0x52,
 PHIDID_REL1101 = 0x53,
 PHIDID_SAF1000 = 0x54,
 PHIDID_SND1000 = 0x55,
 PHIDID_STC1000 = 0x56,
 PHIDID_STC1001 = 0x73,
 PHIDID_STC1002 = 0x76,
 PHIDID_STC1003 = 0x77,
 PHIDID_STC1005 = 0x95,
 PHIDID_TMP1000 = 0x57,
 PHIDID_TMP1100 = 0x58,
 PHIDID_TMP1101 = 0x59,
 PHIDID_TMP1200 = 0x5a,
 PHIDID_VCP1000 = 0x5c,
 PHIDID_VCP1001 = 0x5d,
 PHIDID_VCP1002 = 0x5e,
 PHIDID_VCP1100 = 0x69,
} Phidget_DeviceID;
typedef enum {
 PHIDGET_LOG_CRITICAL = 0x1,
 PHIDGET_LOG_ERROR = 0x2,
 PHIDGET_LOG_WARNING = 0x3,
 PHIDGET_LOG_INFO = 0x4,
 PHIDGET_LOG_DEBUG = 0x5,
 PHIDGET_LOG_VERBOSE = 0x6,
} Phidget_LogLevel;
typedef enum {
 PHIDCLASS_NOTHING = 0x0,
 PHIDCLASS_ACCELEROMETER = 0x1,
 PHIDCLASS_ADVANCEDSERVO = 0x2,
 PHIDCLASS_ANALOG = 0x3,
 PHIDCLASS_BRIDGE = 0x4,
 PHIDCLASS_DATAADAPTER = 0x19,
 PHIDCLASS_DICTIONARY = 0x18,
 PHIDCLASS_ENCODER = 0x5,
 PHIDCLASS_FIRMWAREUPGRADE = 0x17,
 PHIDCLASS_FREQUENCYCOUNTER = 0x6,
 PHIDCLASS_GENERIC = 0x16,
 PHIDCLASS_GPS = 0x7,
 PHIDCLASS_HUB = 0x8,
 PHIDCLASS_INTERFACEKIT = 0x9,
 PHIDCLASS_IR = 0xa,
 PHIDCLASS_LED = 0xb,
 PHIDCLASS_MESHDONGLE = 0xc,
 PHIDCLASS_MOTORCONTROL = 0xd,
 PHIDCLASS_PHSENSOR = 0xe,
 PHIDCLASS_RFID = 0xf,
 PHIDCLASS_SERVO = 0x10,
 PHIDCLASS_SPATIAL = 0x11,
 PHIDCLASS_STEPPER = 0x12,
 PHIDCLASS_TEMPERATURESENSOR = 0x13,
 PHIDCLASS_TEXTLCD = 0x14,
 PHIDCLASS_VINT = 0x15,
} Phidget_DeviceClass;
typedef enum {
 PHIDCHCLASS_NOTHING = 0x0,
 PHIDCHCLASS_ACCELEROMETER = 0x1,
 PHIDCHCLASS_BLDCMOTOR = 0x23,
 PHIDCHCLASS_CAPACITIVETOUCH = 0xe,
 PHIDCHCLASS_CURRENTINPUT = 0x2,
 PHIDCHCLASS_CURRENTOUTPUT = 0x26,
 PHIDCHCLASS_DATAADAPTER = 0x3,
 PHIDCHCLASS_DCMOTOR = 0x4,
 PHIDCHCLASS_DICTIONARY = 0x24,
 PHIDCHCLASS_DIGITALINPUT = 0x5,
 PHIDCHCLASS_DIGITALOUTPUT = 0x6,
 PHIDCHCLASS_DISTANCESENSOR = 0x7,
 PHIDCHCLASS_ENCODER = 0x8,
 PHIDCHCLASS_FIRMWAREUPGRADE = 0x20,
 PHIDCHCLASS_FREQUENCYCOUNTER = 0x9,
 PHIDCHCLASS_GENERIC = 0x21,
 PHIDCHCLASS_GPS = 0xa,
 PHIDCHCLASS_GYROSCOPE = 0xc,
 PHIDCHCLASS_HUB = 0xd,
 PHIDCHCLASS_HUMIDITYSENSOR = 0xf,
 PHIDCHCLASS_IR = 0x10,
 PHIDCHCLASS_LCD = 0xb,
 PHIDCHCLASS_LIGHTSENSOR = 0x11,
 PHIDCHCLASS_MAGNETOMETER = 0x12,
 PHIDCHCLASS_MESHDONGLE = 0x13,
 PHIDCHCLASS_MOTORPOSITIONCONTROLLER = 0x22,
 PHIDCHCLASS_MOTORVELOCITYCONTROLLER = 0x27,
 PHIDCHCLASS_PHSENSOR = 0x25,
 PHIDCHCLASS_POWERGUARD = 0x14,
 PHIDCHCLASS_PRESSURESENSOR = 0x15,
 PHIDCHCLASS_RCSERVO = 0x16,
 PHIDCHCLASS_RESISTANCEINPUT = 0x17,
 PHIDCHCLASS_RFID = 0x18,
 PHIDCHCLASS_SOUNDSENSOR = 0x19,
 PHIDCHCLASS_SPATIAL = 0x1a,
 PHIDCHCLASS_STEPPER = 0x1b,
 PHIDCHCLASS_TEMPERATURESENSOR = 0x1c,
 PHIDCHCLASS_VOLTAGEINPUT = 0x1d,
 PHIDCHCLASS_VOLTAGEOUTPUT = 0x1e,
 PHIDCHCLASS_VOLTAGERATIOINPUT = 0x1f,
} Phidget_ChannelClass;
typedef enum {
 PHIDCHSUBCLASS_NONE = 0x1,
 PHIDCHSUBCLASS_DIGITALOUTPUT_DUTY_CYCLE = 0x10,
 PHIDCHSUBCLASS_DIGITALOUTPUT_FREQUENCY = 0x12,
 PHIDCHSUBCLASS_DIGITALOUTPUT_LED_DRIVER = 0x11,
 PHIDCHSUBCLASS_ENCODER_MODE_SETTABLE = 0x60,
 PHIDCHSUBCLASS_LCD_GRAPHIC = 0x50,
 PHIDCHSUBCLASS_LCD_TEXT = 0x51,
 PHIDCHSUBCLASS_SPATIAL_AHRS = 0x70,
 PHIDCHSUBCLASS_TEMPERATURESENSOR_RTD = 0x20,
 PHIDCHSUBCLASS_TEMPERATURESENSOR_THERMOCOUPLE = 0x21,
 PHIDCHSUBCLASS_VOLTAGEINPUT_SENSOR_PORT = 0x30,
 PHIDCHSUBCLASS_VOLTAGERATIOINPUT_BRIDGE = 0x41,
 PHIDCHSUBCLASS_VOLTAGERATIOINPUT_SENSOR_PORT = 0x40,
} Phidget_ChannelSubclass;
typedef enum {
 MESHMODE_ROUTER = 0x1,
 MESHMODE_SLEEPYENDDEVICE = 0x2,
} Phidget_MeshMode;
typedef enum {
 POWER_SUPPLY_OFF = 0x1,
 POWER_SUPPLY_12V = 0x2,
 POWER_SUPPLY_24V = 0x3,
} Phidget_PowerSupply;
typedef enum {
 RTD_WIRE_SETUP_2WIRE = 0x1,
 RTD_WIRE_SETUP_3WIRE = 0x2,
 RTD_WIRE_SETUP_4WIRE = 0x3,
} Phidget_RTDWireSetup;
typedef enum {
 INPUT_MODE_NPN = 0x1,
 INPUT_MODE_PNP = 0x2,
} Phidget_InputMode;
typedef enum {
 FAN_MODE_OFF = 0x1,
 FAN_MODE_ON = 0x2,
 FAN_MODE_AUTO = 0x3,
} Phidget_FanMode;
typedef enum {
 DECELERATION_TYPE_COAST = 0x1,
 DECELERATION_TYPE_FORCED = 0x2,
} Phidget_DecelerationType;
typedef enum {
 POSITION_TYPE_ENCODER = 0x1,
 POSITION_TYPE_HALL_SENSOR = 0x2,
} Phidget_PositionType;
typedef enum {
 SPATIAL_PRECISION_HYBRID = 0x0,
 SPATIAL_PRECISION_HIGH = 0x1,
 SPATIAL_PRECISION_LOW = 0x2,
} Phidget_SpatialPrecision;
typedef enum {
 PHIDUNIT_NONE = 0x0,
 PHIDUNIT_BOOLEAN = 0x1,
 PHIDUNIT_PERCENT = 0x2,
 PHIDUNIT_DECIBEL = 0x3,
 PHIDUNIT_MILLIMETER = 0x4,
 PHIDUNIT_CENTIMETER = 0x5,
 PHIDUNIT_METER = 0x6,
 PHIDUNIT_GRAM = 0x7,
 PHIDUNIT_KILOGRAM = 0x8,
 PHIDUNIT_MILLIAMPERE = 0x9,
 PHIDUNIT_AMPERE = 0xa,
 PHIDUNIT_KILOPASCAL = 0xb,
 PHIDUNIT_VOLT = 0xc,
 PHIDUNIT_DEGREE_CELCIUS = 0xd,
 PHIDUNIT_LUX = 0xe,
 PHIDUNIT_GAUSS = 0xf,
 PHIDUNIT_PH = 0x10,
 PHIDUNIT_WATT = 0x11,
} Phidget_Unit;
typedef struct {
 Phidget_Unit unit;
 const char * name;
 const char * symbol;
} Phidget_UnitInfo, *Phidget_UnitInfoHandle;
typedef enum {
 PHIDGETSERVER_NONE = 0x0,
 PHIDGETSERVER_DEVICELISTENER = 0x1,
 PHIDGETSERVER_DEVICE = 0x2,
 PHIDGETSERVER_DEVICEREMOTE = 0x3,
 PHIDGETSERVER_WWWLISTENER = 0x4,
 PHIDGETSERVER_WWW = 0x5,
 PHIDGETSERVER_WWWREMOTE = 0x6,
 PHIDGETSERVER_SBC = 0x7,
} PhidgetServerType;
typedef enum {
 BRIDGE_GAIN_1 = 0x1,
 BRIDGE_GAIN_2 = 0x2,
 BRIDGE_GAIN_4 = 0x3,
 BRIDGE_GAIN_8 = 0x4,
 BRIDGE_GAIN_16 = 0x5,
 BRIDGE_GAIN_32 = 0x6,
 BRIDGE_GAIN_64 = 0x7,
 BRIDGE_GAIN_128 = 0x8,
} PhidgetVoltageRatioInput_BridgeGain;
typedef enum {
 SENSOR_TYPE_VOLTAGERATIO = 0x0,
 SENSOR_TYPE_1101_SHARP_2D120X = 0x2b03,
 SENSOR_TYPE_1101_SHARP_2Y0A21 = 0x2b04,
 SENSOR_TYPE_1101_SHARP_2Y0A02 = 0x2b05,
 SENSOR_TYPE_1102 = 0x2b0c,
 SENSOR_TYPE_1103 = 0x2b16,
 SENSOR_TYPE_1104 = 0x2b20,
 SENSOR_TYPE_1105 = 0x2b2a,
 SENSOR_TYPE_1106 = 0x2b34,
 SENSOR_TYPE_1107 = 0x2b3e,
 SENSOR_TYPE_1108 = 0x2b48,
 SENSOR_TYPE_1109 = 0x2b52,
 SENSOR_TYPE_1110 = 0x2b5c,
 SENSOR_TYPE_1111 = 0x2b66,
 SENSOR_TYPE_1112 = 0x2b70,
 SENSOR_TYPE_1113 = 0x2b7a,
 SENSOR_TYPE_1115 = 0x2b8e,
 SENSOR_TYPE_1116 = 0x2b98,
 SENSOR_TYPE_1118_AC = 0x2bad,
 SENSOR_TYPE_1118_DC = 0x2bae,
 SENSOR_TYPE_1119_AC = 0x2bb7,
 SENSOR_TYPE_1119_DC = 0x2bb8,
 SENSOR_TYPE_1120 = 0x2bc0,
 SENSOR_TYPE_1121 = 0x2bca,
 SENSOR_TYPE_1122_AC = 0x2bd5,
 SENSOR_TYPE_1122_DC = 0x2bd6,
 SENSOR_TYPE_1124 = 0x2be8,
 SENSOR_TYPE_1125_HUMIDITY = 0x2bf3,
 SENSOR_TYPE_1125_TEMPERATURE = 0x2bf4,
 SENSOR_TYPE_1126 = 0x2bfc,
 SENSOR_TYPE_1128 = 0x2c10,
 SENSOR_TYPE_1129 = 0x2c1a,
 SENSOR_TYPE_1131 = 0x2c2e,
 SENSOR_TYPE_1134 = 0x2c4c,
 SENSOR_TYPE_1136 = 0x2c60,
 SENSOR_TYPE_1137 = 0x2c6a,
 SENSOR_TYPE_1138 = 0x2c74,
 SENSOR_TYPE_1139 = 0x2c7e,
 SENSOR_TYPE_1140 = 0x2c88,
 SENSOR_TYPE_1141 = 0x2c92,
 SENSOR_TYPE_1146 = 0x2cc4,
 SENSOR_TYPE_3120 = 0x79e0,
 SENSOR_TYPE_3121 = 0x79ea,
 SENSOR_TYPE_3122 = 0x79f4,
 SENSOR_TYPE_3123 = 0x79fe,
 SENSOR_TYPE_3130 = 0x7a44,
 SENSOR_TYPE_3520 = 0x8980,
 SENSOR_TYPE_3521 = 0x898a,
 SENSOR_TYPE_3522 = 0x8994,
} PhidgetVoltageRatioInput_SensorType;
typedef enum {
 LED_FORWARD_VOLTAGE_1_7V = 0x1,
 LED_FORWARD_VOLTAGE_2_75V = 0x2,
 LED_FORWARD_VOLTAGE_3_2V = 0x3,
 LED_FORWARD_VOLTAGE_3_9V = 0x4,
 LED_FORWARD_VOLTAGE_4_0V = 0x5,
 LED_FORWARD_VOLTAGE_4_8V = 0x6,
 LED_FORWARD_VOLTAGE_5_0V = 0x7,
 LED_FORWARD_VOLTAGE_5_6V = 0x8,
} PhidgetDigitalOutput_LEDForwardVoltage;
typedef enum {
 RCSERVO_VOLTAGE_5V = 0x1,
 RCSERVO_VOLTAGE_6V = 0x2,
 RCSERVO_VOLTAGE_7_4V = 0x3,
} PhidgetRCServo_Voltage;
typedef enum {
 VOLTAGE_OUTPUT_RANGE_10V = 0x1,
 VOLTAGE_OUTPUT_RANGE_5V = 0x2,
} PhidgetVoltageOutput_VoltageOutputRange;
typedef enum {
 VOLTAGE_RANGE_10mV = 0x1,
 VOLTAGE_RANGE_40mV = 0x2,
 VOLTAGE_RANGE_200mV = 0x3,
 VOLTAGE_RANGE_312_5mV = 0x4,
 VOLTAGE_RANGE_400mV = 0x5,
 VOLTAGE_RANGE_1000mV = 0x6,
 VOLTAGE_RANGE_2V = 0x7,
 VOLTAGE_RANGE_5V = 0x8,
 VOLTAGE_RANGE_15V = 0x9,
 VOLTAGE_RANGE_40V = 0xa,
 VOLTAGE_RANGE_AUTO = 0xb,
} PhidgetVoltageInput_VoltageRange;
typedef enum {
 SENSOR_TYPE_VOLTAGE = 0x0,
 SENSOR_TYPE_1114 = 0x2b84,
 SENSOR_TYPE_1117 = 0x2ba2,
 SENSOR_TYPE_1123 = 0x2bde,
 SENSOR_TYPE_1127 = 0x2c06,
 SENSOR_TYPE_1130_PH = 0x2c25,
 SENSOR_TYPE_1130_ORP = 0x2c26,
 SENSOR_TYPE_1132 = 0x2c38,
 SENSOR_TYPE_1133 = 0x2c42,
 SENSOR_TYPE_1135 = 0x2c56,
 SENSOR_TYPE_1142 = 0x2c9c,
 SENSOR_TYPE_1143 = 0x2ca6,
 SENSOR_TYPE_3500 = 0x88b8,
 SENSOR_TYPE_3501 = 0x88c2,
 SENSOR_TYPE_3502 = 0x88cc,
 SENSOR_TYPE_3503 = 0x88d6,
 SENSOR_TYPE_3507 = 0x88fe,
 SENSOR_TYPE_3508 = 0x8908,
 SENSOR_TYPE_3509 = 0x8912,
 SENSOR_TYPE_3510 = 0x891c,
 SENSOR_TYPE_3511 = 0x8926,
 SENSOR_TYPE_3512 = 0x8930,
 SENSOR_TYPE_3513 = 0x893a,
 SENSOR_TYPE_3514 = 0x8944,
 SENSOR_TYPE_3515 = 0x894e,
 SENSOR_TYPE_3516 = 0x8958,
 SENSOR_TYPE_3517 = 0x8962,
 SENSOR_TYPE_3518 = 0x896c,
 SENSOR_TYPE_3519 = 0x8976,
 SENSOR_TYPE_3584 = 0x8c00,
 SENSOR_TYPE_3585 = 0x8c0a,
 SENSOR_TYPE_3586 = 0x8c14,
 SENSOR_TYPE_3587 = 0x8c1e,
 SENSOR_TYPE_3588 = 0x8c28,
 SENSOR_TYPE_3589 = 0x8c32,
 SENSOR_TYPE_MOT2002_LOW = 0x4e34,
 SENSOR_TYPE_MOT2002_MED = 0x4e35,
 SENSOR_TYPE_MOT2002_HIGH = 0x4e36,
 SENSOR_TYPE_VCP4114 = 0xa0b4,
} PhidgetVoltageInput_SensorType;
typedef enum {
 PROTOCOL_EM4100 = 0x1,
 PROTOCOL_ISO11785_FDX_B = 0x2,
 PROTOCOL_PHIDGETS = 0x3,
} PhidgetRFID_Protocol;
typedef struct {
 int16_t tm_ms;
 int16_t tm_sec;
 int16_t tm_min;
 int16_t tm_hour;
} PhidgetGPS_Time, *PhidgetGPS_TimeHandle;
typedef struct {
 int16_t tm_mday;
 int16_t tm_mon;
 int16_t tm_year;
} PhidgetGPS_Date, *PhidgetGPS_DateHandle;
typedef struct {
 double latitude;
 double longitude;
 int16_t fixQuality;
 int16_t numSatellites;
 double horizontalDilution;
 double altitude;
 double heightOfGeoid;
} PhidgetGPS_GPGGA, *PhidgetGPS_GPGGAHandle;
typedef struct {
 char mode;
 int16_t fixType;
 int16_t satUsed[12];
 double posnDilution;
 double horizDilution;
 double vertDilution;
} PhidgetGPS_GPGSA, *PhidgetGPS_GPGSAHandle;
typedef struct {
 char status;
 double latitude;
 double longitude;
 double speedKnots;
 double heading;
 double magneticVariation;
 char mode;
} PhidgetGPS_GPRMC, *PhidgetGPS_GPRMCHandle;
typedef struct {
 double trueHeading;
 double magneticHeading;
 double speedKnots;
 double speed;
 char mode;
} PhidgetGPS_GPVTG, *PhidgetGPS_GPVTGHandle;
typedef struct {
 PhidgetGPS_GPGGA GGA;
 PhidgetGPS_GPGSA GSA;
 PhidgetGPS_GPRMC RMC;
 PhidgetGPS_GPVTG VTG;
} PhidgetGPS_NMEAData, *PhidgetGPS_NMEADataHandle;
typedef enum {
 SPATIAL_ALGORITHM_NONE = 0x0,
 SPATIAL_ALGORITHM_AHRS = 0x1,
 SPATIAL_ALGORITHM_IMU = 0x2,
} Phidget_SpatialAlgorithm;
typedef struct {
 double x;
 double y;
 double z;
 double w;
} PhidgetSpatial_SpatialQuaternion, *PhidgetSpatial_SpatialQuaternionHandle;
typedef struct {
 double pitch;
 double roll;
 double heading;
} PhidgetSpatial_SpatialEulerAngles, *PhidgetSpatial_SpatialEulerAnglesHandle;
typedef enum {
 RTD_TYPE_PT100_3850 = 0x1,
 RTD_TYPE_PT1000_3850 = 0x2,
 RTD_TYPE_PT100_3920 = 0x3,
 RTD_TYPE_PT1000_3920 = 0x4,
} PhidgetTemperatureSensor_RTDType;
typedef enum {
 THERMOCOUPLE_TYPE_J = 0x1,
 THERMOCOUPLE_TYPE_K = 0x2,
 THERMOCOUPLE_TYPE_E = 0x3,
 THERMOCOUPLE_TYPE_T = 0x4,
} PhidgetTemperatureSensor_ThermocoupleType;
typedef enum {
 FILTER_TYPE_ZERO_CROSSING = 0x1,
 FILTER_TYPE_LOGIC_LEVEL = 0x2,
} PhidgetFrequencyCounter_FilterType;
typedef enum {
 IR_ENCODING_UNKNOWN = 0x1,
 IR_ENCODING_SPACE = 0x2,
 IR_ENCODING_PULSE = 0x3,
 IR_ENCODING_BIPHASE = 0x4,
 IR_ENCODING_RC5 = 0x5,
 IR_ENCODING_RC6 = 0x6,
} PhidgetIR_Encoding;
typedef enum {
 IR_LENGTH_UNKNOWN = 0x1,
 IR_LENGTH_CONSTANT = 0x2,
 IR_LENGTH_VARIABLE = 0x3,
} PhidgetIR_Length;
typedef struct {
 uint32_t bitCount;
 PhidgetIR_Encoding encoding;
 PhidgetIR_Length length;
 uint32_t gap;
 uint32_t trail;
 uint32_t header[2];
 uint32_t one[2];
 uint32_t zero[2];
 uint32_t repeat[26];
 uint32_t minRepeat;
 double dutyCycle;
 uint32_t carrierFrequency;
 char toggleMask[33];
} PhidgetIR_CodeInfo, *PhidgetIR_CodeInfoHandle;
typedef enum {
 CONTROL_MODE_STEP = 0x0,
 CONTROL_MODE_RUN = 0x1,
} PhidgetStepper_ControlMode;
typedef enum {
 FONT_User1 = 0x1,
 FONT_User2 = 0x2,
 FONT_6x10 = 0x3,
 FONT_5x8 = 0x4,
 FONT_6x12 = 0x5,
} PhidgetLCD_Font;
typedef enum {
 SCREEN_SIZE_NONE = 0x1,
 SCREEN_SIZE_1x8 = 0x2,
 SCREEN_SIZE_2x8 = 0x3,
 SCREEN_SIZE_1x16 = 0x4,
 SCREEN_SIZE_2x16 = 0x5,
 SCREEN_SIZE_4x16 = 0x6,
 SCREEN_SIZE_2x20 = 0x7,
 SCREEN_SIZE_4x20 = 0x8,
 SCREEN_SIZE_2x24 = 0x9,
 SCREEN_SIZE_1x40 = 0xa,
 SCREEN_SIZE_2x40 = 0xb,
 SCREEN_SIZE_4x40 = 0xc,
 SCREEN_SIZE_64x128 = 0xd,
} PhidgetLCD_ScreenSize;
typedef enum {
 PIXEL_STATE_OFF = 0x0,
 PIXEL_STATE_ON = 0x1,
 PIXEL_STATE_INVERT = 0x2,
} PhidgetLCD_PixelState;
typedef enum {
 PARITY_MODE_NONE = 0x1,
 PARITY_MODE_EVEN = 0x2,
 PARITY_MODE_ODD = 0x3,
} PhidgetDataAdapter_Parity;
typedef enum {
 STOP_BITS_ONE = 0x1,
 STOP_BITS_TWO = 0x2,
} PhidgetDataAdapter_StopBits;
typedef enum {
 HANDSHAKE_MODE_NONE = 0x1,
 HANDSHAKE_MODE_REQUEST_TO_SEND = 0x2,
 HANDSHAKE_MODE_READY_TO_RECEIVE = 0x3,
} PhidgetDataAdapter_HandshakeMode;
typedef enum {
 PROTOCOL_RS485 = 0x1,
 PROTOCOL_RS422 = 0x2,
 PROTOCOL_DMX512 = 0x3,
 PROTOCOL_MODBUS_RTU = 0x4,
 PROTOCOL_SPI = 0x5,
 PROTOCOL_I2C = 0x6,
 PROTOCOL_UART = 0x7,
 PROTOCOL_RS232 = 0x8,
} PhidgetDataAdapter_Protocol;
typedef enum {
 SPI_MODE_0 = 0x1,
 SPI_MODE_1 = 0x2,
 SPI_MODE_2 = 0x3,
 SPI_MODE_3 = 0x4,
} PhidgetDataAdapter_SPIMode;
typedef enum {
 ENDIANNESS_MSB_FIRST = 0x1,
 ENDIANNESS_LSB_FIRST = 0x2,
} PhidgetDataAdapter_Endianness;
typedef enum {
 IO_VOLTAGE_EXTERN = 0x1,
 IO_VOLTAGE_1_8V = 0x2,
 IO_VOLTAGE_2_5V = 0x3,
 IO_VOLTAGE_3_3V = 0x4,
 IO_VOLTAGE_5_0V = 0x5,
} PhidgetDataAdapter_IOVoltage;
typedef enum {
 PACKET_ERROR_OK = 0x0,
 PACKET_ERROR_UNKNOWN = 0x1,
 PACKET_ERROR_TIMEOUT = 0x2,
 PACKET_ERROR_FORMAT = 0x3,
 PACKET_ERROR_INVALID = 0x4,
 PACKET_ERROR_OVERRUN = 0x5,
 PACKET_ERROR_CORRUPT = 0x6,
} PhidgetDataAdapter_PacketErrorCode;
typedef enum {
 SPL_RANGE_102dB = 0x1,
 SPL_RANGE_82dB = 0x2,
} PhidgetSoundSensor_SPLRange;
typedef enum {
 PORT_MODE_VINT_PORT = 0x0,
 PORT_MODE_DIGITAL_INPUT = 0x1,
 PORT_MODE_DIGITAL_OUTPUT = 0x2,
 PORT_MODE_VOLTAGE_INPUT = 0x3,
 PORT_MODE_VOLTAGE_RATIO_INPUT = 0x4,
} PhidgetHub_PortMode;
typedef struct _Phidget Phidget;
typedef struct _Phidget *PhidgetHandle;
typedef void( *Phidget_AsyncCallback)(PhidgetHandle phid, void *ctx, PhidgetReturnCode returnCode);
 PhidgetReturnCode Phidget_getLibraryVersion(const char **libraryVersion);
 PhidgetReturnCode Phidget_getLibraryVersionNumber(const char **libraryVersion);
 PhidgetReturnCode Phidget_getErrorDescription(PhidgetReturnCode errorCode, const char **errorString);
 PhidgetReturnCode Phidget_getLastError(PhidgetReturnCode *errorCode, const char **errorString, char *errorDetail, size_t *errorDetailLen);
 PhidgetReturnCode Phidget_finalize(int flags);
 PhidgetReturnCode Phidget_resetLibrary(void);
 PhidgetReturnCode Phidget_open(PhidgetHandle phid);
 PhidgetReturnCode Phidget_openWaitForAttachment(PhidgetHandle phid, uint32_t timeoutMs);
 PhidgetReturnCode Phidget_close(PhidgetHandle phid);
 PhidgetReturnCode Phidget_delete(PhidgetHandle *phid);
 PhidgetReturnCode Phidget_writeDeviceLabel(PhidgetHandle phid, const char *deviceLabel);
 PhidgetReturnCode Phidget_retain(PhidgetHandle phid);
 PhidgetReturnCode Phidget_release(PhidgetHandle *phid);
 PhidgetReturnCode Phidget_getChildDevices(PhidgetHandle phid, PhidgetHandle *arr, size_t *arrCnt);
 PhidgetReturnCode Phidget_releaseDevices(PhidgetHandle *arr, size_t arrCnt);
 PhidgetReturnCode Phidget_getDataInterval(PhidgetHandle phid, uint32_t *di);
 PhidgetReturnCode Phidget_getMinDataInterval(PhidgetHandle phid, uint32_t *min);
 PhidgetReturnCode Phidget_getMaxDataInterval(PhidgetHandle phid, uint32_t *max);
 PhidgetReturnCode Phidget_setDataInterval(PhidgetHandle phid, uint32_t di);
 PhidgetReturnCode Phidget_getDataRate(PhidgetHandle phid, double *dr);
 PhidgetReturnCode Phidget_getMinDataRate(PhidgetHandle phid, double *min);
 PhidgetReturnCode Phidget_getMaxDataRate(PhidgetHandle phid, double *max);
 PhidgetReturnCode Phidget_setDataRate(PhidgetHandle phid, double dr);
 PhidgetReturnCode Phidget_getAttached(PhidgetHandle phid, int *attached);
 PhidgetReturnCode Phidget_getIsChannel(PhidgetHandle phid, int *isChannel);
 PhidgetReturnCode Phidget_getIsLocal(PhidgetHandle phid, int *isLocal);
 PhidgetReturnCode Phidget_setIsLocal(PhidgetHandle phid, int isLocal);
 PhidgetReturnCode Phidget_getIsRemote(PhidgetHandle phid, int *isRemote);
 PhidgetReturnCode Phidget_setIsRemote(PhidgetHandle phid, int isRemote);
 PhidgetReturnCode Phidget_getParent(PhidgetHandle phid, PhidgetHandle *parent);
 PhidgetReturnCode Phidget_getServerName(PhidgetHandle phid, const char **serverName);
 PhidgetReturnCode Phidget_getServerUniqueName(PhidgetHandle phid, const char **serverUniqueName);
 PhidgetReturnCode Phidget_setServerName(PhidgetHandle phid, const char *serverName);
 PhidgetReturnCode Phidget_getServerPeerName(PhidgetHandle phid, const char **serverPeerName);
 PhidgetReturnCode Phidget_getServerHostname(PhidgetHandle phid, const char **serverHostname);
 PhidgetReturnCode Phidget_getServerVersion(PhidgetHandle phid, int *major, int *minor);
 PhidgetReturnCode Phidget_getClientVersion(PhidgetHandle phid, int *major, int *minor);
 PhidgetReturnCode Phidget_getIsOpen(PhidgetHandle phid, int *status);
 PhidgetReturnCode Phidget_getChannel(PhidgetHandle phid, int *channel);
 PhidgetReturnCode Phidget_setChannel(PhidgetHandle phid, int channel);
 PhidgetReturnCode Phidget_getChannelClass(PhidgetHandle phid, Phidget_ChannelClass *channelClass);
 PhidgetReturnCode Phidget_getChannelClassName(PhidgetHandle phid, const char **channelClassName);
 PhidgetReturnCode Phidget_getChannelName(PhidgetHandle phid, const char **channelName);
 PhidgetReturnCode Phidget_getChannelSubclass(PhidgetHandle phid, Phidget_ChannelSubclass *channelSubclass);
 PhidgetReturnCode Phidget_getDeviceClass(PhidgetHandle phid, Phidget_DeviceClass *deviceClass);
 PhidgetReturnCode Phidget_getDeviceClassName(PhidgetHandle phid, const char **deviceClassName);
 PhidgetReturnCode Phidget_getDeviceID(PhidgetHandle phid, Phidget_DeviceID *deviceID);
 PhidgetReturnCode Phidget_getDeviceLabel(PhidgetHandle phid, const char **deviceLabel);
 PhidgetReturnCode Phidget_setDeviceLabel(PhidgetHandle phid, const char *deviceLabel);
 PhidgetReturnCode Phidget_getDeviceName(PhidgetHandle phid, const char **deviceName);
 PhidgetReturnCode Phidget_getDeviceSerialNumber(PhidgetHandle phid, int32_t *deviceSerialNumber);
 PhidgetReturnCode Phidget_setDeviceSerialNumber(PhidgetHandle phid, int32_t deviceSerialNumber);
 PhidgetReturnCode Phidget_getDeviceSKU(PhidgetHandle phid, const char **deviceSKU);
 PhidgetReturnCode Phidget_getDeviceVersion(PhidgetHandle phid, int *deviceVersion);
 PhidgetReturnCode Phidget_getDeviceChannelCount(PhidgetHandle phid, Phidget_ChannelClass cls, uint32_t *count);
 PhidgetReturnCode Phidget_getIsHubPortDevice(PhidgetHandle phid, int *isHubPortDevice);
 PhidgetReturnCode Phidget_setIsHubPortDevice(PhidgetHandle phid, int isHubPortDevice);
 PhidgetReturnCode Phidget_getHub(PhidgetHandle phid, PhidgetHandle *hub);
 PhidgetReturnCode Phidget_getHubPort(PhidgetHandle phid, int *hubPort);
 PhidgetReturnCode Phidget_setHubPort(PhidgetHandle phid, int hubPort);
 PhidgetReturnCode Phidget_getHubPortCount(PhidgetHandle phid, int *hubPortCount);
 PhidgetReturnCode Phidget_getHubPortSpeed(PhidgetHandle phid, uint32_t *speed);
 PhidgetReturnCode Phidget_setHubPortSpeed(PhidgetHandle phid, uint32_t speed);
 PhidgetReturnCode Phidget_getHubPortSupportsSetSpeed(PhidgetHandle phid, int *supportsSetSpeed);
 PhidgetReturnCode Phidget_getHubPortSupportsAutoSetSpeed(PhidgetHandle phid, int *supportsAutoSetSpeed);
 PhidgetReturnCode Phidget_getMaxHubPortSpeed(PhidgetHandle phid, uint32_t *maxSpeed);
 PhidgetReturnCode Phidget_getVINTDeviceSupportsSetSpeed(PhidgetHandle phid, int *supportsSetSpeed);
 PhidgetReturnCode Phidget_getVINTDeviceSupportsAutoSetSpeed(PhidgetHandle phid, int *supportsAutoSetSpeed);
 PhidgetReturnCode Phidget_getMaxVINTDeviceSpeed(PhidgetHandle phid, uint32_t *maxSpeed);
 PhidgetReturnCode Phidget_setMeshMode(PhidgetHandle phid, Phidget_MeshMode mode);
 PhidgetReturnCode Phidget_getMeshMode(PhidgetHandle phid, Phidget_MeshMode *mode);
typedef void( *Phidget_OnAttachCallback)(PhidgetHandle phid, void *ctx);
typedef void( *Phidget_OnDetachCallback)(PhidgetHandle phid, void *ctx);
typedef void( *Phidget_OnErrorCallback)(PhidgetHandle phid, void *ctx, Phidget_ErrorEventCode errorCode, const char *errorString);
typedef void( *Phidget_OnPropertyChangeCallback)(PhidgetHandle phid, void *ctx, const char *property);
 PhidgetReturnCode Phidget_setOnDetachHandler(PhidgetHandle phid, Phidget_OnDetachCallback fptr, void *ctx);
 PhidgetReturnCode Phidget_setOnAttachHandler(PhidgetHandle phid, Phidget_OnAttachCallback fptr, void *ctx);
 PhidgetReturnCode Phidget_setOnErrorHandler(PhidgetHandle phid, Phidget_OnErrorCallback fptr, void *ctx);
 PhidgetReturnCode Phidget_setOnPropertyChangeHandler(PhidgetHandle phid, Phidget_OnPropertyChangeCallback fptr, void *ctx);
 int Phidget_validDictionaryKey(const char *);
typedef void( *PhidgetDictionary_OnChangeCallback)(int, const char *, void *, int, const char *, const char *);
 PhidgetReturnCode PhidgetDictionary_setOnChangeCallbackHandler(PhidgetDictionary_OnChangeCallback, void *);
typedef struct _PhidgetManager *PhidgetManagerHandle;
 PhidgetReturnCode PhidgetManager_create(PhidgetManagerHandle *phidm);
 PhidgetReturnCode PhidgetManager_delete(PhidgetManagerHandle *phidm);
 PhidgetReturnCode PhidgetManager_open(PhidgetManagerHandle phidm);
 PhidgetReturnCode PhidgetManager_close(PhidgetManagerHandle phidm);
typedef void( *PhidgetManager_OnAttachCallback)(PhidgetManagerHandle phidm, void *ctx, PhidgetHandle phid);
typedef void( *PhidgetManager_OnDetachCallback)(PhidgetManagerHandle phidm, void *ctx, PhidgetHandle phid);
typedef void( *PhidgetManager_OnErrorCallback)(PhidgetManagerHandle phidm, void *ctx, Phidget_ErrorEventCode errorCode, const char *errorString);
 PhidgetReturnCode PhidgetManager_setOnAttachHandler(PhidgetManagerHandle phidm, PhidgetManager_OnAttachCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetManager_setOnDetachHandler(PhidgetManagerHandle phidm, PhidgetManager_OnDetachCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetManager_setOnErrorHandler(PhidgetManagerHandle phidm, PhidgetManager_OnErrorCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLog_enable(Phidget_LogLevel level, const char *destination);
 PhidgetReturnCode PhidgetLog_disable(void);
 PhidgetReturnCode PhidgetLog_enableNetwork(const char *address, int port);
 PhidgetReturnCode PhidgetLog_disableNetwork(void);
 PhidgetReturnCode PhidgetLog_log(Phidget_LogLevel level, const char *message, ...) ;
 PhidgetReturnCode PhidgetLog_loge(const char *file, int line, const char *func,
        const char *src, Phidget_LogLevel level, const char *message, ...) ;
 PhidgetReturnCode PhidgetLog_logs(Phidget_LogLevel level, const char *message);
 PhidgetReturnCode PhidgetLog_loges(Phidget_LogLevel level, const char *source, const char *message);
 PhidgetReturnCode PhidgetLog_rotate(void);
 PhidgetReturnCode PhidgetLog_enableRotating(void);
 PhidgetReturnCode PhidgetLog_disableRotating(void);
 PhidgetReturnCode PhidgetLog_isRotating(int *isrotating);
 PhidgetReturnCode PhidgetLog_getRotating(uint64_t *size, int *keepCount);
 PhidgetReturnCode PhidgetLog_setRotating(uint64_t size, int keepCount);
 PhidgetReturnCode PhidgetLog_getLevel(Phidget_LogLevel *level);
 PhidgetReturnCode PhidgetLog_setLevel(Phidget_LogLevel level);
 PhidgetReturnCode PhidgetLog_addSource(const char *, Phidget_LogLevel level);
 PhidgetReturnCode PhidgetLog_getSourceLevel(const char *source, Phidget_LogLevel *level);
 PhidgetReturnCode PhidgetLog_setSourceLevel(const char *source, Phidget_LogLevel level);
 PhidgetReturnCode PhidgetLog_getSources(const char *sources[], uint32_t *count);
typedef struct {
 const char *name;
 const char *stype;
 PhidgetServerType type;
 int flags;
 const char *addr;
 const char *host;
 int port;
 const void *handle;
} PhidgetServer, *PhidgetServerHandle;
 PhidgetReturnCode PhidgetNet_addServer(const char *serverName, const char *address, int port, const char *password, int flags);
 PhidgetReturnCode PhidgetNet_removeServer(const char *serverName);
 PhidgetReturnCode PhidgetNet_removeAllServers(void);
 PhidgetReturnCode PhidgetNet_enableServer(const char *serverName);
 PhidgetReturnCode PhidgetNet_disableServer(const char *serverName, int flags);
 PhidgetReturnCode PhidgetNet_setServerPassword(const char *serverName, const char *password);
 PhidgetReturnCode PhidgetNet_enableServerDiscovery(PhidgetServerType serverType);
 PhidgetReturnCode PhidgetNet_disableServerDiscovery(PhidgetServerType serverType);
typedef void( *PhidgetNet_OnServerAddedCallback)(void *ctx, PhidgetServerHandle server, void *kv);
typedef void( *PhidgetNet_OnServerRemovedCallback)(void *ctx, PhidgetServerHandle server);
 PhidgetReturnCode PhidgetNet_setOnServerAddedHandler(PhidgetNet_OnServerAddedCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetNet_setOnServerRemovedHandler(PhidgetNet_OnServerRemovedCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetNet_getServerAddressList(const char *hostname, int addressFamily, char *addressList[], uint32_t *count);
 PhidgetReturnCode PhidgetNet_freeServerAddressList(char *addressList[], uint32_t count);
 PhidgetReturnCode PhidgetNet_startServer(int flags, int addressFamily, const char *serverName, const char *address, int port,
            const char *password, PhidgetServerHandle *server);
 PhidgetReturnCode PhidgetNet_stopServer(PhidgetServerHandle *server);
 const char * Phidget_enumString(const char *, int);
 int Phidget_enumFromString(const char *);
typedef struct _PhidgetVoltageRatioInput *PhidgetVoltageRatioInputHandle;
 PhidgetReturnCode PhidgetVoltageRatioInput_create(PhidgetVoltageRatioInputHandle *ch);
 PhidgetReturnCode PhidgetVoltageRatioInput_delete(PhidgetVoltageRatioInputHandle *ch);
 PhidgetReturnCode PhidgetVoltageRatioInput_setBridgeEnabled(PhidgetVoltageRatioInputHandle ch,
  int bridgeEnabled);
 PhidgetReturnCode PhidgetVoltageRatioInput_getBridgeEnabled(PhidgetVoltageRatioInputHandle ch,
  int *bridgeEnabled);
 PhidgetReturnCode PhidgetVoltageRatioInput_setBridgeGain(PhidgetVoltageRatioInputHandle ch,
  PhidgetVoltageRatioInput_BridgeGain bridgeGain);
 PhidgetReturnCode PhidgetVoltageRatioInput_getBridgeGain(PhidgetVoltageRatioInputHandle ch,
  PhidgetVoltageRatioInput_BridgeGain *bridgeGain);
 PhidgetReturnCode PhidgetVoltageRatioInput_setDataInterval(PhidgetVoltageRatioInputHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetVoltageRatioInput_getDataInterval(PhidgetVoltageRatioInputHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetVoltageRatioInput_getMinDataInterval(PhidgetVoltageRatioInputHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetVoltageRatioInput_getMaxDataInterval(PhidgetVoltageRatioInputHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetVoltageRatioInput_setDataRate(PhidgetVoltageRatioInputHandle ch,
  double dataRate);
 PhidgetReturnCode PhidgetVoltageRatioInput_getDataRate(PhidgetVoltageRatioInputHandle ch,
  double *dataRate);
 PhidgetReturnCode PhidgetVoltageRatioInput_getMinDataRate(PhidgetVoltageRatioInputHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetVoltageRatioInput_getMaxDataRate(PhidgetVoltageRatioInputHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetVoltageRatioInput_setSensorType(PhidgetVoltageRatioInputHandle ch,
  PhidgetVoltageRatioInput_SensorType sensorType);
 PhidgetReturnCode PhidgetVoltageRatioInput_getSensorType(PhidgetVoltageRatioInputHandle ch,
  PhidgetVoltageRatioInput_SensorType *sensorType);
 PhidgetReturnCode PhidgetVoltageRatioInput_getSensorUnit(PhidgetVoltageRatioInputHandle ch,
  Phidget_UnitInfo *sensorUnit);
 PhidgetReturnCode PhidgetVoltageRatioInput_getSensorValue(PhidgetVoltageRatioInputHandle ch,
  double *sensorValue);
 PhidgetReturnCode PhidgetVoltageRatioInput_setSensorValueChangeTrigger(PhidgetVoltageRatioInputHandle ch,
  double sensorValueChangeTrigger);
 PhidgetReturnCode PhidgetVoltageRatioInput_getSensorValueChangeTrigger(PhidgetVoltageRatioInputHandle ch,
  double *sensorValueChangeTrigger);
 PhidgetReturnCode PhidgetVoltageRatioInput_getVoltageRatio(PhidgetVoltageRatioInputHandle ch,
  double *voltageRatio);
 PhidgetReturnCode PhidgetVoltageRatioInput_getMinVoltageRatio(PhidgetVoltageRatioInputHandle ch,
  double *minVoltageRatio);
 PhidgetReturnCode PhidgetVoltageRatioInput_getMaxVoltageRatio(PhidgetVoltageRatioInputHandle ch,
  double *maxVoltageRatio);
 PhidgetReturnCode PhidgetVoltageRatioInput_setVoltageRatioChangeTrigger(PhidgetVoltageRatioInputHandle ch,
  double voltageRatioChangeTrigger);
 PhidgetReturnCode PhidgetVoltageRatioInput_getVoltageRatioChangeTrigger(PhidgetVoltageRatioInputHandle ch,
  double *voltageRatioChangeTrigger);
 PhidgetReturnCode PhidgetVoltageRatioInput_getMinVoltageRatioChangeTrigger(PhidgetVoltageRatioInputHandle ch, double *minVoltageRatioChangeTrigger);
 PhidgetReturnCode PhidgetVoltageRatioInput_getMaxVoltageRatioChangeTrigger(PhidgetVoltageRatioInputHandle ch, double *maxVoltageRatioChangeTrigger);
typedef void ( *PhidgetVoltageRatioInput_OnSensorChangeCallback)(PhidgetVoltageRatioInputHandle ch,
  void *ctx, double sensorValue, Phidget_UnitInfo *sensorUnit);
 PhidgetReturnCode PhidgetVoltageRatioInput_setOnSensorChangeHandler(PhidgetVoltageRatioInputHandle ch,
  PhidgetVoltageRatioInput_OnSensorChangeCallback fptr, void *ctx);
typedef void ( *PhidgetVoltageRatioInput_OnVoltageRatioChangeCallback)(PhidgetVoltageRatioInputHandle ch, void *ctx, double voltageRatio);
 PhidgetReturnCode PhidgetVoltageRatioInput_setOnVoltageRatioChangeHandler(PhidgetVoltageRatioInputHandle ch,
  PhidgetVoltageRatioInput_OnVoltageRatioChangeCallback fptr, void *ctx);
typedef struct _PhidgetDigitalInput *PhidgetDigitalInputHandle;
 PhidgetReturnCode PhidgetDigitalInput_create(PhidgetDigitalInputHandle *ch);
 PhidgetReturnCode PhidgetDigitalInput_delete(PhidgetDigitalInputHandle *ch);
 PhidgetReturnCode PhidgetDigitalInput_setInputMode(PhidgetDigitalInputHandle ch,
  Phidget_InputMode inputMode);
 PhidgetReturnCode PhidgetDigitalInput_getInputMode(PhidgetDigitalInputHandle ch,
  Phidget_InputMode *inputMode);
 PhidgetReturnCode PhidgetDigitalInput_setPowerSupply(PhidgetDigitalInputHandle ch,
  Phidget_PowerSupply powerSupply);
 PhidgetReturnCode PhidgetDigitalInput_getPowerSupply(PhidgetDigitalInputHandle ch,
  Phidget_PowerSupply *powerSupply);
 PhidgetReturnCode PhidgetDigitalInput_getState(PhidgetDigitalInputHandle ch, int *state);
typedef void ( *PhidgetDigitalInput_OnStateChangeCallback)(PhidgetDigitalInputHandle ch, void *ctx,
  int state);
 PhidgetReturnCode PhidgetDigitalInput_setOnStateChangeHandler(PhidgetDigitalInputHandle ch,
  PhidgetDigitalInput_OnStateChangeCallback fptr, void *ctx);
typedef struct _PhidgetDigitalOutput *PhidgetDigitalOutputHandle;
 PhidgetReturnCode PhidgetDigitalOutput_create(PhidgetDigitalOutputHandle *ch);
 PhidgetReturnCode PhidgetDigitalOutput_delete(PhidgetDigitalOutputHandle *ch);
 PhidgetReturnCode PhidgetDigitalOutput_enableFailsafe(PhidgetDigitalOutputHandle ch,
  uint32_t failsafeTime);
 PhidgetReturnCode PhidgetDigitalOutput_resetFailsafe(PhidgetDigitalOutputHandle ch);
 PhidgetReturnCode PhidgetDigitalOutput_setDutyCycle(PhidgetDigitalOutputHandle ch, double dutyCycle);
 void PhidgetDigitalOutput_setDutyCycle_async(PhidgetDigitalOutputHandle ch, double dutyCycle,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetDigitalOutput_getDutyCycle(PhidgetDigitalOutputHandle ch, double *dutyCycle);
 PhidgetReturnCode PhidgetDigitalOutput_getMinDutyCycle(PhidgetDigitalOutputHandle ch,
  double *minDutyCycle);
 PhidgetReturnCode PhidgetDigitalOutput_getMaxDutyCycle(PhidgetDigitalOutputHandle ch,
  double *maxDutyCycle);
 PhidgetReturnCode PhidgetDigitalOutput_getMinFailsafeTime(PhidgetDigitalOutputHandle ch,
  uint32_t *minFailsafeTime);
 PhidgetReturnCode PhidgetDigitalOutput_getMaxFailsafeTime(PhidgetDigitalOutputHandle ch,
  uint32_t *maxFailsafeTime);
 PhidgetReturnCode PhidgetDigitalOutput_setFrequency(PhidgetDigitalOutputHandle ch, double frequency);
 PhidgetReturnCode PhidgetDigitalOutput_getFrequency(PhidgetDigitalOutputHandle ch, double *frequency);
 PhidgetReturnCode PhidgetDigitalOutput_getMinFrequency(PhidgetDigitalOutputHandle ch,
  double *minFrequency);
 PhidgetReturnCode PhidgetDigitalOutput_getMaxFrequency(PhidgetDigitalOutputHandle ch,
  double *maxFrequency);
 PhidgetReturnCode PhidgetDigitalOutput_setLEDCurrentLimit(PhidgetDigitalOutputHandle ch,
  double LEDCurrentLimit);
 void PhidgetDigitalOutput_setLEDCurrentLimit_async(PhidgetDigitalOutputHandle ch,
  double LEDCurrentLimit, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetDigitalOutput_getLEDCurrentLimit(PhidgetDigitalOutputHandle ch,
  double *LEDCurrentLimit);
 PhidgetReturnCode PhidgetDigitalOutput_getMinLEDCurrentLimit(PhidgetDigitalOutputHandle ch,
  double *minLEDCurrentLimit);
 PhidgetReturnCode PhidgetDigitalOutput_getMaxLEDCurrentLimit(PhidgetDigitalOutputHandle ch,
  double *maxLEDCurrentLimit);
 PhidgetReturnCode PhidgetDigitalOutput_setLEDForwardVoltage(PhidgetDigitalOutputHandle ch,
  PhidgetDigitalOutput_LEDForwardVoltage LEDForwardVoltage);
 PhidgetReturnCode PhidgetDigitalOutput_getLEDForwardVoltage(PhidgetDigitalOutputHandle ch,
  PhidgetDigitalOutput_LEDForwardVoltage *LEDForwardVoltage);
 PhidgetReturnCode PhidgetDigitalOutput_setState(PhidgetDigitalOutputHandle ch, int state);
 void PhidgetDigitalOutput_setState_async(PhidgetDigitalOutputHandle ch, int state,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetDigitalOutput_getState(PhidgetDigitalOutputHandle ch, int *state);
typedef struct _PhidgetRCServo *PhidgetRCServoHandle;
 PhidgetReturnCode PhidgetRCServo_create(PhidgetRCServoHandle *ch);
 PhidgetReturnCode PhidgetRCServo_delete(PhidgetRCServoHandle *ch);
 PhidgetReturnCode PhidgetRCServo_enableFailsafe(PhidgetRCServoHandle ch, uint32_t failsafeTime);
 PhidgetReturnCode PhidgetRCServo_resetFailsafe(PhidgetRCServoHandle ch);
 PhidgetReturnCode PhidgetRCServo_setAcceleration(PhidgetRCServoHandle ch, double acceleration);
 PhidgetReturnCode PhidgetRCServo_getAcceleration(PhidgetRCServoHandle ch, double *acceleration);
 PhidgetReturnCode PhidgetRCServo_getMinAcceleration(PhidgetRCServoHandle ch, double *minAcceleration);
 PhidgetReturnCode PhidgetRCServo_getMaxAcceleration(PhidgetRCServoHandle ch, double *maxAcceleration);
 PhidgetReturnCode PhidgetRCServo_setDataInterval(PhidgetRCServoHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetRCServo_getDataInterval(PhidgetRCServoHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetRCServo_getMinDataInterval(PhidgetRCServoHandle ch, uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetRCServo_getMaxDataInterval(PhidgetRCServoHandle ch, uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetRCServo_setDataRate(PhidgetRCServoHandle ch, double dataRate);
 PhidgetReturnCode PhidgetRCServo_getDataRate(PhidgetRCServoHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetRCServo_getMinDataRate(PhidgetRCServoHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetRCServo_getMaxDataRate(PhidgetRCServoHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetRCServo_setEngaged(PhidgetRCServoHandle ch, int engaged);
 PhidgetReturnCode PhidgetRCServo_getEngaged(PhidgetRCServoHandle ch, int *engaged);
 PhidgetReturnCode PhidgetRCServo_getMinFailsafeTime(PhidgetRCServoHandle ch, uint32_t *minFailsafeTime);
 PhidgetReturnCode PhidgetRCServo_getMaxFailsafeTime(PhidgetRCServoHandle ch, uint32_t *maxFailsafeTime);
 PhidgetReturnCode PhidgetRCServo_getIsMoving(PhidgetRCServoHandle ch, int *isMoving);
 PhidgetReturnCode PhidgetRCServo_getPosition(PhidgetRCServoHandle ch, double *position);
 PhidgetReturnCode PhidgetRCServo_setMinPosition(PhidgetRCServoHandle ch, double minPosition);
 PhidgetReturnCode PhidgetRCServo_getMinPosition(PhidgetRCServoHandle ch, double *minPosition);
 PhidgetReturnCode PhidgetRCServo_setMaxPosition(PhidgetRCServoHandle ch, double maxPosition);
 PhidgetReturnCode PhidgetRCServo_getMaxPosition(PhidgetRCServoHandle ch, double *maxPosition);
 PhidgetReturnCode PhidgetRCServo_setMinPulseWidth(PhidgetRCServoHandle ch, double minPulseWidth);
 PhidgetReturnCode PhidgetRCServo_getMinPulseWidth(PhidgetRCServoHandle ch, double *minPulseWidth);
 PhidgetReturnCode PhidgetRCServo_setMaxPulseWidth(PhidgetRCServoHandle ch, double maxPulseWidth);
 PhidgetReturnCode PhidgetRCServo_getMaxPulseWidth(PhidgetRCServoHandle ch, double *maxPulseWidth);
 PhidgetReturnCode PhidgetRCServo_getMinPulseWidthLimit(PhidgetRCServoHandle ch,
  double *minPulseWidthLimit);
 PhidgetReturnCode PhidgetRCServo_getMaxPulseWidthLimit(PhidgetRCServoHandle ch,
  double *maxPulseWidthLimit);
 PhidgetReturnCode PhidgetRCServo_setSpeedRampingState(PhidgetRCServoHandle ch, int speedRampingState);
 PhidgetReturnCode PhidgetRCServo_getSpeedRampingState(PhidgetRCServoHandle ch, int *speedRampingState);
 PhidgetReturnCode PhidgetRCServo_setTargetPosition(PhidgetRCServoHandle ch, double targetPosition);
 void PhidgetRCServo_setTargetPosition_async(PhidgetRCServoHandle ch, double targetPosition,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetRCServo_getTargetPosition(PhidgetRCServoHandle ch, double *targetPosition);
 PhidgetReturnCode PhidgetRCServo_setTorque(PhidgetRCServoHandle ch, double torque);
 PhidgetReturnCode PhidgetRCServo_getTorque(PhidgetRCServoHandle ch, double *torque);
 PhidgetReturnCode PhidgetRCServo_getMinTorque(PhidgetRCServoHandle ch, double *minTorque);
 PhidgetReturnCode PhidgetRCServo_getMaxTorque(PhidgetRCServoHandle ch, double *maxTorque);
 PhidgetReturnCode PhidgetRCServo_getVelocity(PhidgetRCServoHandle ch, double *velocity);
 PhidgetReturnCode PhidgetRCServo_setVelocityLimit(PhidgetRCServoHandle ch, double velocityLimit);
 PhidgetReturnCode PhidgetRCServo_getVelocityLimit(PhidgetRCServoHandle ch, double *velocityLimit);
 PhidgetReturnCode PhidgetRCServo_getMinVelocityLimit(PhidgetRCServoHandle ch, double *minVelocityLimit);
 PhidgetReturnCode PhidgetRCServo_getMaxVelocityLimit(PhidgetRCServoHandle ch, double *maxVelocityLimit);
 PhidgetReturnCode PhidgetRCServo_setVoltage(PhidgetRCServoHandle ch, PhidgetRCServo_Voltage voltage);
 PhidgetReturnCode PhidgetRCServo_getVoltage(PhidgetRCServoHandle ch, PhidgetRCServo_Voltage *voltage);
typedef void ( *PhidgetRCServo_OnPositionChangeCallback)(PhidgetRCServoHandle ch, void *ctx,
  double position);
 PhidgetReturnCode PhidgetRCServo_setOnPositionChangeHandler(PhidgetRCServoHandle ch,
  PhidgetRCServo_OnPositionChangeCallback fptr, void *ctx);
typedef void ( *PhidgetRCServo_OnTargetPositionReachedCallback)(PhidgetRCServoHandle ch, void *ctx,
  double position);
 PhidgetReturnCode PhidgetRCServo_setOnTargetPositionReachedHandler(PhidgetRCServoHandle ch,
  PhidgetRCServo_OnTargetPositionReachedCallback fptr, void *ctx);
typedef void ( *PhidgetRCServo_OnVelocityChangeCallback)(PhidgetRCServoHandle ch, void *ctx,
  double velocity);
 PhidgetReturnCode PhidgetRCServo_setOnVelocityChangeHandler(PhidgetRCServoHandle ch,
  PhidgetRCServo_OnVelocityChangeCallback fptr, void *ctx);
typedef struct _PhidgetVoltageOutput *PhidgetVoltageOutputHandle;
 PhidgetReturnCode PhidgetVoltageOutput_create(PhidgetVoltageOutputHandle *ch);
 PhidgetReturnCode PhidgetVoltageOutput_delete(PhidgetVoltageOutputHandle *ch);
 PhidgetReturnCode PhidgetVoltageOutput_enableFailsafe(PhidgetVoltageOutputHandle ch,
  uint32_t failsafeTime);
 PhidgetReturnCode PhidgetVoltageOutput_resetFailsafe(PhidgetVoltageOutputHandle ch);
 PhidgetReturnCode PhidgetVoltageOutput_setEnabled(PhidgetVoltageOutputHandle ch, int enabled);
 PhidgetReturnCode PhidgetVoltageOutput_getEnabled(PhidgetVoltageOutputHandle ch, int *enabled);
 PhidgetReturnCode PhidgetVoltageOutput_getMinFailsafeTime(PhidgetVoltageOutputHandle ch,
  uint32_t *minFailsafeTime);
 PhidgetReturnCode PhidgetVoltageOutput_getMaxFailsafeTime(PhidgetVoltageOutputHandle ch,
  uint32_t *maxFailsafeTime);
 PhidgetReturnCode PhidgetVoltageOutput_setVoltage(PhidgetVoltageOutputHandle ch, double voltage);
 void PhidgetVoltageOutput_setVoltage_async(PhidgetVoltageOutputHandle ch, double voltage,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetVoltageOutput_getVoltage(PhidgetVoltageOutputHandle ch, double *voltage);
 PhidgetReturnCode PhidgetVoltageOutput_getMinVoltage(PhidgetVoltageOutputHandle ch, double *minVoltage);
 PhidgetReturnCode PhidgetVoltageOutput_getMaxVoltage(PhidgetVoltageOutputHandle ch, double *maxVoltage);
 PhidgetReturnCode PhidgetVoltageOutput_setVoltageOutputRange(PhidgetVoltageOutputHandle ch,
  PhidgetVoltageOutput_VoltageOutputRange voltageOutputRange);
 PhidgetReturnCode PhidgetVoltageOutput_getVoltageOutputRange(PhidgetVoltageOutputHandle ch,
  PhidgetVoltageOutput_VoltageOutputRange *voltageOutputRange);
typedef struct _PhidgetAccelerometer *PhidgetAccelerometerHandle;
 PhidgetReturnCode PhidgetAccelerometer_create(PhidgetAccelerometerHandle *ch);
 PhidgetReturnCode PhidgetAccelerometer_delete(PhidgetAccelerometerHandle *ch);
 PhidgetReturnCode PhidgetAccelerometer_getAcceleration(PhidgetAccelerometerHandle ch,
  double (*acceleration)[3]);
 PhidgetReturnCode PhidgetAccelerometer_getMinAcceleration(PhidgetAccelerometerHandle ch,
  double (*minAcceleration)[3]);
 PhidgetReturnCode PhidgetAccelerometer_getMaxAcceleration(PhidgetAccelerometerHandle ch,
  double (*maxAcceleration)[3]);
 PhidgetReturnCode PhidgetAccelerometer_setAccelerationChangeTrigger(PhidgetAccelerometerHandle ch,
  double accelerationChangeTrigger);
 PhidgetReturnCode PhidgetAccelerometer_getAccelerationChangeTrigger(PhidgetAccelerometerHandle ch,
  double *accelerationChangeTrigger);
 PhidgetReturnCode PhidgetAccelerometer_getMinAccelerationChangeTrigger(PhidgetAccelerometerHandle ch,
  double *minAccelerationChangeTrigger);
 PhidgetReturnCode PhidgetAccelerometer_getMaxAccelerationChangeTrigger(PhidgetAccelerometerHandle ch,
  double *maxAccelerationChangeTrigger);
 PhidgetReturnCode PhidgetAccelerometer_getAxisCount(PhidgetAccelerometerHandle ch, int *axisCount);
 PhidgetReturnCode PhidgetAccelerometer_setDataInterval(PhidgetAccelerometerHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetAccelerometer_getDataInterval(PhidgetAccelerometerHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetAccelerometer_getMinDataInterval(PhidgetAccelerometerHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetAccelerometer_getMaxDataInterval(PhidgetAccelerometerHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetAccelerometer_setDataRate(PhidgetAccelerometerHandle ch, double dataRate);
 PhidgetReturnCode PhidgetAccelerometer_getDataRate(PhidgetAccelerometerHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetAccelerometer_getMinDataRate(PhidgetAccelerometerHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetAccelerometer_getMaxDataRate(PhidgetAccelerometerHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetAccelerometer_setHeatingEnabled(PhidgetAccelerometerHandle ch,
  int heatingEnabled);
 PhidgetReturnCode PhidgetAccelerometer_getHeatingEnabled(PhidgetAccelerometerHandle ch,
  int *heatingEnabled);
 PhidgetReturnCode PhidgetAccelerometer_getTimestamp(PhidgetAccelerometerHandle ch, double *timestamp);
typedef void ( *PhidgetAccelerometer_OnAccelerationChangeCallback)(PhidgetAccelerometerHandle ch,
  void *ctx, const double acceleration[3], double timestamp);
 PhidgetReturnCode PhidgetAccelerometer_setOnAccelerationChangeHandler(PhidgetAccelerometerHandle ch,
  PhidgetAccelerometer_OnAccelerationChangeCallback fptr, void *ctx);
typedef struct _PhidgetVoltageInput *PhidgetVoltageInputHandle;
 PhidgetReturnCode PhidgetVoltageInput_create(PhidgetVoltageInputHandle *ch);
 PhidgetReturnCode PhidgetVoltageInput_delete(PhidgetVoltageInputHandle *ch);
 PhidgetReturnCode PhidgetVoltageInput_setDataInterval(PhidgetVoltageInputHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetVoltageInput_getDataInterval(PhidgetVoltageInputHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetVoltageInput_getMinDataInterval(PhidgetVoltageInputHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetVoltageInput_getMaxDataInterval(PhidgetVoltageInputHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetVoltageInput_setDataRate(PhidgetVoltageInputHandle ch, double dataRate);
 PhidgetReturnCode PhidgetVoltageInput_getDataRate(PhidgetVoltageInputHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetVoltageInput_getMinDataRate(PhidgetVoltageInputHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetVoltageInput_getMaxDataRate(PhidgetVoltageInputHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetVoltageInput_setPowerSupply(PhidgetVoltageInputHandle ch,
  Phidget_PowerSupply powerSupply);
 PhidgetReturnCode PhidgetVoltageInput_getPowerSupply(PhidgetVoltageInputHandle ch,
  Phidget_PowerSupply *powerSupply);
 PhidgetReturnCode PhidgetVoltageInput_setSensorType(PhidgetVoltageInputHandle ch,
  PhidgetVoltageInput_SensorType sensorType);
 PhidgetReturnCode PhidgetVoltageInput_getSensorType(PhidgetVoltageInputHandle ch,
  PhidgetVoltageInput_SensorType *sensorType);
 PhidgetReturnCode PhidgetVoltageInput_getSensorUnit(PhidgetVoltageInputHandle ch,
  Phidget_UnitInfo *sensorUnit);
 PhidgetReturnCode PhidgetVoltageInput_getSensorValue(PhidgetVoltageInputHandle ch, double *sensorValue);
 PhidgetReturnCode PhidgetVoltageInput_setSensorValueChangeTrigger(PhidgetVoltageInputHandle ch,
  double sensorValueChangeTrigger);
 PhidgetReturnCode PhidgetVoltageInput_getSensorValueChangeTrigger(PhidgetVoltageInputHandle ch,
  double *sensorValueChangeTrigger);
 PhidgetReturnCode PhidgetVoltageInput_getVoltage(PhidgetVoltageInputHandle ch, double *voltage);
 PhidgetReturnCode PhidgetVoltageInput_getMinVoltage(PhidgetVoltageInputHandle ch, double *minVoltage);
 PhidgetReturnCode PhidgetVoltageInput_getMaxVoltage(PhidgetVoltageInputHandle ch, double *maxVoltage);
 PhidgetReturnCode PhidgetVoltageInput_setVoltageChangeTrigger(PhidgetVoltageInputHandle ch,
  double voltageChangeTrigger);
 PhidgetReturnCode PhidgetVoltageInput_getVoltageChangeTrigger(PhidgetVoltageInputHandle ch,
  double *voltageChangeTrigger);
 PhidgetReturnCode PhidgetVoltageInput_getMinVoltageChangeTrigger(PhidgetVoltageInputHandle ch,
  double *minVoltageChangeTrigger);
 PhidgetReturnCode PhidgetVoltageInput_getMaxVoltageChangeTrigger(PhidgetVoltageInputHandle ch,
  double *maxVoltageChangeTrigger);
 PhidgetReturnCode PhidgetVoltageInput_setVoltageRange(PhidgetVoltageInputHandle ch,
  PhidgetVoltageInput_VoltageRange voltageRange);
 PhidgetReturnCode PhidgetVoltageInput_getVoltageRange(PhidgetVoltageInputHandle ch,
  PhidgetVoltageInput_VoltageRange *voltageRange);
typedef void ( *PhidgetVoltageInput_OnSensorChangeCallback)(PhidgetVoltageInputHandle ch, void *ctx,
  double sensorValue, Phidget_UnitInfo *sensorUnit);
 PhidgetReturnCode PhidgetVoltageInput_setOnSensorChangeHandler(PhidgetVoltageInputHandle ch,
  PhidgetVoltageInput_OnSensorChangeCallback fptr, void *ctx);
typedef void ( *PhidgetVoltageInput_OnVoltageChangeCallback)(PhidgetVoltageInputHandle ch, void *ctx,
  double voltage);
 PhidgetReturnCode PhidgetVoltageInput_setOnVoltageChangeHandler(PhidgetVoltageInputHandle ch,
  PhidgetVoltageInput_OnVoltageChangeCallback fptr, void *ctx);
typedef struct _PhidgetCapacitiveTouch *PhidgetCapacitiveTouchHandle;
 PhidgetReturnCode PhidgetCapacitiveTouch_create(PhidgetCapacitiveTouchHandle *ch);
 PhidgetReturnCode PhidgetCapacitiveTouch_delete(PhidgetCapacitiveTouchHandle *ch);
 PhidgetReturnCode PhidgetCapacitiveTouch_setDataInterval(PhidgetCapacitiveTouchHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetCapacitiveTouch_getDataInterval(PhidgetCapacitiveTouchHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMinDataInterval(PhidgetCapacitiveTouchHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMaxDataInterval(PhidgetCapacitiveTouchHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetCapacitiveTouch_setDataRate(PhidgetCapacitiveTouchHandle ch, double dataRate);
 PhidgetReturnCode PhidgetCapacitiveTouch_getDataRate(PhidgetCapacitiveTouchHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMinDataRate(PhidgetCapacitiveTouchHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMaxDataRate(PhidgetCapacitiveTouchHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetCapacitiveTouch_setSensitivity(PhidgetCapacitiveTouchHandle ch,
  double sensitivity);
 PhidgetReturnCode PhidgetCapacitiveTouch_getSensitivity(PhidgetCapacitiveTouchHandle ch,
  double *sensitivity);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMinSensitivity(PhidgetCapacitiveTouchHandle ch,
  double *minSensitivity);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMaxSensitivity(PhidgetCapacitiveTouchHandle ch,
  double *maxSensitivity);
 PhidgetReturnCode PhidgetCapacitiveTouch_getIsTouched(PhidgetCapacitiveTouchHandle ch, int *isTouched);
 PhidgetReturnCode PhidgetCapacitiveTouch_getTouchValue(PhidgetCapacitiveTouchHandle ch,
  double *touchValue);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMinTouchValue(PhidgetCapacitiveTouchHandle ch,
  double *minTouchValue);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMaxTouchValue(PhidgetCapacitiveTouchHandle ch,
  double *maxTouchValue);
 PhidgetReturnCode PhidgetCapacitiveTouch_setTouchValueChangeTrigger(PhidgetCapacitiveTouchHandle ch,
  double touchValueChangeTrigger);
 PhidgetReturnCode PhidgetCapacitiveTouch_getTouchValueChangeTrigger(PhidgetCapacitiveTouchHandle ch,
  double *touchValueChangeTrigger);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMinTouchValueChangeTrigger(PhidgetCapacitiveTouchHandle ch,
  double *minTouchValueChangeTrigger);
 PhidgetReturnCode PhidgetCapacitiveTouch_getMaxTouchValueChangeTrigger(PhidgetCapacitiveTouchHandle ch,
  double *maxTouchValueChangeTrigger);
typedef void ( *PhidgetCapacitiveTouch_OnTouchCallback)(PhidgetCapacitiveTouchHandle ch, void *ctx,
  double touchValue);
 PhidgetReturnCode PhidgetCapacitiveTouch_setOnTouchHandler(PhidgetCapacitiveTouchHandle ch,
  PhidgetCapacitiveTouch_OnTouchCallback fptr, void *ctx);
typedef void ( *PhidgetCapacitiveTouch_OnTouchEndCallback)(PhidgetCapacitiveTouchHandle ch,
  void *ctx);
 PhidgetReturnCode PhidgetCapacitiveTouch_setOnTouchEndHandler(PhidgetCapacitiveTouchHandle ch,
  PhidgetCapacitiveTouch_OnTouchEndCallback fptr, void *ctx);
typedef struct _PhidgetRFID *PhidgetRFIDHandle;
 PhidgetReturnCode PhidgetRFID_create(PhidgetRFIDHandle *ch);
 PhidgetReturnCode PhidgetRFID_delete(PhidgetRFIDHandle *ch);
 PhidgetReturnCode PhidgetRFID_getLastTag(PhidgetRFIDHandle ch, char *tagString, size_t tagStringLen,
  PhidgetRFID_Protocol *protocol);
 PhidgetReturnCode PhidgetRFID_write(PhidgetRFIDHandle ch, const char *tagString,
  PhidgetRFID_Protocol protocol, int lockTag);
 PhidgetReturnCode PhidgetRFID_setAntennaEnabled(PhidgetRFIDHandle ch, int antennaEnabled);
 PhidgetReturnCode PhidgetRFID_getAntennaEnabled(PhidgetRFIDHandle ch, int *antennaEnabled);
 PhidgetReturnCode PhidgetRFID_getTagPresent(PhidgetRFIDHandle ch, int *tagPresent);
typedef void ( *PhidgetRFID_OnTagCallback)(PhidgetRFIDHandle ch, void *ctx, const char *tag,
  PhidgetRFID_Protocol protocol);
 PhidgetReturnCode PhidgetRFID_setOnTagHandler(PhidgetRFIDHandle ch, PhidgetRFID_OnTagCallback fptr,
  void *ctx);
typedef void ( *PhidgetRFID_OnTagLostCallback)(PhidgetRFIDHandle ch, void *ctx, const char *tag,
  PhidgetRFID_Protocol protocol);
 PhidgetReturnCode PhidgetRFID_setOnTagLostHandler(PhidgetRFIDHandle ch, PhidgetRFID_OnTagLostCallback fptr,
  void *ctx);
typedef struct _PhidgetGPS *PhidgetGPSHandle;
 PhidgetReturnCode PhidgetGPS_create(PhidgetGPSHandle *ch);
 PhidgetReturnCode PhidgetGPS_delete(PhidgetGPSHandle *ch);
 PhidgetReturnCode PhidgetGPS_getAltitude(PhidgetGPSHandle ch, double *altitude);
 PhidgetReturnCode PhidgetGPS_getDate(PhidgetGPSHandle ch, PhidgetGPS_Date *date);
 PhidgetReturnCode PhidgetGPS_getHeading(PhidgetGPSHandle ch, double *heading);
 PhidgetReturnCode PhidgetGPS_getLatitude(PhidgetGPSHandle ch, double *latitude);
 PhidgetReturnCode PhidgetGPS_getLongitude(PhidgetGPSHandle ch, double *longitude);
 PhidgetReturnCode PhidgetGPS_getNMEAData(PhidgetGPSHandle ch, PhidgetGPS_NMEAData *NMEAData);
 PhidgetReturnCode PhidgetGPS_getPositionFixState(PhidgetGPSHandle ch, int *positionFixState);
 PhidgetReturnCode PhidgetGPS_getTime(PhidgetGPSHandle ch, PhidgetGPS_Time *time);
 PhidgetReturnCode PhidgetGPS_getVelocity(PhidgetGPSHandle ch, double *velocity);
typedef void ( *PhidgetGPS_OnHeadingChangeCallback)(PhidgetGPSHandle ch, void *ctx, double heading,
  double velocity);
 PhidgetReturnCode PhidgetGPS_setOnHeadingChangeHandler(PhidgetGPSHandle ch,
  PhidgetGPS_OnHeadingChangeCallback fptr, void *ctx);
typedef void ( *PhidgetGPS_OnPositionChangeCallback)(PhidgetGPSHandle ch, void *ctx, double latitude,
  double longitude, double altitude);
 PhidgetReturnCode PhidgetGPS_setOnPositionChangeHandler(PhidgetGPSHandle ch,
  PhidgetGPS_OnPositionChangeCallback fptr, void *ctx);
typedef void ( *PhidgetGPS_OnPositionFixStateChangeCallback)(PhidgetGPSHandle ch, void *ctx,
  int positionFixState);
 PhidgetReturnCode PhidgetGPS_setOnPositionFixStateChangeHandler(PhidgetGPSHandle ch,
  PhidgetGPS_OnPositionFixStateChangeCallback fptr, void *ctx);
typedef struct _PhidgetGyroscope *PhidgetGyroscopeHandle;
 PhidgetReturnCode PhidgetGyroscope_create(PhidgetGyroscopeHandle *ch);
 PhidgetReturnCode PhidgetGyroscope_delete(PhidgetGyroscopeHandle *ch);
 PhidgetReturnCode PhidgetGyroscope_zero(PhidgetGyroscopeHandle ch);
 PhidgetReturnCode PhidgetGyroscope_getAngularRate(PhidgetGyroscopeHandle ch, double (*angularRate)[3]);
 PhidgetReturnCode PhidgetGyroscope_getMinAngularRate(PhidgetGyroscopeHandle ch,
  double (*minAngularRate)[3]);
 PhidgetReturnCode PhidgetGyroscope_getMaxAngularRate(PhidgetGyroscopeHandle ch,
  double (*maxAngularRate)[3]);
 PhidgetReturnCode PhidgetGyroscope_getAxisCount(PhidgetGyroscopeHandle ch, int *axisCount);
 PhidgetReturnCode PhidgetGyroscope_setDataInterval(PhidgetGyroscopeHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetGyroscope_getDataInterval(PhidgetGyroscopeHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetGyroscope_getMinDataInterval(PhidgetGyroscopeHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetGyroscope_getMaxDataInterval(PhidgetGyroscopeHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetGyroscope_setDataRate(PhidgetGyroscopeHandle ch, double dataRate);
 PhidgetReturnCode PhidgetGyroscope_getDataRate(PhidgetGyroscopeHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetGyroscope_getMinDataRate(PhidgetGyroscopeHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetGyroscope_getMaxDataRate(PhidgetGyroscopeHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetGyroscope_setHeatingEnabled(PhidgetGyroscopeHandle ch, int heatingEnabled);
 PhidgetReturnCode PhidgetGyroscope_getHeatingEnabled(PhidgetGyroscopeHandle ch, int *heatingEnabled);
 PhidgetReturnCode PhidgetGyroscope_getTimestamp(PhidgetGyroscopeHandle ch, double *timestamp);
typedef void ( *PhidgetGyroscope_OnAngularRateUpdateCallback)(PhidgetGyroscopeHandle ch, void *ctx,
  const double angularRate[3], double timestamp);
 PhidgetReturnCode PhidgetGyroscope_setOnAngularRateUpdateHandler(PhidgetGyroscopeHandle ch,
  PhidgetGyroscope_OnAngularRateUpdateCallback fptr, void *ctx);
typedef struct _PhidgetMagnetometer *PhidgetMagnetometerHandle;
 PhidgetReturnCode PhidgetMagnetometer_create(PhidgetMagnetometerHandle *ch);
 PhidgetReturnCode PhidgetMagnetometer_delete(PhidgetMagnetometerHandle *ch);
 PhidgetReturnCode PhidgetMagnetometer_setCorrectionParameters(PhidgetMagnetometerHandle ch,
  double magneticField, double offset0, double offset1, double offset2, double gain0, double gain1, double gain2, double T0, double T1, double T2, double T3, double T4, double T5);
 PhidgetReturnCode PhidgetMagnetometer_resetCorrectionParameters(PhidgetMagnetometerHandle ch);
 PhidgetReturnCode PhidgetMagnetometer_saveCorrectionParameters(PhidgetMagnetometerHandle ch);
 PhidgetReturnCode PhidgetMagnetometer_getAxisCount(PhidgetMagnetometerHandle ch, int *axisCount);
 PhidgetReturnCode PhidgetMagnetometer_setDataInterval(PhidgetMagnetometerHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetMagnetometer_getDataInterval(PhidgetMagnetometerHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetMagnetometer_getMinDataInterval(PhidgetMagnetometerHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetMagnetometer_getMaxDataInterval(PhidgetMagnetometerHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetMagnetometer_setDataRate(PhidgetMagnetometerHandle ch, double dataRate);
 PhidgetReturnCode PhidgetMagnetometer_getDataRate(PhidgetMagnetometerHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetMagnetometer_getMinDataRate(PhidgetMagnetometerHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetMagnetometer_getMaxDataRate(PhidgetMagnetometerHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetMagnetometer_setHeatingEnabled(PhidgetMagnetometerHandle ch, int heatingEnabled);
 PhidgetReturnCode PhidgetMagnetometer_getHeatingEnabled(PhidgetMagnetometerHandle ch,
  int *heatingEnabled);
 PhidgetReturnCode PhidgetMagnetometer_getMagneticField(PhidgetMagnetometerHandle ch,
  double (*magneticField)[3]);
 PhidgetReturnCode PhidgetMagnetometer_getMinMagneticField(PhidgetMagnetometerHandle ch,
  double (*minMagneticField)[3]);
 PhidgetReturnCode PhidgetMagnetometer_getMaxMagneticField(PhidgetMagnetometerHandle ch,
  double (*maxMagneticField)[3]);
 PhidgetReturnCode PhidgetMagnetometer_setMagneticFieldChangeTrigger(PhidgetMagnetometerHandle ch,
  double magneticFieldChangeTrigger);
 PhidgetReturnCode PhidgetMagnetometer_getMagneticFieldChangeTrigger(PhidgetMagnetometerHandle ch,
  double *magneticFieldChangeTrigger);
 PhidgetReturnCode PhidgetMagnetometer_getMinMagneticFieldChangeTrigger(PhidgetMagnetometerHandle ch,
  double *minMagneticFieldChangeTrigger);
 PhidgetReturnCode PhidgetMagnetometer_getMaxMagneticFieldChangeTrigger(PhidgetMagnetometerHandle ch,
  double *maxMagneticFieldChangeTrigger);
 PhidgetReturnCode PhidgetMagnetometer_getTimestamp(PhidgetMagnetometerHandle ch, double *timestamp);
typedef void ( *PhidgetMagnetometer_OnMagneticFieldChangeCallback)(PhidgetMagnetometerHandle ch,
  void *ctx, const double magneticField[3], double timestamp);
 PhidgetReturnCode PhidgetMagnetometer_setOnMagneticFieldChangeHandler(PhidgetMagnetometerHandle ch,
  PhidgetMagnetometer_OnMagneticFieldChangeCallback fptr, void *ctx);
typedef struct _PhidgetSpatial *PhidgetSpatialHandle;
 PhidgetReturnCode PhidgetSpatial_create(PhidgetSpatialHandle *ch);
 PhidgetReturnCode PhidgetSpatial_delete(PhidgetSpatialHandle *ch);
 PhidgetReturnCode PhidgetSpatial_setAHRSParameters(PhidgetSpatialHandle ch, double angularVelocityThreshold,
  double angularVelocityDeltaThreshold, double accelerationThreshold, double magTime, double accelTime, double biasTime);
 PhidgetReturnCode PhidgetSpatial_setMagnetometerCorrectionParameters(PhidgetSpatialHandle ch,
  double magneticField, double offset0, double offset1, double offset2, double gain0, double gain1, double gain2, double T0, double T1, double T2, double T3, double T4, double T5);
 PhidgetReturnCode PhidgetSpatial_resetMagnetometerCorrectionParameters(PhidgetSpatialHandle ch);
 PhidgetReturnCode PhidgetSpatial_saveMagnetometerCorrectionParameters(PhidgetSpatialHandle ch);
 PhidgetReturnCode PhidgetSpatial_zeroAlgorithm(PhidgetSpatialHandle ch);
 PhidgetReturnCode PhidgetSpatial_zeroGyro(PhidgetSpatialHandle ch);
 PhidgetReturnCode PhidgetSpatial_getMinAcceleration(PhidgetSpatialHandle ch,
  double (*minAcceleration)[3]);
 PhidgetReturnCode PhidgetSpatial_getMaxAcceleration(PhidgetSpatialHandle ch,
  double (*maxAcceleration)[3]);
 PhidgetReturnCode PhidgetSpatial_setAlgorithm(PhidgetSpatialHandle ch,
  Phidget_SpatialAlgorithm algorithm);
 PhidgetReturnCode PhidgetSpatial_getAlgorithm(PhidgetSpatialHandle ch,
  Phidget_SpatialAlgorithm *algorithm);
 PhidgetReturnCode PhidgetSpatial_setAlgorithmMagnetometerGain(PhidgetSpatialHandle ch,
  double algorithmMagnetometerGain);
 PhidgetReturnCode PhidgetSpatial_getAlgorithmMagnetometerGain(PhidgetSpatialHandle ch,
  double *algorithmMagnetometerGain);
 PhidgetReturnCode PhidgetSpatial_getMinAngularRate(PhidgetSpatialHandle ch, double (*minAngularRate)[3]);
 PhidgetReturnCode PhidgetSpatial_getMaxAngularRate(PhidgetSpatialHandle ch, double (*maxAngularRate)[3]);
 PhidgetReturnCode PhidgetSpatial_setDataInterval(PhidgetSpatialHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetSpatial_getDataInterval(PhidgetSpatialHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetSpatial_getMinDataInterval(PhidgetSpatialHandle ch, uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetSpatial_getMaxDataInterval(PhidgetSpatialHandle ch, uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetSpatial_setDataRate(PhidgetSpatialHandle ch, double dataRate);
 PhidgetReturnCode PhidgetSpatial_getDataRate(PhidgetSpatialHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetSpatial_getMinDataRate(PhidgetSpatialHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetSpatial_getMaxDataRate(PhidgetSpatialHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetSpatial_getEulerAngles(PhidgetSpatialHandle ch,
  PhidgetSpatial_SpatialEulerAngles *eulerAngles);
 PhidgetReturnCode PhidgetSpatial_setHeatingEnabled(PhidgetSpatialHandle ch, int heatingEnabled);
 PhidgetReturnCode PhidgetSpatial_getHeatingEnabled(PhidgetSpatialHandle ch, int *heatingEnabled);
 PhidgetReturnCode PhidgetSpatial_getMinMagneticField(PhidgetSpatialHandle ch,
  double (*minMagneticField)[3]);
 PhidgetReturnCode PhidgetSpatial_getMaxMagneticField(PhidgetSpatialHandle ch,
  double (*maxMagneticField)[3]);
 PhidgetReturnCode PhidgetSpatial_getQuaternion(PhidgetSpatialHandle ch,
  PhidgetSpatial_SpatialQuaternion *quaternion);
typedef void ( *PhidgetSpatial_OnAlgorithmDataCallback)(PhidgetSpatialHandle ch, void *ctx,
  const double quaternion[4], double timestamp);
 PhidgetReturnCode PhidgetSpatial_setOnAlgorithmDataHandler(PhidgetSpatialHandle ch,
  PhidgetSpatial_OnAlgorithmDataCallback fptr, void *ctx);
typedef void ( *PhidgetSpatial_OnSpatialDataCallback)(PhidgetSpatialHandle ch, void *ctx,
  const double acceleration[3], const double angularRate[3], const double magneticField[3], double timestamp);
 PhidgetReturnCode PhidgetSpatial_setOnSpatialDataHandler(PhidgetSpatialHandle ch,
  PhidgetSpatial_OnSpatialDataCallback fptr, void *ctx);
typedef struct _PhidgetTemperatureSensor *PhidgetTemperatureSensorHandle;
 PhidgetReturnCode PhidgetTemperatureSensor_create(PhidgetTemperatureSensorHandle *ch);
 PhidgetReturnCode PhidgetTemperatureSensor_delete(PhidgetTemperatureSensorHandle *ch);
 PhidgetReturnCode PhidgetTemperatureSensor_setDataInterval(PhidgetTemperatureSensorHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetTemperatureSensor_getDataInterval(PhidgetTemperatureSensorHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetTemperatureSensor_getMinDataInterval(PhidgetTemperatureSensorHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetTemperatureSensor_getMaxDataInterval(PhidgetTemperatureSensorHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetTemperatureSensor_setDataRate(PhidgetTemperatureSensorHandle ch,
  double dataRate);
 PhidgetReturnCode PhidgetTemperatureSensor_getDataRate(PhidgetTemperatureSensorHandle ch,
  double *dataRate);
 PhidgetReturnCode PhidgetTemperatureSensor_getMinDataRate(PhidgetTemperatureSensorHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetTemperatureSensor_getMaxDataRate(PhidgetTemperatureSensorHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetTemperatureSensor_setRTDType(PhidgetTemperatureSensorHandle ch,
  PhidgetTemperatureSensor_RTDType RTDType);
 PhidgetReturnCode PhidgetTemperatureSensor_getRTDType(PhidgetTemperatureSensorHandle ch,
  PhidgetTemperatureSensor_RTDType *RTDType);
 PhidgetReturnCode PhidgetTemperatureSensor_setRTDWireSetup(PhidgetTemperatureSensorHandle ch,
  Phidget_RTDWireSetup RTDWireSetup);
 PhidgetReturnCode PhidgetTemperatureSensor_getRTDWireSetup(PhidgetTemperatureSensorHandle ch,
  Phidget_RTDWireSetup *RTDWireSetup);
 PhidgetReturnCode PhidgetTemperatureSensor_getTemperature(PhidgetTemperatureSensorHandle ch,
  double *temperature);
 PhidgetReturnCode PhidgetTemperatureSensor_getMinTemperature(PhidgetTemperatureSensorHandle ch,
  double *minTemperature);
 PhidgetReturnCode PhidgetTemperatureSensor_getMaxTemperature(PhidgetTemperatureSensorHandle ch,
  double *maxTemperature);
 PhidgetReturnCode PhidgetTemperatureSensor_setTemperatureChangeTrigger(PhidgetTemperatureSensorHandle ch,
  double temperatureChangeTrigger);
 PhidgetReturnCode PhidgetTemperatureSensor_getTemperatureChangeTrigger(PhidgetTemperatureSensorHandle ch,
  double *temperatureChangeTrigger);
 PhidgetReturnCode PhidgetTemperatureSensor_getMinTemperatureChangeTrigger(PhidgetTemperatureSensorHandle ch,
  double *minTemperatureChangeTrigger);
 PhidgetReturnCode PhidgetTemperatureSensor_getMaxTemperatureChangeTrigger(PhidgetTemperatureSensorHandle ch,
  double *maxTemperatureChangeTrigger);
 PhidgetReturnCode PhidgetTemperatureSensor_setThermocoupleType(PhidgetTemperatureSensorHandle ch,
  PhidgetTemperatureSensor_ThermocoupleType thermocoupleType);
 PhidgetReturnCode PhidgetTemperatureSensor_getThermocoupleType(PhidgetTemperatureSensorHandle ch,
  PhidgetTemperatureSensor_ThermocoupleType *thermocoupleType);
typedef void ( *PhidgetTemperatureSensor_OnTemperatureChangeCallback)(PhidgetTemperatureSensorHandle ch, void *ctx, double temperature);
 PhidgetReturnCode PhidgetTemperatureSensor_setOnTemperatureChangeHandler(PhidgetTemperatureSensorHandle ch,
  PhidgetTemperatureSensor_OnTemperatureChangeCallback fptr, void *ctx);
typedef struct _PhidgetEncoder *PhidgetEncoderHandle;
 PhidgetReturnCode PhidgetEncoder_create(PhidgetEncoderHandle *ch);
 PhidgetReturnCode PhidgetEncoder_delete(PhidgetEncoderHandle *ch);
 PhidgetReturnCode PhidgetEncoder_setEnabled(PhidgetEncoderHandle ch, int enabled);
 PhidgetReturnCode PhidgetEncoder_getEnabled(PhidgetEncoderHandle ch, int *enabled);
 PhidgetReturnCode PhidgetEncoder_setDataInterval(PhidgetEncoderHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetEncoder_getDataInterval(PhidgetEncoderHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetEncoder_getMinDataInterval(PhidgetEncoderHandle ch, uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetEncoder_getMaxDataInterval(PhidgetEncoderHandle ch, uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetEncoder_setDataRate(PhidgetEncoderHandle ch, double dataRate);
 PhidgetReturnCode PhidgetEncoder_getDataRate(PhidgetEncoderHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetEncoder_getMinDataRate(PhidgetEncoderHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetEncoder_getMaxDataRate(PhidgetEncoderHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetEncoder_getIndexPosition(PhidgetEncoderHandle ch, int64_t *indexPosition);
 PhidgetReturnCode PhidgetEncoder_setIOMode(PhidgetEncoderHandle ch, Phidget_EncoderIOMode IOMode);
 PhidgetReturnCode PhidgetEncoder_getIOMode(PhidgetEncoderHandle ch, Phidget_EncoderIOMode *IOMode);
 PhidgetReturnCode PhidgetEncoder_setPosition(PhidgetEncoderHandle ch, int64_t position);
 PhidgetReturnCode PhidgetEncoder_getPosition(PhidgetEncoderHandle ch, int64_t *position);
 PhidgetReturnCode PhidgetEncoder_setPositionChangeTrigger(PhidgetEncoderHandle ch,
  uint32_t positionChangeTrigger);
 PhidgetReturnCode PhidgetEncoder_getPositionChangeTrigger(PhidgetEncoderHandle ch,
  uint32_t *positionChangeTrigger);
 PhidgetReturnCode PhidgetEncoder_getMinPositionChangeTrigger(PhidgetEncoderHandle ch,
  uint32_t *minPositionChangeTrigger);
 PhidgetReturnCode PhidgetEncoder_getMaxPositionChangeTrigger(PhidgetEncoderHandle ch,
  uint32_t *maxPositionChangeTrigger);
typedef void ( *PhidgetEncoder_OnPositionChangeCallback)(PhidgetEncoderHandle ch, void *ctx,
  int positionChange, double timeChange, int indexTriggered);
 PhidgetReturnCode PhidgetEncoder_setOnPositionChangeHandler(PhidgetEncoderHandle ch,
  PhidgetEncoder_OnPositionChangeCallback fptr, void *ctx);
typedef struct _PhidgetFrequencyCounter *PhidgetFrequencyCounterHandle;
 PhidgetReturnCode PhidgetFrequencyCounter_create(PhidgetFrequencyCounterHandle *ch);
 PhidgetReturnCode PhidgetFrequencyCounter_delete(PhidgetFrequencyCounterHandle *ch);
 PhidgetReturnCode PhidgetFrequencyCounter_reset(PhidgetFrequencyCounterHandle ch);
 PhidgetReturnCode PhidgetFrequencyCounter_getCount(PhidgetFrequencyCounterHandle ch, uint64_t *count);
 PhidgetReturnCode PhidgetFrequencyCounter_setEnabled(PhidgetFrequencyCounterHandle ch, int enabled);
 PhidgetReturnCode PhidgetFrequencyCounter_getEnabled(PhidgetFrequencyCounterHandle ch, int *enabled);
 PhidgetReturnCode PhidgetFrequencyCounter_setDataInterval(PhidgetFrequencyCounterHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetFrequencyCounter_getDataInterval(PhidgetFrequencyCounterHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetFrequencyCounter_getMinDataInterval(PhidgetFrequencyCounterHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetFrequencyCounter_getMaxDataInterval(PhidgetFrequencyCounterHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetFrequencyCounter_setDataRate(PhidgetFrequencyCounterHandle ch, double dataRate);
 PhidgetReturnCode PhidgetFrequencyCounter_getDataRate(PhidgetFrequencyCounterHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetFrequencyCounter_getMinDataRate(PhidgetFrequencyCounterHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetFrequencyCounter_getMaxDataRate(PhidgetFrequencyCounterHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetFrequencyCounter_setFilterType(PhidgetFrequencyCounterHandle ch,
  PhidgetFrequencyCounter_FilterType filterType);
 PhidgetReturnCode PhidgetFrequencyCounter_getFilterType(PhidgetFrequencyCounterHandle ch,
  PhidgetFrequencyCounter_FilterType *filterType);
 PhidgetReturnCode PhidgetFrequencyCounter_getFrequency(PhidgetFrequencyCounterHandle ch,
  double *frequency);
 PhidgetReturnCode PhidgetFrequencyCounter_getMaxFrequency(PhidgetFrequencyCounterHandle ch,
  double *maxFrequency);
 PhidgetReturnCode PhidgetFrequencyCounter_setFrequencyCutoff(PhidgetFrequencyCounterHandle ch,
  double frequencyCutoff);
 PhidgetReturnCode PhidgetFrequencyCounter_getFrequencyCutoff(PhidgetFrequencyCounterHandle ch,
  double *frequencyCutoff);
 PhidgetReturnCode PhidgetFrequencyCounter_getMinFrequencyCutoff(PhidgetFrequencyCounterHandle ch,
  double *minFrequencyCutoff);
 PhidgetReturnCode PhidgetFrequencyCounter_getMaxFrequencyCutoff(PhidgetFrequencyCounterHandle ch,
  double *maxFrequencyCutoff);
 PhidgetReturnCode PhidgetFrequencyCounter_setInputMode(PhidgetFrequencyCounterHandle ch,
  Phidget_InputMode inputMode);
 PhidgetReturnCode PhidgetFrequencyCounter_getInputMode(PhidgetFrequencyCounterHandle ch,
  Phidget_InputMode *inputMode);
 PhidgetReturnCode PhidgetFrequencyCounter_setPowerSupply(PhidgetFrequencyCounterHandle ch,
  Phidget_PowerSupply powerSupply);
 PhidgetReturnCode PhidgetFrequencyCounter_getPowerSupply(PhidgetFrequencyCounterHandle ch,
  Phidget_PowerSupply *powerSupply);
 PhidgetReturnCode PhidgetFrequencyCounter_getTimeElapsed(PhidgetFrequencyCounterHandle ch,
  double *timeElapsed);
typedef void ( *PhidgetFrequencyCounter_OnCountChangeCallback)(PhidgetFrequencyCounterHandle ch,
  void *ctx, uint64_t counts, double timeChange);
 PhidgetReturnCode PhidgetFrequencyCounter_setOnCountChangeHandler(PhidgetFrequencyCounterHandle ch,
  PhidgetFrequencyCounter_OnCountChangeCallback fptr, void *ctx);
typedef void ( *PhidgetFrequencyCounter_OnFrequencyChangeCallback)(PhidgetFrequencyCounterHandle ch,
  void *ctx, double frequency);
 PhidgetReturnCode PhidgetFrequencyCounter_setOnFrequencyChangeHandler(PhidgetFrequencyCounterHandle ch,
  PhidgetFrequencyCounter_OnFrequencyChangeCallback fptr, void *ctx);
typedef struct _PhidgetIR *PhidgetIRHandle;
 PhidgetReturnCode PhidgetIR_create(PhidgetIRHandle *ch);
 PhidgetReturnCode PhidgetIR_delete(PhidgetIRHandle *ch);
 PhidgetReturnCode PhidgetIR_getLastCode(PhidgetIRHandle ch, char *code, size_t codeLen,
  uint32_t *bitCount);
 PhidgetReturnCode PhidgetIR_getLastLearnedCode(PhidgetIRHandle ch, char *code, size_t codeLen,
  PhidgetIR_CodeInfo *codeInfo);
 PhidgetReturnCode PhidgetIR_transmit(PhidgetIRHandle ch, const char *code, PhidgetIR_CodeInfo *codeInfo);
 PhidgetReturnCode PhidgetIR_transmitRaw(PhidgetIRHandle ch, const uint32_t *data, size_t dataLen,
  uint32_t carrierFrequency, double dutyCycle, uint32_t gap);
 PhidgetReturnCode PhidgetIR_transmitRepeat(PhidgetIRHandle ch);
typedef void ( *PhidgetIR_OnCodeCallback)(PhidgetIRHandle ch, void *ctx, const char *code,
  uint32_t bitCount, int isRepeat);
 PhidgetReturnCode PhidgetIR_setOnCodeHandler(PhidgetIRHandle ch, PhidgetIR_OnCodeCallback fptr,
  void *ctx);
typedef void ( *PhidgetIR_OnLearnCallback)(PhidgetIRHandle ch, void *ctx, const char *code,
  PhidgetIR_CodeInfo *codeInfo);
 PhidgetReturnCode PhidgetIR_setOnLearnHandler(PhidgetIRHandle ch, PhidgetIR_OnLearnCallback fptr,
  void *ctx);
typedef void ( *PhidgetIR_OnRawDataCallback)(PhidgetIRHandle ch, void *ctx, const uint32_t *data,
  size_t dataLen);
 PhidgetReturnCode PhidgetIR_setOnRawDataHandler(PhidgetIRHandle ch, PhidgetIR_OnRawDataCallback fptr,
  void *ctx);
typedef struct _PhidgetPHSensor *PhidgetPHSensorHandle;
 PhidgetReturnCode PhidgetPHSensor_create(PhidgetPHSensorHandle *ch);
 PhidgetReturnCode PhidgetPHSensor_delete(PhidgetPHSensorHandle *ch);
 PhidgetReturnCode PhidgetPHSensor_setCorrectionTemperature(PhidgetPHSensorHandle ch,
  double correctionTemperature);
 PhidgetReturnCode PhidgetPHSensor_getCorrectionTemperature(PhidgetPHSensorHandle ch,
  double *correctionTemperature);
 PhidgetReturnCode PhidgetPHSensor_getMinCorrectionTemperature(PhidgetPHSensorHandle ch,
  double *minCorrectionTemperature);
 PhidgetReturnCode PhidgetPHSensor_getMaxCorrectionTemperature(PhidgetPHSensorHandle ch,
  double *maxCorrectionTemperature);
 PhidgetReturnCode PhidgetPHSensor_setDataInterval(PhidgetPHSensorHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetPHSensor_getDataInterval(PhidgetPHSensorHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetPHSensor_getMinDataInterval(PhidgetPHSensorHandle ch, uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetPHSensor_getMaxDataInterval(PhidgetPHSensorHandle ch, uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetPHSensor_setDataRate(PhidgetPHSensorHandle ch, double dataRate);
 PhidgetReturnCode PhidgetPHSensor_getDataRate(PhidgetPHSensorHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetPHSensor_getMinDataRate(PhidgetPHSensorHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetPHSensor_getMaxDataRate(PhidgetPHSensorHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetPHSensor_getPH(PhidgetPHSensorHandle ch, double *PH);
 PhidgetReturnCode PhidgetPHSensor_getMinPH(PhidgetPHSensorHandle ch, double *minPH);
 PhidgetReturnCode PhidgetPHSensor_getMaxPH(PhidgetPHSensorHandle ch, double *maxPH);
 PhidgetReturnCode PhidgetPHSensor_setPHChangeTrigger(PhidgetPHSensorHandle ch, double PHChangeTrigger);
 PhidgetReturnCode PhidgetPHSensor_getPHChangeTrigger(PhidgetPHSensorHandle ch, double *PHChangeTrigger);
 PhidgetReturnCode PhidgetPHSensor_getMinPHChangeTrigger(PhidgetPHSensorHandle ch,
  double *minPHChangeTrigger);
 PhidgetReturnCode PhidgetPHSensor_getMaxPHChangeTrigger(PhidgetPHSensorHandle ch,
  double *maxPHChangeTrigger);
typedef void ( *PhidgetPHSensor_OnPHChangeCallback)(PhidgetPHSensorHandle ch, void *ctx,
  double PH);
 PhidgetReturnCode PhidgetPHSensor_setOnPHChangeHandler(PhidgetPHSensorHandle ch,
  PhidgetPHSensor_OnPHChangeCallback fptr, void *ctx);
typedef struct _PhidgetDCMotor *PhidgetDCMotorHandle;
 PhidgetReturnCode PhidgetDCMotor_create(PhidgetDCMotorHandle *ch);
 PhidgetReturnCode PhidgetDCMotor_delete(PhidgetDCMotorHandle *ch);
 PhidgetReturnCode PhidgetDCMotor_enableFailsafe(PhidgetDCMotorHandle ch, uint32_t failsafeTime);
 PhidgetReturnCode PhidgetDCMotor_resetFailsafe(PhidgetDCMotorHandle ch);
 PhidgetReturnCode PhidgetDCMotor_setAcceleration(PhidgetDCMotorHandle ch, double acceleration);
 PhidgetReturnCode PhidgetDCMotor_getAcceleration(PhidgetDCMotorHandle ch, double *acceleration);
 PhidgetReturnCode PhidgetDCMotor_getMinAcceleration(PhidgetDCMotorHandle ch, double *minAcceleration);
 PhidgetReturnCode PhidgetDCMotor_getMaxAcceleration(PhidgetDCMotorHandle ch, double *maxAcceleration);
 PhidgetReturnCode PhidgetDCMotor_getBackEMF(PhidgetDCMotorHandle ch, double *backEMF);
 PhidgetReturnCode PhidgetDCMotor_setBackEMFSensingState(PhidgetDCMotorHandle ch, int backEMFSensingState);
 PhidgetReturnCode PhidgetDCMotor_getBackEMFSensingState(PhidgetDCMotorHandle ch,
  int *backEMFSensingState);
 PhidgetReturnCode PhidgetDCMotor_getBrakingStrength(PhidgetDCMotorHandle ch, double *brakingStrength);
 PhidgetReturnCode PhidgetDCMotor_getMinBrakingStrength(PhidgetDCMotorHandle ch,
  double *minBrakingStrength);
 PhidgetReturnCode PhidgetDCMotor_getMaxBrakingStrength(PhidgetDCMotorHandle ch,
  double *maxBrakingStrength);
 PhidgetReturnCode PhidgetDCMotor_setCurrentLimit(PhidgetDCMotorHandle ch, double currentLimit);
 PhidgetReturnCode PhidgetDCMotor_getCurrentLimit(PhidgetDCMotorHandle ch, double *currentLimit);
 PhidgetReturnCode PhidgetDCMotor_getMinCurrentLimit(PhidgetDCMotorHandle ch, double *minCurrentLimit);
 PhidgetReturnCode PhidgetDCMotor_getMaxCurrentLimit(PhidgetDCMotorHandle ch, double *maxCurrentLimit);
 PhidgetReturnCode PhidgetDCMotor_setCurrentRegulatorGain(PhidgetDCMotorHandle ch,
  double currentRegulatorGain);
 PhidgetReturnCode PhidgetDCMotor_getCurrentRegulatorGain(PhidgetDCMotorHandle ch,
  double *currentRegulatorGain);
 PhidgetReturnCode PhidgetDCMotor_getMinCurrentRegulatorGain(PhidgetDCMotorHandle ch,
  double *minCurrentRegulatorGain);
 PhidgetReturnCode PhidgetDCMotor_getMaxCurrentRegulatorGain(PhidgetDCMotorHandle ch,
  double *maxCurrentRegulatorGain);
 PhidgetReturnCode PhidgetDCMotor_setDataInterval(PhidgetDCMotorHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetDCMotor_getDataInterval(PhidgetDCMotorHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetDCMotor_getMinDataInterval(PhidgetDCMotorHandle ch, uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetDCMotor_getMaxDataInterval(PhidgetDCMotorHandle ch, uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetDCMotor_setDataRate(PhidgetDCMotorHandle ch, double dataRate);
 PhidgetReturnCode PhidgetDCMotor_getDataRate(PhidgetDCMotorHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetDCMotor_getMinDataRate(PhidgetDCMotorHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetDCMotor_getMaxDataRate(PhidgetDCMotorHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetDCMotor_getMinFailsafeTime(PhidgetDCMotorHandle ch, uint32_t *minFailsafeTime);
 PhidgetReturnCode PhidgetDCMotor_getMaxFailsafeTime(PhidgetDCMotorHandle ch, uint32_t *maxFailsafeTime);
 PhidgetReturnCode PhidgetDCMotor_setFanMode(PhidgetDCMotorHandle ch, Phidget_FanMode fanMode);
 PhidgetReturnCode PhidgetDCMotor_getFanMode(PhidgetDCMotorHandle ch, Phidget_FanMode *fanMode);
 PhidgetReturnCode PhidgetDCMotor_setTargetBrakingStrength(PhidgetDCMotorHandle ch,
  double targetBrakingStrength);
 PhidgetReturnCode PhidgetDCMotor_getTargetBrakingStrength(PhidgetDCMotorHandle ch,
  double *targetBrakingStrength);
 PhidgetReturnCode PhidgetDCMotor_setTargetVelocity(PhidgetDCMotorHandle ch, double targetVelocity);
 void PhidgetDCMotor_setTargetVelocity_async(PhidgetDCMotorHandle ch, double targetVelocity,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetDCMotor_getTargetVelocity(PhidgetDCMotorHandle ch, double *targetVelocity);
 PhidgetReturnCode PhidgetDCMotor_getVelocity(PhidgetDCMotorHandle ch, double *velocity);
 PhidgetReturnCode PhidgetDCMotor_getMinVelocity(PhidgetDCMotorHandle ch, double *minVelocity);
 PhidgetReturnCode PhidgetDCMotor_getMaxVelocity(PhidgetDCMotorHandle ch, double *maxVelocity);
typedef void ( *PhidgetDCMotor_OnBackEMFChangeCallback)(PhidgetDCMotorHandle ch, void *ctx,
  double backEMF);
 PhidgetReturnCode PhidgetDCMotor_setOnBackEMFChangeHandler(PhidgetDCMotorHandle ch,
  PhidgetDCMotor_OnBackEMFChangeCallback fptr, void *ctx);
typedef void ( *PhidgetDCMotor_OnBrakingStrengthChangeCallback)(PhidgetDCMotorHandle ch, void *ctx,
  double brakingStrength);
 PhidgetReturnCode PhidgetDCMotor_setOnBrakingStrengthChangeHandler(PhidgetDCMotorHandle ch,
  PhidgetDCMotor_OnBrakingStrengthChangeCallback fptr, void *ctx);
typedef void ( *PhidgetDCMotor_OnVelocityUpdateCallback)(PhidgetDCMotorHandle ch, void *ctx,
  double velocity);
 PhidgetReturnCode PhidgetDCMotor_setOnVelocityUpdateHandler(PhidgetDCMotorHandle ch,
  PhidgetDCMotor_OnVelocityUpdateCallback fptr, void *ctx);
typedef struct _PhidgetCurrentInput *PhidgetCurrentInputHandle;
 PhidgetReturnCode PhidgetCurrentInput_create(PhidgetCurrentInputHandle *ch);
 PhidgetReturnCode PhidgetCurrentInput_delete(PhidgetCurrentInputHandle *ch);
 PhidgetReturnCode PhidgetCurrentInput_getCurrent(PhidgetCurrentInputHandle ch, double *current);
 PhidgetReturnCode PhidgetCurrentInput_getMinCurrent(PhidgetCurrentInputHandle ch, double *minCurrent);
 PhidgetReturnCode PhidgetCurrentInput_getMaxCurrent(PhidgetCurrentInputHandle ch, double *maxCurrent);
 PhidgetReturnCode PhidgetCurrentInput_setCurrentChangeTrigger(PhidgetCurrentInputHandle ch,
  double currentChangeTrigger);
 PhidgetReturnCode PhidgetCurrentInput_getCurrentChangeTrigger(PhidgetCurrentInputHandle ch,
  double *currentChangeTrigger);
 PhidgetReturnCode PhidgetCurrentInput_getMinCurrentChangeTrigger(PhidgetCurrentInputHandle ch,
  double *minCurrentChangeTrigger);
 PhidgetReturnCode PhidgetCurrentInput_getMaxCurrentChangeTrigger(PhidgetCurrentInputHandle ch,
  double *maxCurrentChangeTrigger);
 PhidgetReturnCode PhidgetCurrentInput_setDataInterval(PhidgetCurrentInputHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetCurrentInput_getDataInterval(PhidgetCurrentInputHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetCurrentInput_getMinDataInterval(PhidgetCurrentInputHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetCurrentInput_getMaxDataInterval(PhidgetCurrentInputHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetCurrentInput_setDataRate(PhidgetCurrentInputHandle ch, double dataRate);
 PhidgetReturnCode PhidgetCurrentInput_getDataRate(PhidgetCurrentInputHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetCurrentInput_getMinDataRate(PhidgetCurrentInputHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetCurrentInput_getMaxDataRate(PhidgetCurrentInputHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetCurrentInput_setPowerSupply(PhidgetCurrentInputHandle ch,
  Phidget_PowerSupply powerSupply);
 PhidgetReturnCode PhidgetCurrentInput_getPowerSupply(PhidgetCurrentInputHandle ch,
  Phidget_PowerSupply *powerSupply);
typedef void ( *PhidgetCurrentInput_OnCurrentChangeCallback)(PhidgetCurrentInputHandle ch, void *ctx,
  double current);
 PhidgetReturnCode PhidgetCurrentInput_setOnCurrentChangeHandler(PhidgetCurrentInputHandle ch,
  PhidgetCurrentInput_OnCurrentChangeCallback fptr, void *ctx);
typedef struct _PhidgetStepper *PhidgetStepperHandle;
 PhidgetReturnCode PhidgetStepper_create(PhidgetStepperHandle *ch);
 PhidgetReturnCode PhidgetStepper_delete(PhidgetStepperHandle *ch);
 PhidgetReturnCode PhidgetStepper_enableFailsafe(PhidgetStepperHandle ch, uint32_t failsafeTime);
 PhidgetReturnCode PhidgetStepper_addPositionOffset(PhidgetStepperHandle ch, double positionOffset);
 PhidgetReturnCode PhidgetStepper_resetFailsafe(PhidgetStepperHandle ch);
 PhidgetReturnCode PhidgetStepper_setAcceleration(PhidgetStepperHandle ch, double acceleration);
 PhidgetReturnCode PhidgetStepper_getAcceleration(PhidgetStepperHandle ch, double *acceleration);
 PhidgetReturnCode PhidgetStepper_getMinAcceleration(PhidgetStepperHandle ch, double *minAcceleration);
 PhidgetReturnCode PhidgetStepper_getMaxAcceleration(PhidgetStepperHandle ch, double *maxAcceleration);
 PhidgetReturnCode PhidgetStepper_setControlMode(PhidgetStepperHandle ch,
  PhidgetStepper_ControlMode controlMode);
 PhidgetReturnCode PhidgetStepper_getControlMode(PhidgetStepperHandle ch,
  PhidgetStepper_ControlMode *controlMode);
 PhidgetReturnCode PhidgetStepper_setCurrentLimit(PhidgetStepperHandle ch, double currentLimit);
 PhidgetReturnCode PhidgetStepper_getCurrentLimit(PhidgetStepperHandle ch, double *currentLimit);
 PhidgetReturnCode PhidgetStepper_getMinCurrentLimit(PhidgetStepperHandle ch, double *minCurrentLimit);
 PhidgetReturnCode PhidgetStepper_getMaxCurrentLimit(PhidgetStepperHandle ch, double *maxCurrentLimit);
 PhidgetReturnCode PhidgetStepper_setDataInterval(PhidgetStepperHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetStepper_getDataInterval(PhidgetStepperHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetStepper_getMinDataInterval(PhidgetStepperHandle ch, uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetStepper_getMaxDataInterval(PhidgetStepperHandle ch, uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetStepper_setDataRate(PhidgetStepperHandle ch, double dataRate);
 PhidgetReturnCode PhidgetStepper_getDataRate(PhidgetStepperHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetStepper_getMinDataRate(PhidgetStepperHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetStepper_getMaxDataRate(PhidgetStepperHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetStepper_setEngaged(PhidgetStepperHandle ch, int engaged);
 PhidgetReturnCode PhidgetStepper_getEngaged(PhidgetStepperHandle ch, int *engaged);
 PhidgetReturnCode PhidgetStepper_getMinFailsafeTime(PhidgetStepperHandle ch, uint32_t *minFailsafeTime);
 PhidgetReturnCode PhidgetStepper_getMaxFailsafeTime(PhidgetStepperHandle ch, uint32_t *maxFailsafeTime);
 PhidgetReturnCode PhidgetStepper_setHoldingCurrentLimit(PhidgetStepperHandle ch,
  double holdingCurrentLimit);
 PhidgetReturnCode PhidgetStepper_getHoldingCurrentLimit(PhidgetStepperHandle ch,
  double *holdingCurrentLimit);
 PhidgetReturnCode PhidgetStepper_getIsMoving(PhidgetStepperHandle ch, int *isMoving);
 PhidgetReturnCode PhidgetStepper_getPosition(PhidgetStepperHandle ch, double *position);
 PhidgetReturnCode PhidgetStepper_getMinPosition(PhidgetStepperHandle ch, double *minPosition);
 PhidgetReturnCode PhidgetStepper_getMaxPosition(PhidgetStepperHandle ch, double *maxPosition);
 PhidgetReturnCode PhidgetStepper_setRescaleFactor(PhidgetStepperHandle ch, double rescaleFactor);
 PhidgetReturnCode PhidgetStepper_getRescaleFactor(PhidgetStepperHandle ch, double *rescaleFactor);
 PhidgetReturnCode PhidgetStepper_setTargetPosition(PhidgetStepperHandle ch, double targetPosition);
 void PhidgetStepper_setTargetPosition_async(PhidgetStepperHandle ch, double targetPosition,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetStepper_getTargetPosition(PhidgetStepperHandle ch, double *targetPosition);
 PhidgetReturnCode PhidgetStepper_getVelocity(PhidgetStepperHandle ch, double *velocity);
 PhidgetReturnCode PhidgetStepper_setVelocityLimit(PhidgetStepperHandle ch, double velocityLimit);
 PhidgetReturnCode PhidgetStepper_getVelocityLimit(PhidgetStepperHandle ch, double *velocityLimit);
 PhidgetReturnCode PhidgetStepper_getMinVelocityLimit(PhidgetStepperHandle ch, double *minVelocityLimit);
 PhidgetReturnCode PhidgetStepper_getMaxVelocityLimit(PhidgetStepperHandle ch, double *maxVelocityLimit);
typedef void ( *PhidgetStepper_OnPositionChangeCallback)(PhidgetStepperHandle ch, void *ctx,
  double position);
 PhidgetReturnCode PhidgetStepper_setOnPositionChangeHandler(PhidgetStepperHandle ch,
  PhidgetStepper_OnPositionChangeCallback fptr, void *ctx);
typedef void ( *PhidgetStepper_OnStoppedCallback)(PhidgetStepperHandle ch, void *ctx);
 PhidgetReturnCode PhidgetStepper_setOnStoppedHandler(PhidgetStepperHandle ch,
  PhidgetStepper_OnStoppedCallback fptr, void *ctx);
typedef void ( *PhidgetStepper_OnVelocityChangeCallback)(PhidgetStepperHandle ch, void *ctx,
  double velocity);
 PhidgetReturnCode PhidgetStepper_setOnVelocityChangeHandler(PhidgetStepperHandle ch,
  PhidgetStepper_OnVelocityChangeCallback fptr, void *ctx);
typedef struct _PhidgetLCD *PhidgetLCDHandle;
 PhidgetReturnCode PhidgetLCD_create(PhidgetLCDHandle *ch);
 PhidgetReturnCode PhidgetLCD_delete(PhidgetLCDHandle *ch);
 PhidgetReturnCode PhidgetLCD_setCharacterBitmap(PhidgetLCDHandle ch, PhidgetLCD_Font font,
  const char *character, const uint8_t *bitmap);
 void PhidgetLCD_setCharacterBitmap_async(PhidgetLCDHandle ch, PhidgetLCD_Font font,
  const char *character, const uint8_t *bitmap, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_getMaxCharacters(PhidgetLCDHandle ch, PhidgetLCD_Font font,
  int *maxCharacters);
 PhidgetReturnCode PhidgetLCD_clear(PhidgetLCDHandle ch);
 void PhidgetLCD_clear_async(PhidgetLCDHandle ch, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_copy(PhidgetLCDHandle ch, int sourceFramebuffer, int destFramebuffer,
  int sourceX1, int sourceY1, int sourceX2, int sourceY2, int destX, int destY, int inverted);
 void PhidgetLCD_copy_async(PhidgetLCDHandle ch, int sourceFramebuffer, int destFramebuffer,
  int sourceX1, int sourceY1, int sourceX2, int sourceY2, int destX, int destY, int inverted, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_drawLine(PhidgetLCDHandle ch, int x1, int y1, int x2, int y2);
 void PhidgetLCD_drawLine_async(PhidgetLCDHandle ch, int x1, int y1, int x2, int y2,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_drawPixel(PhidgetLCDHandle ch, int x, int y,
  PhidgetLCD_PixelState pixelState);
 void PhidgetLCD_drawPixel_async(PhidgetLCDHandle ch, int x, int y,
  PhidgetLCD_PixelState pixelState, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_drawRect(PhidgetLCDHandle ch, int x1, int y1, int x2, int y2, int filled,
  int inverted);
 void PhidgetLCD_drawRect_async(PhidgetLCDHandle ch, int x1, int y1, int x2, int y2, int filled,
  int inverted, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_flush(PhidgetLCDHandle ch);
 void PhidgetLCD_flush_async(PhidgetLCDHandle ch, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_getFontSize(PhidgetLCDHandle ch, PhidgetLCD_Font font, int *width,
  int *height);
 PhidgetReturnCode PhidgetLCD_setFontSize(PhidgetLCDHandle ch, PhidgetLCD_Font font, int width,
  int height);
 PhidgetReturnCode PhidgetLCD_initialize(PhidgetLCDHandle ch);
 PhidgetReturnCode PhidgetLCD_saveFrameBuffer(PhidgetLCDHandle ch, int frameBuffer);
 void PhidgetLCD_saveFrameBuffer_async(PhidgetLCDHandle ch, int frameBuffer,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_writeBitmap(PhidgetLCDHandle ch, int xPosition, int yPosition, int xSize,
  int ySize, const uint8_t *bitmap);
 void PhidgetLCD_writeBitmap_async(PhidgetLCDHandle ch, int xPosition, int yPosition, int xSize,
  int ySize, const uint8_t *bitmap, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_writeText(PhidgetLCDHandle ch, PhidgetLCD_Font font, int xPosition,
  int yPosition, const char *text);
 void PhidgetLCD_writeText_async(PhidgetLCDHandle ch, PhidgetLCD_Font font, int xPosition,
  int yPosition, const char *text, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_setAutoFlush(PhidgetLCDHandle ch, int autoFlush);
 PhidgetReturnCode PhidgetLCD_getAutoFlush(PhidgetLCDHandle ch, int *autoFlush);
 PhidgetReturnCode PhidgetLCD_setBacklight(PhidgetLCDHandle ch, double backlight);
 PhidgetReturnCode PhidgetLCD_getBacklight(PhidgetLCDHandle ch, double *backlight);
 PhidgetReturnCode PhidgetLCD_getMinBacklight(PhidgetLCDHandle ch, double *minBacklight);
 PhidgetReturnCode PhidgetLCD_getMaxBacklight(PhidgetLCDHandle ch, double *maxBacklight);
 PhidgetReturnCode PhidgetLCD_setContrast(PhidgetLCDHandle ch, double contrast);
 PhidgetReturnCode PhidgetLCD_getContrast(PhidgetLCDHandle ch, double *contrast);
 PhidgetReturnCode PhidgetLCD_getMinContrast(PhidgetLCDHandle ch, double *minContrast);
 PhidgetReturnCode PhidgetLCD_getMaxContrast(PhidgetLCDHandle ch, double *maxContrast);
 PhidgetReturnCode PhidgetLCD_setCursorBlink(PhidgetLCDHandle ch, int cursorBlink);
 PhidgetReturnCode PhidgetLCD_getCursorBlink(PhidgetLCDHandle ch, int *cursorBlink);
 PhidgetReturnCode PhidgetLCD_setCursorOn(PhidgetLCDHandle ch, int cursorOn);
 PhidgetReturnCode PhidgetLCD_getCursorOn(PhidgetLCDHandle ch, int *cursorOn);
 PhidgetReturnCode PhidgetLCD_setFrameBuffer(PhidgetLCDHandle ch, int frameBuffer);
 void PhidgetLCD_setFrameBuffer_async(PhidgetLCDHandle ch, int frameBuffer,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetLCD_getFrameBuffer(PhidgetLCDHandle ch, int *frameBuffer);
 PhidgetReturnCode PhidgetLCD_getHeight(PhidgetLCDHandle ch, int *height);
 PhidgetReturnCode PhidgetLCD_setScreenSize(PhidgetLCDHandle ch, PhidgetLCD_ScreenSize screenSize);
 PhidgetReturnCode PhidgetLCD_getScreenSize(PhidgetLCDHandle ch, PhidgetLCD_ScreenSize *screenSize);
 PhidgetReturnCode PhidgetLCD_setSleeping(PhidgetLCDHandle ch, int sleeping);
 PhidgetReturnCode PhidgetLCD_getSleeping(PhidgetLCDHandle ch, int *sleeping);
 PhidgetReturnCode PhidgetLCD_getWidth(PhidgetLCDHandle ch, int *width);
typedef struct _PhidgetMotorPositionController *PhidgetMotorPositionControllerHandle;
 PhidgetReturnCode PhidgetMotorPositionController_create(PhidgetMotorPositionControllerHandle *ch);
 PhidgetReturnCode PhidgetMotorPositionController_delete(PhidgetMotorPositionControllerHandle *ch);
 PhidgetReturnCode PhidgetMotorPositionController_enableFailsafe(PhidgetMotorPositionControllerHandle ch,
  uint32_t failsafeTime);
 PhidgetReturnCode PhidgetMotorPositionController_addPositionOffset(PhidgetMotorPositionControllerHandle ch,
  double positionOffset);
 PhidgetReturnCode PhidgetMotorPositionController_resetFailsafe(PhidgetMotorPositionControllerHandle ch);
 PhidgetReturnCode PhidgetMotorPositionController_setAcceleration(PhidgetMotorPositionControllerHandle ch,
  double acceleration);
 PhidgetReturnCode PhidgetMotorPositionController_getAcceleration(PhidgetMotorPositionControllerHandle ch,
  double *acceleration);
 PhidgetReturnCode PhidgetMotorPositionController_getMinAcceleration(PhidgetMotorPositionControllerHandle ch,
  double *minAcceleration);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxAcceleration(PhidgetMotorPositionControllerHandle ch,
  double *maxAcceleration);
 PhidgetReturnCode PhidgetMotorPositionController_setCurrentLimit(PhidgetMotorPositionControllerHandle ch,
  double currentLimit);
 PhidgetReturnCode PhidgetMotorPositionController_getCurrentLimit(PhidgetMotorPositionControllerHandle ch,
  double *currentLimit);
 PhidgetReturnCode PhidgetMotorPositionController_getMinCurrentLimit(PhidgetMotorPositionControllerHandle ch,
  double *minCurrentLimit);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxCurrentLimit(PhidgetMotorPositionControllerHandle ch,
  double *maxCurrentLimit);
 PhidgetReturnCode PhidgetMotorPositionController_setCurrentRegulatorGain(PhidgetMotorPositionControllerHandle ch, double currentRegulatorGain);
 PhidgetReturnCode PhidgetMotorPositionController_getCurrentRegulatorGain(PhidgetMotorPositionControllerHandle ch, double *currentRegulatorGain);
 PhidgetReturnCode PhidgetMotorPositionController_getMinCurrentRegulatorGain(PhidgetMotorPositionControllerHandle ch, double *minCurrentRegulatorGain);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxCurrentRegulatorGain(PhidgetMotorPositionControllerHandle ch, double *maxCurrentRegulatorGain);
 PhidgetReturnCode PhidgetMotorPositionController_setDataInterval(PhidgetMotorPositionControllerHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetMotorPositionController_getDataInterval(PhidgetMotorPositionControllerHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetMotorPositionController_getMinDataInterval(PhidgetMotorPositionControllerHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxDataInterval(PhidgetMotorPositionControllerHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetMotorPositionController_setDataRate(PhidgetMotorPositionControllerHandle ch,
  double dataRate);
 PhidgetReturnCode PhidgetMotorPositionController_getDataRate(PhidgetMotorPositionControllerHandle ch,
  double *dataRate);
 PhidgetReturnCode PhidgetMotorPositionController_getMinDataRate(PhidgetMotorPositionControllerHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxDataRate(PhidgetMotorPositionControllerHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetMotorPositionController_setDeadBand(PhidgetMotorPositionControllerHandle ch,
  double deadBand);
 PhidgetReturnCode PhidgetMotorPositionController_getDeadBand(PhidgetMotorPositionControllerHandle ch,
  double *deadBand);
 PhidgetReturnCode PhidgetMotorPositionController_getDutyCycle(PhidgetMotorPositionControllerHandle ch,
  double *dutyCycle);
 PhidgetReturnCode PhidgetMotorPositionController_setEngaged(PhidgetMotorPositionControllerHandle ch,
  int engaged);
 PhidgetReturnCode PhidgetMotorPositionController_getEngaged(PhidgetMotorPositionControllerHandle ch,
  int *engaged);
 PhidgetReturnCode PhidgetMotorPositionController_getMinFailsafeTime(PhidgetMotorPositionControllerHandle ch,
  uint32_t *minFailsafeTime);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxFailsafeTime(PhidgetMotorPositionControllerHandle ch,
  uint32_t *maxFailsafeTime);
 PhidgetReturnCode PhidgetMotorPositionController_setFanMode(PhidgetMotorPositionControllerHandle ch,
  Phidget_FanMode fanMode);
 PhidgetReturnCode PhidgetMotorPositionController_getFanMode(PhidgetMotorPositionControllerHandle ch,
  Phidget_FanMode *fanMode);
 PhidgetReturnCode PhidgetMotorPositionController_setIOMode(PhidgetMotorPositionControllerHandle ch,
  Phidget_EncoderIOMode IOMode);
 PhidgetReturnCode PhidgetMotorPositionController_getIOMode(PhidgetMotorPositionControllerHandle ch,
  Phidget_EncoderIOMode *IOMode);
 PhidgetReturnCode PhidgetMotorPositionController_setKd(PhidgetMotorPositionControllerHandle ch,
  double kd);
 PhidgetReturnCode PhidgetMotorPositionController_getKd(PhidgetMotorPositionControllerHandle ch,
  double *kd);
 PhidgetReturnCode PhidgetMotorPositionController_setKi(PhidgetMotorPositionControllerHandle ch,
  double ki);
 PhidgetReturnCode PhidgetMotorPositionController_getKi(PhidgetMotorPositionControllerHandle ch,
  double *ki);
 PhidgetReturnCode PhidgetMotorPositionController_setKp(PhidgetMotorPositionControllerHandle ch,
  double kp);
 PhidgetReturnCode PhidgetMotorPositionController_getKp(PhidgetMotorPositionControllerHandle ch,
  double *kp);
 PhidgetReturnCode PhidgetMotorPositionController_getPosition(PhidgetMotorPositionControllerHandle ch,
  double *position);
 PhidgetReturnCode PhidgetMotorPositionController_getMinPosition(PhidgetMotorPositionControllerHandle ch,
  double *minPosition);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxPosition(PhidgetMotorPositionControllerHandle ch,
  double *maxPosition);
 PhidgetReturnCode PhidgetMotorPositionController_setRescaleFactor(PhidgetMotorPositionControllerHandle ch,
  double rescaleFactor);
 PhidgetReturnCode PhidgetMotorPositionController_getRescaleFactor(PhidgetMotorPositionControllerHandle ch,
  double *rescaleFactor);
 PhidgetReturnCode PhidgetMotorPositionController_setStallVelocity(PhidgetMotorPositionControllerHandle ch,
  double stallVelocity);
 PhidgetReturnCode PhidgetMotorPositionController_getStallVelocity(PhidgetMotorPositionControllerHandle ch,
  double *stallVelocity);
 PhidgetReturnCode PhidgetMotorPositionController_getMinStallVelocity(PhidgetMotorPositionControllerHandle ch, double *minStallVelocity);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxStallVelocity(PhidgetMotorPositionControllerHandle ch, double *maxStallVelocity);
 PhidgetReturnCode PhidgetMotorPositionController_setTargetPosition(PhidgetMotorPositionControllerHandle ch,
  double targetPosition);
 void PhidgetMotorPositionController_setTargetPosition_async(PhidgetMotorPositionControllerHandle ch, double targetPosition, Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetMotorPositionController_getTargetPosition(PhidgetMotorPositionControllerHandle ch,
  double *targetPosition);
 PhidgetReturnCode PhidgetMotorPositionController_setVelocityLimit(PhidgetMotorPositionControllerHandle ch,
  double velocityLimit);
 PhidgetReturnCode PhidgetMotorPositionController_getVelocityLimit(PhidgetMotorPositionControllerHandle ch,
  double *velocityLimit);
 PhidgetReturnCode PhidgetMotorPositionController_getMinVelocityLimit(PhidgetMotorPositionControllerHandle ch, double *minVelocityLimit);
 PhidgetReturnCode PhidgetMotorPositionController_getMaxVelocityLimit(PhidgetMotorPositionControllerHandle ch, double *maxVelocityLimit);
typedef void ( *PhidgetMotorPositionController_OnDutyCycleUpdateCallback)(PhidgetMotorPositionControllerHandle ch, void *ctx, double dutyCycle);
 PhidgetReturnCode PhidgetMotorPositionController_setOnDutyCycleUpdateHandler(PhidgetMotorPositionControllerHandle ch, PhidgetMotorPositionController_OnDutyCycleUpdateCallback fptr, void *ctx);
typedef void ( *PhidgetMotorPositionController_OnPositionChangeCallback)(PhidgetMotorPositionControllerHandle ch, void *ctx, double position);
 PhidgetReturnCode PhidgetMotorPositionController_setOnPositionChangeHandler(PhidgetMotorPositionControllerHandle ch, PhidgetMotorPositionController_OnPositionChangeCallback fptr, void *ctx);
typedef struct _PhidgetBLDCMotor *PhidgetBLDCMotorHandle;
 PhidgetReturnCode PhidgetBLDCMotor_create(PhidgetBLDCMotorHandle *ch);
 PhidgetReturnCode PhidgetBLDCMotor_delete(PhidgetBLDCMotorHandle *ch);
 PhidgetReturnCode PhidgetBLDCMotor_enableFailsafe(PhidgetBLDCMotorHandle ch, uint32_t failsafeTime);
 PhidgetReturnCode PhidgetBLDCMotor_addPositionOffset(PhidgetBLDCMotorHandle ch, double positionOffset);
 PhidgetReturnCode PhidgetBLDCMotor_resetFailsafe(PhidgetBLDCMotorHandle ch);
 PhidgetReturnCode PhidgetBLDCMotor_setAcceleration(PhidgetBLDCMotorHandle ch, double acceleration);
 PhidgetReturnCode PhidgetBLDCMotor_getAcceleration(PhidgetBLDCMotorHandle ch, double *acceleration);
 PhidgetReturnCode PhidgetBLDCMotor_getMinAcceleration(PhidgetBLDCMotorHandle ch, double *minAcceleration);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxAcceleration(PhidgetBLDCMotorHandle ch, double *maxAcceleration);
 PhidgetReturnCode PhidgetBLDCMotor_getBrakingStrength(PhidgetBLDCMotorHandle ch, double *brakingStrength);
 PhidgetReturnCode PhidgetBLDCMotor_getMinBrakingStrength(PhidgetBLDCMotorHandle ch,
  double *minBrakingStrength);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxBrakingStrength(PhidgetBLDCMotorHandle ch,
  double *maxBrakingStrength);
 PhidgetReturnCode PhidgetBLDCMotor_setCurrentLimit(PhidgetBLDCMotorHandle ch, double currentLimit);
 PhidgetReturnCode PhidgetBLDCMotor_getCurrentLimit(PhidgetBLDCMotorHandle ch, double *currentLimit);
 PhidgetReturnCode PhidgetBLDCMotor_getMinCurrentLimit(PhidgetBLDCMotorHandle ch, double *minCurrentLimit);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxCurrentLimit(PhidgetBLDCMotorHandle ch, double *maxCurrentLimit);
 PhidgetReturnCode PhidgetBLDCMotor_setDataInterval(PhidgetBLDCMotorHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetBLDCMotor_getDataInterval(PhidgetBLDCMotorHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetBLDCMotor_getMinDataInterval(PhidgetBLDCMotorHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxDataInterval(PhidgetBLDCMotorHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetBLDCMotor_setDataRate(PhidgetBLDCMotorHandle ch, double dataRate);
 PhidgetReturnCode PhidgetBLDCMotor_getDataRate(PhidgetBLDCMotorHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetBLDCMotor_getMinDataRate(PhidgetBLDCMotorHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxDataRate(PhidgetBLDCMotorHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetBLDCMotor_getMinFailsafeTime(PhidgetBLDCMotorHandle ch,
  uint32_t *minFailsafeTime);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxFailsafeTime(PhidgetBLDCMotorHandle ch,
  uint32_t *maxFailsafeTime);
 PhidgetReturnCode PhidgetBLDCMotor_getPosition(PhidgetBLDCMotorHandle ch, double *position);
 PhidgetReturnCode PhidgetBLDCMotor_getMinPosition(PhidgetBLDCMotorHandle ch, double *minPosition);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxPosition(PhidgetBLDCMotorHandle ch, double *maxPosition);
 PhidgetReturnCode PhidgetBLDCMotor_setRescaleFactor(PhidgetBLDCMotorHandle ch, double rescaleFactor);
 PhidgetReturnCode PhidgetBLDCMotor_getRescaleFactor(PhidgetBLDCMotorHandle ch, double *rescaleFactor);
 PhidgetReturnCode PhidgetBLDCMotor_setStallVelocity(PhidgetBLDCMotorHandle ch, double stallVelocity);
 PhidgetReturnCode PhidgetBLDCMotor_getStallVelocity(PhidgetBLDCMotorHandle ch, double *stallVelocity);
 PhidgetReturnCode PhidgetBLDCMotor_getMinStallVelocity(PhidgetBLDCMotorHandle ch,
  double *minStallVelocity);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxStallVelocity(PhidgetBLDCMotorHandle ch,
  double *maxStallVelocity);
 PhidgetReturnCode PhidgetBLDCMotor_setTargetBrakingStrength(PhidgetBLDCMotorHandle ch,
  double targetBrakingStrength);
 PhidgetReturnCode PhidgetBLDCMotor_getTargetBrakingStrength(PhidgetBLDCMotorHandle ch,
  double *targetBrakingStrength);
 PhidgetReturnCode PhidgetBLDCMotor_setTargetVelocity(PhidgetBLDCMotorHandle ch, double targetVelocity);
 void PhidgetBLDCMotor_setTargetVelocity_async(PhidgetBLDCMotorHandle ch, double targetVelocity,
  Phidget_AsyncCallback fptr, void *ctx);
 PhidgetReturnCode PhidgetBLDCMotor_getTargetVelocity(PhidgetBLDCMotorHandle ch, double *targetVelocity);
 PhidgetReturnCode PhidgetBLDCMotor_getVelocity(PhidgetBLDCMotorHandle ch, double *velocity);
 PhidgetReturnCode PhidgetBLDCMotor_getMinVelocity(PhidgetBLDCMotorHandle ch, double *minVelocity);
 PhidgetReturnCode PhidgetBLDCMotor_getMaxVelocity(PhidgetBLDCMotorHandle ch, double *maxVelocity);
typedef void ( *PhidgetBLDCMotor_OnBrakingStrengthChangeCallback)(PhidgetBLDCMotorHandle ch,
  void *ctx, double brakingStrength);
 PhidgetReturnCode PhidgetBLDCMotor_setOnBrakingStrengthChangeHandler(PhidgetBLDCMotorHandle ch,
  PhidgetBLDCMotor_OnBrakingStrengthChangeCallback fptr, void *ctx);
typedef void ( *PhidgetBLDCMotor_OnPositionChangeCallback)(PhidgetBLDCMotorHandle ch, void *ctx,
  double position);
 PhidgetReturnCode PhidgetBLDCMotor_setOnPositionChangeHandler(PhidgetBLDCMotorHandle ch,
  PhidgetBLDCMotor_OnPositionChangeCallback fptr, void *ctx);
typedef void ( *PhidgetBLDCMotor_OnVelocityUpdateCallback)(PhidgetBLDCMotorHandle ch, void *ctx,
  double velocity);
 PhidgetReturnCode PhidgetBLDCMotor_setOnVelocityUpdateHandler(PhidgetBLDCMotorHandle ch,
  PhidgetBLDCMotor_OnVelocityUpdateCallback fptr, void *ctx);
typedef struct _PhidgetDistanceSensor *PhidgetDistanceSensorHandle;
 PhidgetReturnCode PhidgetDistanceSensor_create(PhidgetDistanceSensorHandle *ch);
 PhidgetReturnCode PhidgetDistanceSensor_delete(PhidgetDistanceSensorHandle *ch);
 PhidgetReturnCode PhidgetDistanceSensor_getSonarReflections(PhidgetDistanceSensorHandle ch,
  uint32_t (*distances)[8], uint32_t (*amplitudes)[8], uint32_t *count);
 PhidgetReturnCode PhidgetDistanceSensor_setDataInterval(PhidgetDistanceSensorHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetDistanceSensor_getDataInterval(PhidgetDistanceSensorHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetDistanceSensor_getMinDataInterval(PhidgetDistanceSensorHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetDistanceSensor_getMaxDataInterval(PhidgetDistanceSensorHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetDistanceSensor_setDataRate(PhidgetDistanceSensorHandle ch, double dataRate);
 PhidgetReturnCode PhidgetDistanceSensor_getDataRate(PhidgetDistanceSensorHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetDistanceSensor_getMinDataRate(PhidgetDistanceSensorHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetDistanceSensor_getMaxDataRate(PhidgetDistanceSensorHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetDistanceSensor_getDistance(PhidgetDistanceSensorHandle ch, uint32_t *distance);
 PhidgetReturnCode PhidgetDistanceSensor_getMinDistance(PhidgetDistanceSensorHandle ch,
  uint32_t *minDistance);
 PhidgetReturnCode PhidgetDistanceSensor_getMaxDistance(PhidgetDistanceSensorHandle ch,
  uint32_t *maxDistance);
 PhidgetReturnCode PhidgetDistanceSensor_setDistanceChangeTrigger(PhidgetDistanceSensorHandle ch,
  uint32_t distanceChangeTrigger);
 PhidgetReturnCode PhidgetDistanceSensor_getDistanceChangeTrigger(PhidgetDistanceSensorHandle ch,
  uint32_t *distanceChangeTrigger);
 PhidgetReturnCode PhidgetDistanceSensor_getMinDistanceChangeTrigger(PhidgetDistanceSensorHandle ch,
  uint32_t *minDistanceChangeTrigger);
 PhidgetReturnCode PhidgetDistanceSensor_getMaxDistanceChangeTrigger(PhidgetDistanceSensorHandle ch,
  uint32_t *maxDistanceChangeTrigger);
 PhidgetReturnCode PhidgetDistanceSensor_setSonarQuietMode(PhidgetDistanceSensorHandle ch,
  int sonarQuietMode);
 PhidgetReturnCode PhidgetDistanceSensor_getSonarQuietMode(PhidgetDistanceSensorHandle ch,
  int *sonarQuietMode);
typedef void ( *PhidgetDistanceSensor_OnDistanceChangeCallback)(PhidgetDistanceSensorHandle ch,
  void *ctx, uint32_t distance);
 PhidgetReturnCode PhidgetDistanceSensor_setOnDistanceChangeHandler(PhidgetDistanceSensorHandle ch,
  PhidgetDistanceSensor_OnDistanceChangeCallback fptr, void *ctx);
typedef void ( *PhidgetDistanceSensor_OnSonarReflectionsUpdateCallback)(PhidgetDistanceSensorHandle ch, void *ctx, const uint32_t distances[8], const uint32_t amplitudes[8], uint32_t count);
 PhidgetReturnCode PhidgetDistanceSensor_setOnSonarReflectionsUpdateHandler(PhidgetDistanceSensorHandle ch,
  PhidgetDistanceSensor_OnSonarReflectionsUpdateCallback fptr, void *ctx);
typedef struct _PhidgetHumiditySensor *PhidgetHumiditySensorHandle;
 PhidgetReturnCode PhidgetHumiditySensor_create(PhidgetHumiditySensorHandle *ch);
 PhidgetReturnCode PhidgetHumiditySensor_delete(PhidgetHumiditySensorHandle *ch);
 PhidgetReturnCode PhidgetHumiditySensor_setDataInterval(PhidgetHumiditySensorHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetHumiditySensor_getDataInterval(PhidgetHumiditySensorHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetHumiditySensor_getMinDataInterval(PhidgetHumiditySensorHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetHumiditySensor_getMaxDataInterval(PhidgetHumiditySensorHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetHumiditySensor_setDataRate(PhidgetHumiditySensorHandle ch, double dataRate);
 PhidgetReturnCode PhidgetHumiditySensor_getDataRate(PhidgetHumiditySensorHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetHumiditySensor_getMinDataRate(PhidgetHumiditySensorHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetHumiditySensor_getMaxDataRate(PhidgetHumiditySensorHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetHumiditySensor_getHumidity(PhidgetHumiditySensorHandle ch, double *humidity);
 PhidgetReturnCode PhidgetHumiditySensor_getMinHumidity(PhidgetHumiditySensorHandle ch,
  double *minHumidity);
 PhidgetReturnCode PhidgetHumiditySensor_getMaxHumidity(PhidgetHumiditySensorHandle ch,
  double *maxHumidity);
 PhidgetReturnCode PhidgetHumiditySensor_setHumidityChangeTrigger(PhidgetHumiditySensorHandle ch,
  double humidityChangeTrigger);
 PhidgetReturnCode PhidgetHumiditySensor_getHumidityChangeTrigger(PhidgetHumiditySensorHandle ch,
  double *humidityChangeTrigger);
 PhidgetReturnCode PhidgetHumiditySensor_getMinHumidityChangeTrigger(PhidgetHumiditySensorHandle ch,
  double *minHumidityChangeTrigger);
 PhidgetReturnCode PhidgetHumiditySensor_getMaxHumidityChangeTrigger(PhidgetHumiditySensorHandle ch,
  double *maxHumidityChangeTrigger);
typedef void ( *PhidgetHumiditySensor_OnHumidityChangeCallback)(PhidgetHumiditySensorHandle ch,
  void *ctx, double humidity);
 PhidgetReturnCode PhidgetHumiditySensor_setOnHumidityChangeHandler(PhidgetHumiditySensorHandle ch,
  PhidgetHumiditySensor_OnHumidityChangeCallback fptr, void *ctx);
typedef struct _PhidgetLightSensor *PhidgetLightSensorHandle;
 PhidgetReturnCode PhidgetLightSensor_create(PhidgetLightSensorHandle *ch);
 PhidgetReturnCode PhidgetLightSensor_delete(PhidgetLightSensorHandle *ch);
 PhidgetReturnCode PhidgetLightSensor_setDataInterval(PhidgetLightSensorHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetLightSensor_getDataInterval(PhidgetLightSensorHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetLightSensor_getMinDataInterval(PhidgetLightSensorHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetLightSensor_getMaxDataInterval(PhidgetLightSensorHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetLightSensor_setDataRate(PhidgetLightSensorHandle ch, double dataRate);
 PhidgetReturnCode PhidgetLightSensor_getDataRate(PhidgetLightSensorHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetLightSensor_getMinDataRate(PhidgetLightSensorHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetLightSensor_getMaxDataRate(PhidgetLightSensorHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetLightSensor_getIlluminance(PhidgetLightSensorHandle ch, double *illuminance);
 PhidgetReturnCode PhidgetLightSensor_getMinIlluminance(PhidgetLightSensorHandle ch,
  double *minIlluminance);
 PhidgetReturnCode PhidgetLightSensor_getMaxIlluminance(PhidgetLightSensorHandle ch,
  double *maxIlluminance);
 PhidgetReturnCode PhidgetLightSensor_setIlluminanceChangeTrigger(PhidgetLightSensorHandle ch,
  double illuminanceChangeTrigger);
 PhidgetReturnCode PhidgetLightSensor_getIlluminanceChangeTrigger(PhidgetLightSensorHandle ch,
  double *illuminanceChangeTrigger);
 PhidgetReturnCode PhidgetLightSensor_getMinIlluminanceChangeTrigger(PhidgetLightSensorHandle ch,
  double *minIlluminanceChangeTrigger);
 PhidgetReturnCode PhidgetLightSensor_getMaxIlluminanceChangeTrigger(PhidgetLightSensorHandle ch,
  double *maxIlluminanceChangeTrigger);
typedef void ( *PhidgetLightSensor_OnIlluminanceChangeCallback)(PhidgetLightSensorHandle ch,
  void *ctx, double illuminance);
 PhidgetReturnCode PhidgetLightSensor_setOnIlluminanceChangeHandler(PhidgetLightSensorHandle ch,
  PhidgetLightSensor_OnIlluminanceChangeCallback fptr, void *ctx);
typedef struct _PhidgetPressureSensor *PhidgetPressureSensorHandle;
 PhidgetReturnCode PhidgetPressureSensor_create(PhidgetPressureSensorHandle *ch);
 PhidgetReturnCode PhidgetPressureSensor_delete(PhidgetPressureSensorHandle *ch);
 PhidgetReturnCode PhidgetPressureSensor_setDataInterval(PhidgetPressureSensorHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetPressureSensor_getDataInterval(PhidgetPressureSensorHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetPressureSensor_getMinDataInterval(PhidgetPressureSensorHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetPressureSensor_getMaxDataInterval(PhidgetPressureSensorHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetPressureSensor_setDataRate(PhidgetPressureSensorHandle ch, double dataRate);
 PhidgetReturnCode PhidgetPressureSensor_getDataRate(PhidgetPressureSensorHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetPressureSensor_getMinDataRate(PhidgetPressureSensorHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetPressureSensor_getMaxDataRate(PhidgetPressureSensorHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetPressureSensor_getPressure(PhidgetPressureSensorHandle ch, double *pressure);
 PhidgetReturnCode PhidgetPressureSensor_getMinPressure(PhidgetPressureSensorHandle ch,
  double *minPressure);
 PhidgetReturnCode PhidgetPressureSensor_getMaxPressure(PhidgetPressureSensorHandle ch,
  double *maxPressure);
 PhidgetReturnCode PhidgetPressureSensor_setPressureChangeTrigger(PhidgetPressureSensorHandle ch,
  double pressureChangeTrigger);
 PhidgetReturnCode PhidgetPressureSensor_getPressureChangeTrigger(PhidgetPressureSensorHandle ch,
  double *pressureChangeTrigger);
 PhidgetReturnCode PhidgetPressureSensor_getMinPressureChangeTrigger(PhidgetPressureSensorHandle ch,
  double *minPressureChangeTrigger);
 PhidgetReturnCode PhidgetPressureSensor_getMaxPressureChangeTrigger(PhidgetPressureSensorHandle ch,
  double *maxPressureChangeTrigger);
typedef void ( *PhidgetPressureSensor_OnPressureChangeCallback)(PhidgetPressureSensorHandle ch,
  void *ctx, double pressure);
 PhidgetReturnCode PhidgetPressureSensor_setOnPressureChangeHandler(PhidgetPressureSensorHandle ch,
  PhidgetPressureSensor_OnPressureChangeCallback fptr, void *ctx);
typedef struct _PhidgetResistanceInput *PhidgetResistanceInputHandle;
 PhidgetReturnCode PhidgetResistanceInput_create(PhidgetResistanceInputHandle *ch);
 PhidgetReturnCode PhidgetResistanceInput_delete(PhidgetResistanceInputHandle *ch);
 PhidgetReturnCode PhidgetResistanceInput_setDataInterval(PhidgetResistanceInputHandle ch,
  uint32_t dataInterval);
 PhidgetReturnCode PhidgetResistanceInput_getDataInterval(PhidgetResistanceInputHandle ch,
  uint32_t *dataInterval);
 PhidgetReturnCode PhidgetResistanceInput_getMinDataInterval(PhidgetResistanceInputHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetResistanceInput_getMaxDataInterval(PhidgetResistanceInputHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetResistanceInput_setDataRate(PhidgetResistanceInputHandle ch, double dataRate);
 PhidgetReturnCode PhidgetResistanceInput_getDataRate(PhidgetResistanceInputHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetResistanceInput_getMinDataRate(PhidgetResistanceInputHandle ch,
  double *minDataRate);
 PhidgetReturnCode PhidgetResistanceInput_getMaxDataRate(PhidgetResistanceInputHandle ch,
  double *maxDataRate);
 PhidgetReturnCode PhidgetResistanceInput_getResistance(PhidgetResistanceInputHandle ch,
  double *resistance);
 PhidgetReturnCode PhidgetResistanceInput_getMinResistance(PhidgetResistanceInputHandle ch,
  double *minResistance);
 PhidgetReturnCode PhidgetResistanceInput_getMaxResistance(PhidgetResistanceInputHandle ch,
  double *maxResistance);
 PhidgetReturnCode PhidgetResistanceInput_setResistanceChangeTrigger(PhidgetResistanceInputHandle ch,
  double resistanceChangeTrigger);
 PhidgetReturnCode PhidgetResistanceInput_getResistanceChangeTrigger(PhidgetResistanceInputHandle ch,
  double *resistanceChangeTrigger);
 PhidgetReturnCode PhidgetResistanceInput_getMinResistanceChangeTrigger(PhidgetResistanceInputHandle ch,
  double *minResistanceChangeTrigger);
 PhidgetReturnCode PhidgetResistanceInput_getMaxResistanceChangeTrigger(PhidgetResistanceInputHandle ch,
  double *maxResistanceChangeTrigger);
 PhidgetReturnCode PhidgetResistanceInput_setRTDWireSetup(PhidgetResistanceInputHandle ch,
  Phidget_RTDWireSetup RTDWireSetup);
 PhidgetReturnCode PhidgetResistanceInput_getRTDWireSetup(PhidgetResistanceInputHandle ch,
  Phidget_RTDWireSetup *RTDWireSetup);
typedef void ( *PhidgetResistanceInput_OnResistanceChangeCallback)(PhidgetResistanceInputHandle ch,
  void *ctx, double resistance);
 PhidgetReturnCode PhidgetResistanceInput_setOnResistanceChangeHandler(PhidgetResistanceInputHandle ch,
  PhidgetResistanceInput_OnResistanceChangeCallback fptr, void *ctx);
typedef struct _PhidgetPowerGuard *PhidgetPowerGuardHandle;
 PhidgetReturnCode PhidgetPowerGuard_create(PhidgetPowerGuardHandle *ch);
 PhidgetReturnCode PhidgetPowerGuard_delete(PhidgetPowerGuardHandle *ch);
 PhidgetReturnCode PhidgetPowerGuard_enableFailsafe(PhidgetPowerGuardHandle ch, uint32_t failsafeTime);
 PhidgetReturnCode PhidgetPowerGuard_resetFailsafe(PhidgetPowerGuardHandle ch);
 PhidgetReturnCode PhidgetPowerGuard_getMinFailsafeTime(PhidgetPowerGuardHandle ch,
  uint32_t *minFailsafeTime);
 PhidgetReturnCode PhidgetPowerGuard_getMaxFailsafeTime(PhidgetPowerGuardHandle ch,
  uint32_t *maxFailsafeTime);
 PhidgetReturnCode PhidgetPowerGuard_setFanMode(PhidgetPowerGuardHandle ch, Phidget_FanMode fanMode);
 PhidgetReturnCode PhidgetPowerGuard_getFanMode(PhidgetPowerGuardHandle ch, Phidget_FanMode *fanMode);
 PhidgetReturnCode PhidgetPowerGuard_setOverVoltage(PhidgetPowerGuardHandle ch, double overVoltage);
 PhidgetReturnCode PhidgetPowerGuard_getOverVoltage(PhidgetPowerGuardHandle ch, double *overVoltage);
 PhidgetReturnCode PhidgetPowerGuard_getMinOverVoltage(PhidgetPowerGuardHandle ch, double *minOverVoltage);
 PhidgetReturnCode PhidgetPowerGuard_getMaxOverVoltage(PhidgetPowerGuardHandle ch, double *maxOverVoltage);
 PhidgetReturnCode PhidgetPowerGuard_setPowerEnabled(PhidgetPowerGuardHandle ch, int powerEnabled);
 PhidgetReturnCode PhidgetPowerGuard_getPowerEnabled(PhidgetPowerGuardHandle ch, int *powerEnabled);
typedef struct _PhidgetSoundSensor *PhidgetSoundSensorHandle;
 PhidgetReturnCode PhidgetSoundSensor_create(PhidgetSoundSensorHandle *ch);
 PhidgetReturnCode PhidgetSoundSensor_delete(PhidgetSoundSensorHandle *ch);
 PhidgetReturnCode PhidgetSoundSensor_setDataInterval(PhidgetSoundSensorHandle ch, uint32_t dataInterval);
 PhidgetReturnCode PhidgetSoundSensor_getDataInterval(PhidgetSoundSensorHandle ch, uint32_t *dataInterval);
 PhidgetReturnCode PhidgetSoundSensor_getMinDataInterval(PhidgetSoundSensorHandle ch,
  uint32_t *minDataInterval);
 PhidgetReturnCode PhidgetSoundSensor_getMaxDataInterval(PhidgetSoundSensorHandle ch,
  uint32_t *maxDataInterval);
 PhidgetReturnCode PhidgetSoundSensor_setDataRate(PhidgetSoundSensorHandle ch, double dataRate);
 PhidgetReturnCode PhidgetSoundSensor_getDataRate(PhidgetSoundSensorHandle ch, double *dataRate);
 PhidgetReturnCode PhidgetSoundSensor_getMinDataRate(PhidgetSoundSensorHandle ch, double *minDataRate);
 PhidgetReturnCode PhidgetSoundSensor_getMaxDataRate(PhidgetSoundSensorHandle ch, double *maxDataRate);
 PhidgetReturnCode PhidgetSoundSensor_getdB(PhidgetSoundSensorHandle ch, double *dB);
 PhidgetReturnCode PhidgetSoundSensor_getMaxdB(PhidgetSoundSensorHandle ch, double *maxdB);
 PhidgetReturnCode PhidgetSoundSensor_getdBA(PhidgetSoundSensorHandle ch, double *dBA);
 PhidgetReturnCode PhidgetSoundSensor_getdBC(PhidgetSoundSensorHandle ch, double *dBC);
 PhidgetReturnCode PhidgetSoundSensor_getNoiseFloor(PhidgetSoundSensorHandle ch, double *noiseFloor);
 PhidgetReturnCode PhidgetSoundSensor_getOctaves(PhidgetSoundSensorHandle ch, double (*octaves)[10]);
 PhidgetReturnCode PhidgetSoundSensor_setSPLChangeTrigger(PhidgetSoundSensorHandle ch,
  double SPLChangeTrigger);
 PhidgetReturnCode PhidgetSoundSensor_getSPLChangeTrigger(PhidgetSoundSensorHandle ch,
  double *SPLChangeTrigger);
 PhidgetReturnCode PhidgetSoundSensor_getMinSPLChangeTrigger(PhidgetSoundSensorHandle ch,
  double *minSPLChangeTrigger);
 PhidgetReturnCode PhidgetSoundSensor_getMaxSPLChangeTrigger(PhidgetSoundSensorHandle ch,
  double *maxSPLChangeTrigger);
 PhidgetReturnCode PhidgetSoundSensor_setSPLRange(PhidgetSoundSensorHandle ch,
  PhidgetSoundSensor_SPLRange SPLRange);
 PhidgetReturnCode PhidgetSoundSensor_getSPLRange(PhidgetSoundSensorHandle ch,
  PhidgetSoundSensor_SPLRange *SPLRange);
typedef void ( *PhidgetSoundSensor_OnSPLChangeCallback)(PhidgetSoundSensorHandle ch, void *ctx,
  double dB, double dBA, double dBC, const double octaves[10]);
 PhidgetReturnCode PhidgetSoundSensor_setOnSPLChangeHandler(PhidgetSoundSensorHandle ch,
  PhidgetSoundSensor_OnSPLChangeCallback fptr, void *ctx);
typedef struct _PhidgetHub *PhidgetHubHandle;
 PhidgetReturnCode PhidgetHub_create(PhidgetHubHandle *ch);
 PhidgetReturnCode PhidgetHub_delete(PhidgetHubHandle *ch);
 PhidgetReturnCode PhidgetHub_setPortAutoSetSpeed(PhidgetHubHandle ch, int port, int state);
 PhidgetReturnCode PhidgetHub_getPortMaxSpeed(PhidgetHubHandle ch, int port, uint32_t *state);
 PhidgetReturnCode PhidgetHub_getPortMode(PhidgetHubHandle ch, int port, PhidgetHub_PortMode *mode);
 PhidgetReturnCode PhidgetHub_setPortMode(PhidgetHubHandle ch, int port, PhidgetHub_PortMode mode);
 PhidgetReturnCode PhidgetHub_getPortPower(PhidgetHubHandle ch, int port, int *state);
 PhidgetReturnCode PhidgetHub_setPortPower(PhidgetHubHandle ch, int port, int state);
 PhidgetReturnCode PhidgetHub_getPortSupportsAutoSetSpeed(PhidgetHubHandle ch, int port, int *state);
 PhidgetReturnCode PhidgetHub_getPortSupportsSetSpeed(PhidgetHubHandle ch, int port, int *state);
typedef struct _PhidgetDictionary *PhidgetDictionaryHandle;
 PhidgetReturnCode PhidgetDictionary_create(PhidgetDictionaryHandle *ch);
 PhidgetReturnCode PhidgetDictionary_delete(PhidgetDictionaryHandle *ch);
 PhidgetReturnCode PhidgetDictionary_add(PhidgetDictionaryHandle ch, const char *key, const char *value);
 PhidgetReturnCode PhidgetDictionary_removeAll(PhidgetDictionaryHandle ch);
 PhidgetReturnCode PhidgetDictionary_get(PhidgetDictionaryHandle ch, const char *key, char *value,
  size_t valueLen);
 PhidgetReturnCode PhidgetDictionary_remove(PhidgetDictionaryHandle ch, const char *key);
 PhidgetReturnCode PhidgetDictionary_scan(PhidgetDictionaryHandle ch, const char *start, char *keyList,
  size_t keyListLen);
 PhidgetReturnCode PhidgetDictionary_set(PhidgetDictionaryHandle ch, const char *key, const char *value);
 PhidgetReturnCode PhidgetDictionary_update(PhidgetDictionaryHandle ch, const char *key,
  const char *value);
typedef void ( *PhidgetDictionary_OnAddCallback)(PhidgetDictionaryHandle ch, void *ctx,
  const char *key, const char *value);
 PhidgetReturnCode PhidgetDictionary_setOnAddHandler(PhidgetDictionaryHandle ch,
  PhidgetDictionary_OnAddCallback fptr, void *ctx);
typedef void ( *PhidgetDictionary_OnRemoveCallback)(PhidgetDictionaryHandle ch, void *ctx,
  const char *key);
 PhidgetReturnCode PhidgetDictionary_setOnRemoveHandler(PhidgetDictionaryHandle ch,
  PhidgetDictionary_OnRemoveCallback fptr, void *ctx);
typedef void ( *PhidgetDictionary_OnUpdateCallback)(PhidgetDictionaryHandle ch, void *ctx,
  const char *key, const char *value);
 PhidgetReturnCode PhidgetDictionary_setOnUpdateHandler(PhidgetDictionaryHandle ch,
  PhidgetDictionary_OnUpdateCallback fptr, void *ctx);
#ifdef __cplusplus
}
#endif

#endif
