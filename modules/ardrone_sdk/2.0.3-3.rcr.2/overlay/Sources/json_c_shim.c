/*
 * Copyright 2026 Open Source Robotics Foundation, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "json-c/json.h"

struct json_kv {
    char *key;
    struct json_object *val;
    struct json_kv *next;
};

struct json_object {
    enum json_type type;
    int refcount;
    int32_t int_val;
    char *str_val;
    struct json_kv *fields;
    char *json_str_buf;
};

struct json_object *json_object_get(struct json_object *obj) {
    if (obj != NULL) {
        obj->refcount++;
    }
    return obj;
}

int json_object_put(struct json_object *obj) {
    if (obj == NULL) {
        return 0;
    }
    obj->refcount--;
    if (obj->refcount > 0) {
        return 0;
    }
    struct json_kv *kv = obj->fields;
    while (kv != NULL) {
        struct json_kv *next = kv->next;
        free(kv->key);
        json_object_put(kv->val);
        free(kv);
        kv = next;
    }
    free(obj->str_val);
    free(obj->json_str_buf);
    free(obj);
    return 1;
}

struct json_object *json_object_new_object(void) {
    struct json_object *obj = (struct json_object *)calloc(1, sizeof(struct json_object));
    if (obj != NULL) {
        obj->type = json_type_object;
        obj->refcount = 1;
    }
    return obj;
}

struct json_object *json_object_new_int(int32_t i) {
    struct json_object *obj = (struct json_object *)calloc(1, sizeof(struct json_object));
    if (obj != NULL) {
        obj->type = json_type_int;
        obj->refcount = 1;
        obj->int_val = i;
    }
    return obj;
}

int32_t json_object_get_int(struct json_object *obj) {
    if (obj == NULL) {
        return 0;
    }
    if (obj->type == json_type_int || obj->type == json_type_boolean) {
        return obj->int_val;
    }
    if (obj->type == json_type_string && obj->str_val != NULL) {
        return (int32_t)strtol(obj->str_val, NULL, 10);
    }
    return 0;
}

struct json_object *json_object_new_string(const char *s) {
    struct json_object *obj = (struct json_object *)calloc(1, sizeof(struct json_object));
    if (obj != NULL) {
        obj->type = json_type_string;
        obj->refcount = 1;
        if (s != NULL) {
            obj->str_val = strdup(s);
        }
    }
    return obj;
}

const char *json_object_get_string(struct json_object *obj) {
    if (obj == NULL) {
        return NULL;
    }
    if (obj->type == json_type_string) {
        return obj->str_val ? obj->str_val : "";
    }
    return json_object_to_json_string(obj);
}

void json_object_object_add(struct json_object *obj, const char *key, struct json_object *val) {
    if (obj == NULL || obj->type != json_type_object || key == NULL) {
        return;
    }
    struct json_kv *kv = obj->fields;
    struct json_kv *last = NULL;
    while (kv != NULL) {
        if (strcmp(kv->key, key) == 0) {
            json_object_put(kv->val);
            kv->val = val;
            return;
        }
        last = kv;
        kv = kv->next;
    }
    struct json_kv *new_kv = (struct json_kv *)calloc(1, sizeof(struct json_kv));
    if (new_kv == NULL) {
        return;
    }
    new_kv->key = strdup(key);
    new_kv->val = val;
    if (last != NULL) {
        last->next = new_kv;
    } else {
        obj->fields = new_kv;
    }
}

json_bool json_object_object_get_ex(struct json_object *obj, const char *key, struct json_object **value) {
    if (value != NULL) {
        *value = NULL;
    }
    if (obj == NULL || obj->type != json_type_object || key == NULL) {
        return FALSE;
    }
    struct json_kv *kv = obj->fields;
    while (kv != NULL) {
        if (strcmp(kv->key, key) == 0) {
            if (value != NULL) {
                *value = kv->val;
            }
            return TRUE;
        }
        kv = kv->next;
    }
    return FALSE;
}

const char *json_object_to_json_string(struct json_object *obj) {
    if (obj == NULL) {
        return "null";
    }
    free(obj->json_str_buf);
    obj->json_str_buf = NULL;

    if (obj->type == json_type_int) {
        obj->json_str_buf = (char *)malloc(32);
        if (obj->json_str_buf != NULL) {
            snprintf(obj->json_str_buf, 32, "%d", (int)obj->int_val);
        }
        return obj->json_str_buf ? obj->json_str_buf : "0";
    }
    if (obj->type == json_type_string) {
        const char *s = obj->str_val ? obj->str_val : "";
        size_t len = strlen(s) + 3;
        obj->json_str_buf = (char *)malloc(len);
        if (obj->json_str_buf != NULL) {
            snprintf(obj->json_str_buf, len, "\"%s\"", s);
        }
        return obj->json_str_buf ? obj->json_str_buf : "\"\"";
    }
    if (obj->type == json_type_object) {
        size_t cap = 256;
        size_t used = 0;
        char *buf = (char *)malloc(cap);
        if (buf == NULL) {
            return "{}";
        }
        buf[used++] = '{';
        struct json_kv *kv = obj->fields;
        int first = 1;
        while (kv != NULL) {
            const char *val_str = json_object_to_json_string(kv->val);
            size_t need = strlen(kv->key) + strlen(val_str) + 8;
            if (used + need >= cap) {
                cap = (cap + need) * 2;
                char *new_buf = (char *)realloc(buf, cap);
                if (new_buf == NULL) {
                    free(buf);
                    return "{}";
                }
                buf = new_buf;
            }
            if (!first) {
                buf[used++] = ',';
            }
            first = 0;
            used += (size_t)snprintf(buf + used, cap - used, "\"%s\":%s", kv->key, val_str);
            kv = kv->next;
        }
        buf[used++] = '}';
        buf[used] = '\0';
        obj->json_str_buf = buf;
        return obj->json_str_buf;
    }
    return "null";
}

static void skip_ws(const char **p) {
    while (**p != '\0' && isspace((unsigned char)**p)) {
        (*p)++;
    }
}

static char *parse_json_string_raw(const char **p) {
    skip_ws(p);
    if (**p != '"') {
        return NULL;
    }
    (*p)++;
    const char *start = *p;
    while (**p != '\0' && **p != '"') {
        if (**p == '\\' && *(*p + 1) != '\0') {
            (*p)++;
        }
        (*p)++;
    }
    size_t len = (size_t)(*p - start);
    char *s = (char *)malloc(len + 1);
    if (s != NULL) {
        memcpy(s, start, len);
        s[len] = '\0';
    }
    if (**p == '"') {
        (*p)++;
    }
    return s;
}

static struct json_object *parse_json_value(const char **p);

static struct json_object *parse_json_object(const char **p) {
    skip_ws(p);
    if (**p != '{') {
        return NULL;
    }
    (*p)++;
    struct json_object *obj = json_object_new_object();
    if (obj == NULL) {
        return NULL;
    }
    skip_ws(p);
    if (**p == '}') {
        (*p)++;
        return obj;
    }
    while (**p != '\0') {
        char *key = parse_json_string_raw(p);
        if (key == NULL) {
            break;
        }
        skip_ws(p);
        if (**p == ':') {
            (*p)++;
        }
        struct json_object *val = parse_json_value(p);
        json_object_object_add(obj, key, val);
        free(key);
        skip_ws(p);
        if (**p == ',') {
            (*p)++;
            continue;
        }
        if (**p == '}') {
            (*p)++;
            break;
        }
        break;
    }
    return obj;
}

static struct json_object *parse_json_value(const char **p) {
    skip_ws(p);
    if (**p == '{') {
        return parse_json_object(p);
    }
    if (**p == '"') {
        char *s = parse_json_string_raw(p);
        struct json_object *obj = json_object_new_string(s ? s : "");
        free(s);
        return obj;
    }
    if (**p == '-' || isdigit((unsigned char)**p)) {
        char *end = NULL;
        long v = strtol(*p, &end, 10);
        *p = end;
        return json_object_new_int((int32_t)v);
    }
    if (strncmp(*p, "true", 4) == 0) {
        *p += 4;
        return json_object_new_int(1);
    }
    if (strncmp(*p, "false", 5) == 0) {
        *p += 5;
        return json_object_new_int(0);
    }
    if (strncmp(*p, "null", 4) == 0) {
        *p += 4;
        return NULL;
    }
    return NULL;
}

struct json_object *json_tokener_parse(const char *str) {
    if (str == NULL) {
        return NULL;
    }
    const char *p = str;
    return parse_json_value(&p);
}
