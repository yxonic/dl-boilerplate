# DL Boilerplate

This project provides a good starting point for all kinds of experiments that have concerns in reproducibility. It frees myself from coding for features like configure/save/load a model, resume a training process, testing on each snapshots, tracking progress, logging, etc.

The template doesn't rely on any third-party packages except for [toml](https://github.com/toml-lang/toml), which provides powerful yet human-readable configuration facilities.

## Design

There main design idea behind this template is the **workspace** concept.

Model configurations are saved as `config.toml` file inside each workspace, by the `config` command. After that, we can run `train` or `test` command, which loads the configuration in that workspace, builds the model or trainer accordingly if needed, and resume training / reproduce testing results.

## TODO
- [x] Tests with full coverage
- [ ] Workspace utilities
- [ ] More example scenarios
- [ ] Tutorials and full documentation
