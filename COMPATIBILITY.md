# Version Compatibility Guide

## Why Compatibility Matters

The pyannote diarization models work best with compatible versions of PyTorch, Pyannote Audio, and PyTorch Lightning. Using incompatible versions can lead to:

- ⚠️ Warning messages during processing
- 🔽 Reduced diarization quality
- ❌ Potential model loading failures
- 🐛 Unexpected behavior

## Current Issues

If you see warnings like:
```
Model was trained with pyannote.audio 0.0.1, yours is 3.3.2. Bad things might happen unless you revert pyannote.audio to 0.x.
Model was trained with torch 1.10.0+cu102, yours is 2.7.1. Bad things might happen unless you revert torch to 1.x.
```

This indicates version incompatibility that may affect diarization quality.

## Quick Fix

Run the compatibility setup script:

```bash
python setup_compatible_env.py
```

This will:
1. ✅ Check your current versions
2. ✅ Use uv sync to install compatible versions
3. ✅ Create a backup of your current setup
4. ✅ Verify the installation

## Manual Fix

If you prefer to fix manually:

```bash
# Check current versions
python fix_compatibility.py check

# Sync dependencies with uv
uv sync

# Restore original versions (if needed)
python fix_compatibility.py restore
```

## Compatible Versions

For optimal diarization quality, use these version ranges:

| Package | Compatible Range | Notes |
|---------|------------------|-------|
| PyTorch | 2.0.0 - 3.0.0 | Modern stable versions |
| TorchAudio | 2.0.0 - 3.0.0 | Must match PyTorch version |
| Pyannote Audio | 3.0.0 - 4.0.0 | Latest stable for diarization |
| PyTorch Lightning | 2.0.0 - 3.0.0 | Compatible with modern models |

## Using uv for Dependency Management

This project uses `uv` for dependency management. Always use:

```bash
# Install dependencies
uv sync

# Run scripts
uv run transcribe_advanced.py

# Add new dependencies
uv add package-name
```

## Alternative Solutions

### Option 1: Use Compatible Models
If you can't change versions, try these models in order:
1. `pyannote/speaker-diarization-3.1` (latest, most compatible)
2. `pyannote/speaker-diarization-2.1` (fallback option)
3. `pyannote/speaker-diarization` (original version)

### Option 2: Continue with Warnings
The models often work despite warnings, but quality may be reduced.

## Verification

After fixing compatibility, run:

```bash
uv run transcribe_advanced.py --test-env
```

You should see:
- ✅ No version compatibility warnings
- ✅ All packages at compatible versions
- ✅ Optimal diarization quality

## Troubleshooting

### Dependency Resolution Fails
- Try: `uv sync --reinstall`
- Check: `uv pip list` to see installed versions
- Restore: `python fix_compatibility.py restore`

### Still Getting Warnings
- Restart your Python environment
- Check if you're using the right virtual environment
- Verify package versions: `python fix_compatibility.py check`

### Performance Issues
- Modern versions may be faster and more accurate
- Consider using smaller models if speed is critical
- Monitor memory usage during processing

## Backup and Restore

The setup creates `package_versions_backup.json` with your original versions.

To restore:
```bash
python fix_compatibility.py restore
```

## Support

If you continue having issues:
1. Check the backup file for your original versions
2. Try the alternative model options
3. Consider using the simple transcription script instead
4. Use `uv run` instead of direct python execution 