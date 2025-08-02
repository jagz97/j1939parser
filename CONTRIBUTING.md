# Contributing to j1939parser

Thanks for your interest in contributing to the project!

We welcome improvements, fixes, and suggestions for `j1939parser`. Here's how you can help:

---

## Getting Started

1. **Fork** this repository and **clone** your fork:
   ```bash
   git clone https://github.com/jagz97/j1939parser.git
   cd j1939parser
   ```

2. **Set up your environment** (with optional CAN support):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e '.[can]'
   ```

3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/my-new-feature
   ```

---

## Code Guidelines

- Keep code clean and readable
- Follow [PEP8](https://pep8.org/) conventions
- Avoid unnecessary dependencies
- Write docstrings and comments where needed

---

## Testing

We use `pytest` for testing.

To run tests:

```bash
pip install pytest
pytest tests/
```

Please include unit tests for any new feature or logic you contribute.

---

## Submitting a Pull Request

1. Push your branch:
   ```bash
   git push origin feature/my-new-feature
   ```

2. Open a pull request (PR) to the `main` branch on GitHub

3. Clearly explain:
   - What the PR does
   - Why it’s needed
   - Any limitations or follow-ups

---

## Questions?

Feel free to open an [Issue](https://github.com/jagz97/j1939parser/issues) for bugs, feature requests, or clarification.
```

---