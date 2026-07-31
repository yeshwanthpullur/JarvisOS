# CLI Guide

The interactive `Jarvis >` prompt is the current primary JARVIS experience. It is backed by the Conversation and Command engines; ordinary messages use Executive JARVIS and Provider Router, while registered commands remain on the command path.

Start with `python main.py`. Use `help` for the focused command guide and `project status` for the current release, MVP readiness, and next milestone. Common operating commands include `local only on/off`, `local use <model>`, `provider status`, `tools status`, `voice status`, `voice output on/off`, `voice say <text>`, and `exit`.

Vision commands are `vision status`, `vision describe <image_path>`, and `vision ask <image_path> <question>`. Quote paths containing spaces. Image metadata is available after validation; semantic descriptions require a genuinely vision-capable configured model.
