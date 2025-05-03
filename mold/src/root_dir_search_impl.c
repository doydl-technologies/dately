#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include "root_dir_search.h"

// Windows implementation of basename
char* basename(char *path) {
    char *base = strrchr(path, '\\');
    return base ? base + 1 : path;
}

// Windows implementation of dirname
char* dirname(char *path) {
    static char buffer[MAX_PATH];
    strncpy(buffer, path, MAX_PATH);
    char *last_backslash = strrchr(buffer, '\\');
    if (last_backslash != NULL) {
        *last_backslash = '\0';
    } else {
        buffer[0] = '.';
        buffer[1] = '\0';
    }
    return buffer;
}

char* find_directory(const char *start_path, const char *dir_name) {
    char current_path[MAX_PATH];
    char *parent_path = NULL;
    char *directory_path = NULL;

    strncpy(current_path, start_path, MAX_PATH);
    current_path[MAX_PATH - 1] = '\0';

    while (1) {
        char *base_name = basename(current_path);
        if (strcmp(base_name, dir_name) == 0) {
            directory_path = _strdup(current_path);
            break;
        }

        parent_path = dirname(current_path);
        if (strcmp(current_path, parent_path) == 0) {
            // Reached the root directory
            break;
        }

        strncpy(current_path, parent_path, MAX_PATH);
        current_path[MAX_PATH - 1] = '\0';
    }

    return directory_path;
}