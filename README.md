# CodeSync - Real-time Collaborative Code Editor

A collaborative coding platform with real-time synchronization, multi-language support, and AI assistance.

## ✨ Features

- **Real-time Collaboration** - Multiple users can code together with live cursor tracking
- **Multi-language Support** - Python, JavaScript, Java, C/C++, Go, Rust, and more
- **Code Execution** - Run code directly in the browser
- **AI Assistant** - Get help with debugging and code optimization (Gemini, OpenAI, Claude, Groq)
- **Built-in Terminal** - Execute commands in a sandboxed environment
- **File Management** - Create, edit, delete files in organized rooms
- **Live Chat** - Communicate with teammates in real-time

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js (for JavaScript execution)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/codesync.git
cd codesync

# Install dependencies
pip install flask flask-socketio python-socketio

# Run the application
python app.py
```

Visit `http://localhost:5000` to start coding!

## 📖 Usage

1. Enter a room name on the landing page
2. Share the room URL with teammates
3. Start coding together in real-time
4. Use the AI assistant for help (API key required)
5. Execute code and see output instantly

## 🛠️ Tech Stack

**Backend:**
- Flask + Flask-SocketIO
- Python 3.8+

**Frontend:**
- Ace Editor
- Socket.IO
- Vanilla JavaScript

**AI Integration:**
- Google Gemini
- OpenAI GPT
- Anthropic Claude
- Groq

## 💻 Supported Languages

Python • JavaScript • TypeScript • Java • C • C++ • Go • Rust • Ruby • PHP • Bash • SQL • HTML • CSS

## 🔌 Main API Endpoints

- `GET /api/files/<room_id>` - List files
- `POST /api/file/<room_id>/<filename>` - Save file
- `POST /api/execute` - Execute code
- `POST /api/ai_assist` - AI assistance

## 🔒 Security Notes

⚠️ **This is a development version.** For production:
- Add user authentication
- Use HTTPS/WSS
- Implement rate limiting
- Validate all inputs
- Add proper session management

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📝 License

MIT License - feel free to use this project for learning and development.

## 👨‍💻 Author

Made with ❤️ by Rugved Chandekar

---

⭐ Star this repo if you find it helpful!
