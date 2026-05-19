#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>

typedef struct {
    char timestamp[32];
    char level[10];
    char message[256];
} LogEntry;

void parse_line(char *line) {
    LogEntry entry;
    char date[16];
    char time[16];

    int parsed = sscanf(line, "%s %s %s %[^\n]",
                        date, time, entry.level, entry.message);

    if (parsed == 4) {
        snprintf(entry.timestamp, sizeof(entry.timestamp), "%s %s", date, time);
        printf("TIMESTAMP: %s | LEVEL: %s | MESSAGE: %s\n",
               entry.timestamp, entry.level, entry.message);
    }
}

int main() {
    int fd = open("test.log", O_RDONLY);
    if (fd == -1) {
        perror("open failed");
        return 1;
    }

    lseek(fd, 0, SEEK_END);
    printf("Watching test.log...\n");

    char buffer[4096];

    while (1) {
        int bytes_read = read(fd, buffer, sizeof(buffer));

        if (bytes_read > 0) {
            buffer[bytes_read] = '\0';
            char *line = strtok(buffer, "\n");
            while (line != NULL) {
                parse_line(line);
                line = strtok(NULL, "\n");
            }
        } else {
            sleep(1);
        }
    }

    return 0;
}