# Experiment artifacts

This directory contains research evidence and reproducibility bundles. It is
not installed in the `autocedar` Python package.

Committed experiment runs should be intentional and reviewable:

- include a short README or summary stating the question, configuration, and
  result;
- include a manifest when a run contains many generated workspaces;
- retain inputs and the smallest set of outputs needed to reproduce a reported
  claim;
- do not commit credentials, model caches, virtual environments, temporary
  files, or uncurated local smoke runs.

Normal AutoCedar session output belongs in `autocedar-runs/` or `eval_runs/`,
both of which are gitignored. Large public datasets should use a GitHub release
or dedicated data repository when they no longer benefit from line-by-line
code review.
