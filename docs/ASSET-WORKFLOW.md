# Asset Workflow

This is a generic workflow only; the exact WrestleMania XIX file formats still need to be identified from the owner's local files.

## Before analysis

1. Make a separate backup of the files you plan to inspect.
2. Record the game/platform/version.
3. Generate a listing with relative path, file size, and SHA-256.
4. Do not upload a full game image or dump to GitHub.

## Investigation order

1. List files and inspect file signatures.
2. Group by extension, size, and repeated naming patterns.
3. Identify archive/container boundaries and likely compression.
4. Inspect small samples with read-only tools.
5. Record confirmed observations and the sample hashes used.
6. Only then design an extractor or editor.

## Change tracking

For every changed file, record:

- Original relative path and SHA-256
- Tool and version
- Operation performed
- Output path and SHA-256
- Test result and rollback instructions

## Safety rails

- Never overwrite the only original.
- Never run an unverified repacker against the only copy.
- Avoid committing extracted proprietary art, audio, video, executable files, or complete game data.
- Use original or authorized assets for public examples.
