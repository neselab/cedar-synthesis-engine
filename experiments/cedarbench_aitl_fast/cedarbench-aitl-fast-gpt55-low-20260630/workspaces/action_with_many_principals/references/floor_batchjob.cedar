// Floor: any BatchJob MUST be permitted to invoke (BatchJobs are
// pre-vetted by the orchestrator and have no per-request gate here).
permit (principal is BatchJob, action == Action::"invoke", resource is Resource);
