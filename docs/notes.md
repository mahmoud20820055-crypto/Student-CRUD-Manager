# Technical Notes

## 1. Biggest Docker problem and how I solved it

**Problem: `pip install` failed inside `docker build` with an SSL error, even though it worked on the host.**

```
SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: self-signed certificate in certificate chain'))
ERROR: No matching distribution found for Flask==3.0.3
```

**Cause:** the build machine reached the internet through a TLS-intercepting proxy, which re-signs
HTTPS traffic with its own certificate authority (CA). The host trusted that CA, but the fresh
`python:3.12-slim` container did not. So pip inside the build rejected PyPI's certificate.

**Bad fixes I rejected:**
- `pip install --trusted-host pypi.org ...` turns off certificate checks. That is insecure.
- `COPY ca.crt` into the image bakes a machine-specific file into every layer and every user's image.

**Solution: an optional BuildKit secret mount.**

```dockerfile
RUN --mount=type=secret,id=pip_ca,required=false \
    if [ -f /run/secrets/pip_ca ]; then export PIP_CERT=/run/secrets/pip_ca; fi; \
    pip install -r requirements.txt
```

- On a normal machine, `docker build .` works unchanged. The secret is optional (`required=false`).
- Behind a proxy: `docker build --secret id=pip_ca,src=/path/ca.crt .` (or `make build PIP_CA=...`).
- The CA file is mounted only while that single `RUN` step executes. It is never written to an image layer.

**Smaller issues along the way:**
- *Docker Hub rate limit (HTTP 429)* when pulling the base image. I pulled the same official image
  from the `mirror.gcr.io` mirror and tagged it locally as `python:3.12-slim`.
- *Environment variables in `CMD`:* exec-form `CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}"]` does not
  expand `${PORT}`. I used `sh -c "exec gunicorn ... ${PORT}"`. `exec` keeps gunicorn as PID 1,
  so `docker stop` (SIGTERM) shuts it down cleanly.
- *SQLite permissions as non-root:* the `app` user could not create the database file until
  `/app/data` was created and `chown`ed before switching `USER`.
- *Healthcheck without curl:* the slim image has no `curl`. The `HEALTHCHECK` uses Python's built-in `urllib`
  instead of installing extra packages.

## 2. Most important Git/GitHub lesson

**Commit small, meaningful steps, and let the history tell the story.**

Each commit has one purpose and a conventional prefix (`feat:`, `test:`, `chore:`, `docker:`,
`ci:`, `docs:`). Anyone can read `git log --oneline` and see how the project was built:
structure → application → tests → Docker → Compose/Make → CI → documentation.
This also made problems easier to isolate. When the Docker build failed, I knew the app and tests
(already committed and passing) were not the cause.

Related lessons:
- **`.gitignore` first.** Adding it in the first commit kept `__pycache__/`, virtualenvs and the
  local SQLite database out of history. Removing a committed file later does not remove it from history.
- **Feature branch + Pull Request.** Work is done on a feature branch and goes into `main`
  through a Pull Request. CI runs on the PR, so broken code is caught before it reaches `main`.
- **`.gitignore` ≠ `.dockerignore`.** Git and Docker use separate ignore files. Tests are committed to
  Git but excluded from the build context of the runtime image.
