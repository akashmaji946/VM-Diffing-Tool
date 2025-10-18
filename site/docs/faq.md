# FAQ

## Why do I see `Python.h not found`?
Install `python3-dev` (or distro equivalent) and rebuild the backend.

## Can I run without KVM?
libguestfs performs best with KVM. In Docker, run with `--privileged` and expose `/dev/kvm`.

## Where are exports saved?
Downloads are triggered in the browser with sensible filenames, e.g. `block_<N>_<FORMAT>.json|pdf`.
