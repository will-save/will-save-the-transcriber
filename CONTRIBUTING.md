# Contributing to Will Save the Transcriber

Thank you for your interest in contributing to this project! We're committed to making Will Save the Podcast content accessible to everyone and providing tools for others to transcribe their own content.

## Table of Contents
- [Types of Contributions](#types-of-contributions)
- [Transcription Corrections](#transcription-corrections)
- [Development Contributions](#development-contributions)
- [Getting Started](#getting-started)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Types of Contributions

We welcome contributions in two main areas:

### 1. Transcription Corrections
Help improve the accuracy of transcribed episodes by correcting:
- Speaker attribution errors
- Mistranslations
- Punctuation and formatting
- Character and place names
- Starfinder/Pathfinder terminology

### 2. Development Contributions
Help improve the transcription scripts by:
- Enhancing diarization accuracy
- Adding Starfinder vocabulary dictionaries
- Optimizing performance
- Adding new features
- Fixing bugs

## Transcription Corrections

### How to Submit Corrections

1. **Find the Episode**: Locate the episode file in the `episodes/` directory
   - Files are organized by series: `episodes/[series_name]/[episode_title].md`
   - Example: `episodes/threefold_conspiracy_book_1/episode_1_title.md`

2. **Create an Issue**: Use the [Transcription Correction template](.github/ISSUE_TEMPLATE/transcription_correction.md)
   - Provide the exact file path
   - Include current and corrected text
   - Specify the type of correction needed

3. **Submit a Pull Request**: 
   - Fork the repository
   - Make your corrections
   - Use the proper commit message format (see below)
   - Submit a PR with a clear description

### Commit Message Format

For transcription corrections, use this format:
```
[type]: [description of changes]
```

**Types:**
- `speaker`: Speaker attribution corrections
- `mistranslation`: Incorrect word/phrase corrections
- `punctuation`: Punctuation and formatting fixes
- `character`: Character or place name corrections
- `terminology`: Starfinder/Pathfinder term corrections
- `formatting`: Markdown formatting issues

**Examples:**
```
speaker: fixed speaker attribution for Will in episode 15
mistranslation: corrected "app" to "ep" (short for episode)
speaker/mistranslation: changed Speaker_0 to Will and fixed "star finder" to "Starfinder"
punctuation: added missing commas and periods
character: corrected "Keskodai" to "Keskodai" throughout episode
terminology: updated "solarian" to "Solarian" class references
```

### File Organization

**Important**: Maintain the exact file structure and naming conventions:
- Directory names: `threefold_conspiracy_book_1`, `unknown_treasures`, etc.
- File names: Use the exact sanitized title from the script
- File paths: `episodes/[series_directory]/[episode_title].md`

The script relies on this structure to skip already transcribed episodes.

## Development Contributions

### Areas of Focus

We're particularly interested in contributions that improve:

1. **Diarization Accuracy**
   - Better speaker identification
   - Improved overlap detection
   - Enhanced speaker clustering algorithms

2. **Starfinder Vocabulary Integration**
   - Add custom vocabulary dictionaries
   - Improve recognition of game terms
   - Character and place name dictionaries
   - Class and ability terminology

3. **Performance Optimization**
   - Faster transcription processing
   - Reduced memory usage
   - Better GPU utilization

4. **Feature Enhancements**
   - Support for additional audio formats
   - Multi-language transcription
   - Batch processing improvements
   - Better error handling

### Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/will-save-the-transcriber.git
   cd will-save-the-transcriber
   ```

2. **Set Up Development Environment**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install dependencies
   uv sync
   
   # Activate virtual environment
   source .venv/bin/activate
   ```

3. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Code Style

- **Python**: Follow PEP 8 guidelines
- **Comments**: Use clear, descriptive comments
- **Docstrings**: Include docstrings for all functions and classes
- **Type Hints**: Use type hints where appropriate
- **Error Handling**: Implement proper error handling and logging

### Testing

Before submitting a PR:

1. **Test Your Changes**
   ```bash
   # Test with a sample audio file
   python transcribe_simple.py test_audio.mp3
   python transcribe_advanced.py test_audio.mp3
   python podcast_transcriber.py --keep-audio
   ```

2. **Check Compatibility**
   - Test on different platforms if possible
   - Verify with different audio formats
   - Test both diarization versions (v1 and v2)

3. **Performance Testing**
   - Compare processing times
   - Check memory usage
   - Verify accuracy improvements

### Pull Request Process

1. **Create an Issue First** (for features)
   - Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
   - Discuss the proposed changes
   - Get feedback from maintainers

2. **Make Your Changes**
   - Follow the code style guidelines
   - Add tests if applicable
   - Update documentation

3. **Submit the PR**
   - Use a clear, descriptive title
   - Include a detailed description
   - Reference related issues
   - Add screenshots or examples if relevant

4. **PR Title Format**
   ```
   [type]: [brief description]
   ```
   
   **Types:**
   - `feat`: New features
   - `fix`: Bug fixes
   - `docs`: Documentation changes
   - `perf`: Performance improvements
   - `refactor`: Code refactoring
   - `test`: Adding or updating tests

   **Examples:**
   ```
   feat: add Starfinder vocabulary dictionary
   fix: improve speaker diarization accuracy
   perf: optimize audio processing pipeline
   ```

## Review Process

- All PRs require review from maintainers
- We aim to review within 48 hours
- Feedback will be constructive and helpful
- We may request changes before merging

## Questions or Need Help?

- **Issues**: Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
- **Discussions**: Start a discussion in the GitHub Discussions tab
- **Documentation**: Check the README.md and other documentation files

## Code of Conduct

We're committed to providing a welcoming and inclusive environment. Please:
- Be respectful and constructive
- Help others learn and contribute
- Focus on the content and quality of contributions
- Report any inappropriate behavior

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for helping make podcast content more accessible!** 🎙️✨ 