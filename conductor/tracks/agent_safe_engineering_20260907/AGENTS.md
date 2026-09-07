# Scope for this engineering programme

Before changing any implementation file for this track, read worker-guide.md,
spec.md and the selected packet in packets.json. Every implementation slice needs
an exact file allowlist, baseline hashes, acceptance witness and satisfied
prerequisite evidence. candidate_write_scope is not a final write allowlist.

All implementation_ready flags start false. Do not set one true solely because
the packet parses or its plan exists. Until G01 lands, the integrator explicitly
checks readiness. G01 itself needs the reviewed negative-test design in G01.1.

Do not edit another track, overwrite evidence, relax quality gates, or infer
scientific and release decisions. Follow worker-guide.md for escalation and
parallel ownership. Planning completion is not implementation completion.

## Repository admission

Read [repository-boundaries.md](./repository-boundaries.md) before any scope
refinement. One slice has one delivery repository. Generic inference, game
solving, simulation, source acquisition and shared automation stay with their
owners. Future Rust-first providers may have distinct APIs/ABIs; validate the
chosen scientific and interchange contract. Existing Voiage compatibility
promises remain in force. Do not edit a sibling repository from this track.
