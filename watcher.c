#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>

typedef struct {
    char timestamp[32];
    char level[10];
    char message[256];
} LogEntry;

void escape_json(const char *input, char *output, int output_size) {
    int j = 0;
    for (int i = 0; input[i] != '\0' && j < output_size - 2; i++) {
        if (input[i] == '"' || input[i] == '\\') {
            output[j++] = '\\';
        }
        output[j++] = input[i];
    }
    output[j] = '\0';
}

void parse_line(char *line) {
    LogEntry entry;
    char date[16];
    char time[16];
    char output[512];

    int parsed = sscanf(line, "%15s %15s %9s %255[^\n]",
                        date, time, entry.level, entry.message);

    if (parsed == 4) {
        snprintf(entry.timestamp, sizeof(entry.timestamp), "%s %s", date, time);
        char escaped_message[512];
        escape_json(entry.message, escaped_message, sizeof(escaped_message));
        snprintf(output, sizeof(output),
        "{\"timestamp\": \"%s\", \"level\": \"%s\", \"message\": \"%s\"}\n",
        entry.timestamp, entry.level, escaped_message);
        if (write(1, output, strlen(output)) == -1) {
            fprintf(stderr, "write failed, exiting\n");
            exit(1);
        }
    }
}

int main() {
    int fd = open("test.log", O_RDONLY);
    if (fd == -1) {
        perror("open failed");
        return 1;
    }

    lseek(fd, 0, SEEK_END);
    fprintf(stderr, "Watching test.log...\n");

    char buffer[4096];
    char line_buf[4096];
    int line_len = 0;

    while (1) {
        ssize_t bytes_read = read(fd, buffer, sizeof(buffer) - 1);

        if (bytes_read > 0) {
            for (int i = 0; i < bytes_read; i++) {
                if (buffer[i] == '\n') {
                    line_buf[line_len] = '\0';
                    parse_line(line_buf);
                    line_len = 0;
                } else {
                    if (line_len < (int)sizeof(line_buf) - 1) {
                        line_buf[line_len++] = buffer[i];
                    }
                }
            }
        } else {
            sleep(1);
        }
    }

    return 0;
}