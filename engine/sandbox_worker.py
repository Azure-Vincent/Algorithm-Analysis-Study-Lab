"""Child-process entry point for engine.sandbox: JSON in on stdin, JSON result out on stdout."""
import json
import sys

from engine.pseudo import run_tests


CPU_SECONDS = 5
MEMORY_BYTES = 512 * 1024 * 1024


def apply_limits():
    """Cap CPU time, memory, file writes and child processes (POSIX only)."""
    try:
        import resource
    except ImportError:          # Windows: the parent's wall-clock timeout still applies
        return
    for limit, value in ((resource.RLIMIT_CPU, CPU_SECONDS), (resource.RLIMIT_AS, MEMORY_BYTES),
                         (resource.RLIMIT_FSIZE, 0), (getattr(resource, "RLIMIT_NPROC", None), 0)):
        if limit is None:
            continue
        try:
            resource.setrlimit(limit, (value, value))
        except (ValueError, OSError):
            pass


def main():
    apply_limits()
    job = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    result = run_tests(job["src"], job["tests"], job.get("entry"), job.get("params"), bool(job.get("one_indexed")))
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
