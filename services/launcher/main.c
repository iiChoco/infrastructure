/* The launcher: an application bundle that starts Ciel and stays.
 *
 * macOS attributes microphone access to the *responsible* process — the
 * application that launched the one asking — and only an application whose
 * Info.plist carries NSMicrophoneUsageDescription is ever asked. Python's
 * own bundle carries none, so a spoke started by launchd as python directly
 * is denied without a prompt, and a `/bin/sh -c 'exec python'` wrapper is
 * an Apple platform binary that is never asked either. This bundle is the
 * application: it spawns Python as a child (never exec, which would replace
 * the code identity), forwards the signals launchd sends, and exits with the
 * child's status so KeepAlive restarts the pair together. The child's own
 * re-exec on a source change keeps the same pid and the same parent, so the
 * permission survives every reload.
 */
#include <errno.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;
static pid_t child = 0;

static void forward(int sig) {
    if (child > 0) kill(child, sig);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: ciel-launcher program [args...]\n");
        return 64;
    }
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = forward;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    int rc = posix_spawn(&child, argv[1], NULL, NULL, argv + 1, environ);
    if (rc != 0) {
        fprintf(stderr, "ciel-launcher: cannot start %s: %s\n", argv[1], strerror(rc));
        return 127;
    }
    int status;
    while (waitpid(child, &status, 0) < 0) {
        if (errno != EINTR) return 1;
    }
    if (WIFEXITED(status)) return WEXITSTATUS(status);
    if (WIFSIGNALED(status)) return 128 + WTERMSIG(status);
    return 1;
}
