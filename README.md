# CodeSync - Real-time Collaborative Code Editor

<div align="center">

![CodeSync Banner](https://img.shields.io/badge/CodeSync-Next--Gen_Collab-00F2FE?style=for-the-badge&logo=visual-studio-code&logoColor=white)

**A god-tier collaborative development environment with integrated AI, terminal access, and seamless real-time synchronization.**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-4.7+-010101?style=flat-square&logo=socket.io&logoColor=white)](https://socket.io/)
[![Ace Editor](https://img.shields.io/badge/Ace_Editor-1.32-E34C26?style=flat-square&logo=javascript&logoColor=white)](https://ace.c9.io/)

</div>

---

## 🌟 Features

### 🔥 Core Features
- **Real-time Collaboration** - Multiple users can edit code simultaneously with live cursor tracking
- **Multi-language Support** - Python, JavaScript, Java, C/C++, Go, Rust, Ruby, PHP, TypeScript, and more
- **Code Execution** - Run code directly in the browser with instant output
- **Live Cursors & Selections** - See where your teammates are working in real-time
- **Integrated Chat** - Built-in communication system for team collaboration
- **File Management** - Create, delete, rename, and organize files within rooms

### 🤖 AI-Powered Features
- **AI Code Assistance** - Get help with debugging, optimization, and code completion
- **Multiple AI Providers** - Support for Google Gemini, OpenAI, Anthropic Claude, and Groq
- **Code Analysis** - Automated complexity analysis and improvement suggestions
- **Smart Completion** - AI-powered code completion and suggestions

### 💻 Development Tools
- **Terminal Integration** - Built-in terminal for running commands
- **Code Snippets** - Pre-built code templates for rapid development
- **Syntax Highlighting** - Advanced syntax highlighting for all supported languages
- **Theme Customization** - Multiple editor themes (Monokai, Twilight, GitHub, Solarized, etc.)
- **Auto-save** - Automatic file saving with configurable intervals

### 🎨 User Experience
- **Modern UI/UX** - Sleek, glass-morphism design with smooth animations
- **Responsive Design** - Works seamlessly on desktop and mobile devices
- **Session Management** - Recent rooms tracking for quick access
- **User Presence** - See who's online in your room
- **Status Indicators** - Real-time file and connection status

---

## 📋 Table of Contents

- [Features](#-features)
- [Screenshots](#-screenshots)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Supported Languages](#-supported-languages)
- [API Endpoints](#-api-endpoints)
- [WebSocket Events](#-websocket-events)
- [Configuration](#-configuration)
- [AI Integration](#-ai-integration)
- [File Structure](#-file-structure)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🖼️ Screenshots

### Landing Page
Modern, animated landing page with glassmorphism effects and recent sessions

### Editor Interface
Split-panel IDE with file explorer, code editor, and output console

### Real-time Collaboration
Live cursor tracking and synchronized code editing

---

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework
- **Flask-SocketIO** - WebSocket implementation for real-time communication
- **Python 3.8+** - Core programming language

### Frontend
- **Ace Editor** - Powerful code editor with syntax highlighting
- **Socket.IO** - Real-time bidirectional event-based communication
- **Vanilla JavaScript** - No heavy frameworks, just pure performance
- **CSS3** - Modern styling with animations and transitions

### AI Integration
- **Google Gemini API** - Advanced AI assistance
- **OpenAI API** - GPT models for code generation
- **Anthropic Claude API** - Advanced reasoning and code analysis
- **Groq API** - Ultra-fast inference

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Node.js and npm (for running JavaScript code)
- Optional: Java, C/C++ compilers, Go, Rust for respective language support

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/codesync.git
cd codesync
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install flask flask-socketio python-socketio
```

### Step 4: Create Required Directories
```bash
mkdir -p rooms settings snippets static/css
```

### Step 5: Add CSS File
Create `static/css/style.css` with the following base styles:

```css
:root {
    --primary: #00F2FE;
    --secondary: #4FACFE;
    --bg-dark: #050510;
    --bg-dark-secondary: #0a0a1a;
    --text-main: #ffffff;
    --text-muted: #a0a0b0;
    --glass-border: rgba(255, 255, 255, 0.1);
    --gradient-primary: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    --radius-sm: 6px;
    --radius-md: 12px;
    --radius-lg: 20px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Outfit', sans-serif;
    background: var(--bg-dark);
    color: var(--text-main);
    overflow-x: hidden;
    min-height: 100vh;
}

.text-gradient {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.glass {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
}

.animate-fade-in {
    animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Step 6: Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

---

## 🚀 Usage

### Starting a New Room
1. Navigate to `http://localhost:5000`
2. Enter a room name or use the auto-generated suggestion
3. Click "Launch" to create/join a room

### Collaborating
1. Share the room URL with teammates
2. All users in the same room can see live code changes
3. Use the chat panel to communicate
4. See cursor positions and selections in real-time

### Running Code
1. Select a file or create a new one
2. Write or paste your code
3. Click the "Run" button or use `Ctrl+Enter`
4. View output in the console panel

### Using AI Assistance
1. Click the AI icon in the toolbar
2. Select your AI provider and enter your API key
3. Choose a task (debug, optimize, complete, or chat)
4. Get instant AI-powered suggestions

### Terminal Commands
1. Click the terminal tab in the output panel
2. Enter commands (limited to safe commands for security)
3. View command output in real-time

---

## 💻 Supported Languages

| Language   | Execution | Compilation | Extension |
|------------|-----------|-------------|-----------|
| Python     | ✅        | N/A         | .py       |
| JavaScript | ✅        | N/A         | .js       |
| TypeScript | ✅        | N/A         | .ts       |
| Java       | ✅        | ✅          | .java     |
| C          | ✅        | ✅          | .c        |
| C++        | ✅        | ✅          | .cpp      |
| Go         | ✅        | N/A         | .go       |
| Rust       | ✅        | ✅          | .rs       |
| Ruby       | ✅        | N/A         | .rb       |
| PHP        | ✅        | N/A         | .php      |
| Bash       | ✅        | N/A         | .sh       |
| SQL        | ✅        | N/A         | .sql      |
| HTML       | Preview   | N/A         | .html     |
| CSS        | Preview   | N/A         | .css      |

---

## 🔌 API Endpoints

### REST API

#### File Operations
- `GET /api/files/<room_id>` - List all files in a room
- `GET /api/file/<room_id>/<filename>` - Get file content
- `POST /api/file/<room_id>/<filename>` - Save file content
- `DELETE /api/file/<room_id>/<filename>` - Delete a file
- `POST /api/file/<room_id>/<old_name>/rename` - Rename a file

#### Code Execution
- `POST /api/execute` - Execute code
  ```json
  {
    "room_id": "my-room",
    "filename": "script.py",
    "language": "python"
  }
  ```

#### AI Features
- `POST /api/ai_assist` - Get AI assistance
  ```json
  {
    "api_key": "your-api-key",
    "provider": "gemini",
    "model": "gemini-pro",
    "prompt": "Debug this code",
    "context": "print('hello world)",
    "task": "debug"
  }
  ```

- `POST /api/analyze_code` - Analyze code complexity
  ```json
  {
    "code": "def hello(): pass",
    "language": "python"
  }
  ```

#### Settings
- `GET /api/settings/<room_id>` - Get room settings
- `POST /api/settings/<room_id>` - Save room settings

#### Languages
- `GET /api/languages` - Get list of supported languages
- `GET /api/snippets/<language>` - Get code snippets for a language

---

## 🔄 WebSocket Events

### Client → Server

| Event              | Data                                          | Description                    |
|--------------------|-----------------------------------------------|--------------------------------|
| `join`             | `{room, username, color}`                     | User joins a room              |
| `leave`            | `{room}`                                      | User leaves a room             |
| `code_change`      | `{room, file, content, auto_save}`            | Code content changed           |
| `cursor_move`      | `{room, cursor: {row, column}}`               | Cursor position updated        |
| `selection_change` | `{room, selection}`                           | Text selection changed         |
| `chat_message`     | `{room, message}`                             | Chat message sent              |
| `terminal_input`   | `{room, command}`                             | Terminal command executed      |

### Server → Client

| Event              | Data                                          | Description                    |
|--------------------|-----------------------------------------------|--------------------------------|
| `user_joined`      | `{username, users[], sid}`                    | User joined notification       |
| `user_left`        | `{username, users[], sid}`                    | User left notification         |
| `update_code`      | `{file, content, user}`                       | Code update from other user    |
| `remote_cursor`    | `{sid, username, cursor, color}`              | Remote cursor position         |
| `remote_selection` | `{sid, selection, username}`                  | Remote text selection          |
| `chat_message`     | `{username, message, timestamp}`              | Chat message broadcast         |
| `terminal_output`  | `{output, command}`                           | Terminal command output        |
| `status`           | `{msg, type}`                                 | Status notification            |

---

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Server Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# File Limits
MAX_FILE_SIZE=5242880  # 5MB in bytes
CODE_EXECUTION_TIMEOUT=10

# AI Configuration (Optional)
DEFAULT_AI_PROVIDER=gemini
```

### Room Settings
Each room can have custom settings stored in `settings/<room_id>.json`:

```json
{
  "theme": "monokai",
  "font_size": 14,
  "tab_size": 4,
  "auto_save": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### Editor Themes
Available themes:
- `monokai` (default)
- `twilight`
- `github`
- `solarized_dark`
- `solarized_light`
- `tomorrow_night`
- `dracula`

---

## 🤖 AI Integration

### Supported AI Providers

#### 1. Google Gemini
```javascript
provider: 'gemini'
models: ['gemini-pro', 'gemini-1.5-pro']
```

#### 2. OpenAI
```javascript
provider: 'openai'
models: ['gpt-4', 'gpt-3.5-turbo']
```

#### 3. Anthropic Claude
```javascript
provider: 'anthropic'
models: ['claude-3-opus', 'claude-3-sonnet']
```

#### 4. Groq
```javascript
provider: 'groq'
models: ['mixtral-8x7b', 'llama2-70b']
```

### AI Tasks
- **Debug** - Find and fix errors in code
- **Optimize** - Improve code performance and efficiency
- **Complete** - Auto-complete code snippets
- **Chat** - General programming assistance

### Getting API Keys
- **Gemini**: https://makersuite.google.com/app/apikey
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Groq**: https://console.groq.com/

---

## 📁 File Structure

```
codesync/
├── app.py                  # Flask application & Socket.IO server
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── templates/
│   ├── landing.html       # Landing page
│   └── room.html          # Collaborative editor interface
│
├── static/
│   ├── css/
│   │   └── style.css      # Global styles
│   └── js/
│       └── room.js        # Frontend logic
│
├── rooms/                 # User rooms (auto-created)
│   └── <room-id>/
│       ├── main.py
│       ├── script.js
│       └── ...
│
├── settings/              # Room settings (auto-created)
│   └── <room-id>.json
│
└── snippets/             # Code snippets (auto-created)
    └── <language>.json
```

---

## 🔒 Security

### Implemented Security Measures

1. **Terminal Command Whitelist**
   - Only safe commands are allowed
   - Prevents arbitrary code execution
   - Restricted to development tools

2. **File Path Validation**
   - Prevents directory traversal attacks
   - Validates all file operations
   - Restricts access to room directories

3. **File Size Limits**
   - Maximum 5MB per file
   - Prevents resource exhaustion

4. **Code Execution Timeout**
   - 10-second timeout for code execution
   - Prevents infinite loops

5. **Input Sanitization**
   - All user inputs are validated
   - SQL injection prevention
   - XSS protection

### Security Best Practices

⚠️ **For Production Deployment:**
- Use HTTPS/WSS for encrypted connections
- Implement user authentication
- Add rate limiting
- Use environment variables for secrets
- Enable CORS only for trusted domains
- Regularly update dependencies
- Implement proper session management
- Add input validation on all endpoints

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Bugs
1. Check if the bug has already been reported
2. Create a detailed issue with reproduction steps
3. Include error messages and screenshots

### Suggesting Features
1. Open an issue with the `enhancement` label
2. Describe the feature and its benefits
3. Provide use cases and examples

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Test your changes thoroughly
- Update documentation as needed

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 CodeSync

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **Ace Editor** - Powerful code editor
- **Flask & Socket.IO** - Real-time web framework
- **Font Awesome** - Beautiful icons
- **Google Fonts** - Typography (JetBrains Mono, Outfit)
- **AI Providers** - Gemini, OpenAI, Claude, Groq for AI capabilities

---

## 📧 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/codesync/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/codesync/discussions)
- **Email**: support@codesync.dev

---

## 🗺️ Roadmap

### Upcoming Features
- [ ] Video/Audio chat integration
- [ ] Git integration
- [ ] Code review tools
- [ ] Plugin system
- [ ] Offline mode with sync
- [ ] Mobile app (iOS/Android)
- [ ] Whiteboard for diagrams
- [ ] Code diff viewer
- [ ] Performance profiling
- [ ] Docker integration

### In Progress
- [x] Real-time collaboration
- [x] Multi-language support
- [x] AI assistance
- [x] Terminal integration
- [x] File management

---

## 📊 Project Status

![GitHub Stars](https://img.shields.io/github/stars/yourusername/codesync?style=social)
![GitHub Forks](https://img.shields.io/github/forks/yourusername/codesync?style=social)
![GitHub Issues](https://img.shields.io/github/issues/yourusername/codesync)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/yourusername/codesync)

**Status**: ✨ Active Development

---

<div align="center">

Made with ❤️ by developers, for developers

**[⬆ Back to Top](#codesync---real-time-collaborative-code-editor)**

</div>
