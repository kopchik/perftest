#pragma once
#include <stdio.h>
#include <errno.h>
#include <string.h>

/* thanks to http://www.decompile.com/cpp/faq/file_and_line_error_string.htm */
#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)
#define _FILEPOS_ "["__FILE__":"TOSTRING(__LINE__)"] "


/* in Russia we believe that assert is unreliable as it depends on NDEBUG */
#define myassert(expr, ...) \
    if (!(expr)) { fprintf(stderr, _FILEPOS_ __VA_ARGS__); \
                   fprintf(stderr, "\n"); \
                   abort(); }

/* another version of assert which prints errno */
#define myassert2(expr, msg) { \
    if (!(expr)) { \
        fprintf(stderr, _FILEPOS_"%s: %s\n", \
            msg, strerror(errno)); \
        abort(); }}

