# Contributing to Bot Factory

Thank you for your interest in contributing to Bot Factory!

## How to Contribute

### Reporting Issues

1. Check if the issue already exists
2. Create a new issue with a clear description
3. Include steps to reproduce (if applicable)
4. Add relevant labels

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes locally
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/chicohaager/bot-factory.git
cd bot-factory

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
npm run dev
```

### Code Style

- Python: Follow PEP 8 guidelines
- JavaScript/React: Use ESLint with the provided configuration
- Keep code clean and well-documented

### Testing

Before submitting a PR, ensure:
- The application runs without errors
- Docker build completes successfully
- No security vulnerabilities are introduced

## Questions?

Open an issue or contact the maintainer.
