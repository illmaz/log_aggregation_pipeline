#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

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
        write(1, buffer, bytes_read);
    } else {
        sleep(1);
    }
}
    return 0;
}