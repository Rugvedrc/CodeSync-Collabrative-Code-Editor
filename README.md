# 🚀 CodeSync – Real-Time Collaborative Coding Platform

CodeSync is a web-based collaborative coding environment that allows multiple users to write, run, and analyze code together in real time.  
It combines a powerful in-browser IDE, live collaboration via WebSockets, integrated terminal, chat, and AI-assisted code analysis.

---

## ✨ Features

- 🧑‍🤝‍🧑 **Real-time collaboration** using Socket.IO
- 📝 **Multi-language code editor** (Python, JS, Java, C/C++, Go, Rust, etc.)
- ▶️ **Run code directly** from the browser
- 💬 **Built-in chat** for team communication
- 🖥️ **Integrated terminal**
- 🤖 **AI Assistant**
  - Code explanation
  - Debugging
  - Refactoring
  - Optimization
- 📊 **Code analysis & complexity metrics**
- 📂 **File & folder management per room**
- 🔐 **Isolated execution with safety checks**

---

## 🛠️ Tech Stack

### Frontend
- HTML, CSS, JavaScript
- Ace Editor
- Socket.IO Client

### Backend
- Python
- Flask
- Flask-SocketIO
- Eventlet

### AI Providers
- Google Gemini
- OpenAI
- Anthropic

---

## 📂 Project Structure

codesync/
│
├── app.py # Flask backend + Socket.IO server
├── requirements.txt # Python dependencies
│
├── templates/
│ ├── landing.html # Landing page
│ └── room.html # Collaborative IDE page
│
├── static/
│ ├── css/
│ │ └── style.css
│ └── js/
│ └── room.js
│
├── rooms/ # Room-specific files (auto-created)
├── settings/ # Room settings
├── snippets/ # Language snippets
└── README.md


---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<your-username>/codesync.git
cd codesync
2️⃣ Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
3️⃣ Install dependencies
pip install -r requirements.txt
4️⃣ Run the application
python app.py
Server will start at:

http://127.0.0.1:5000
🚪 How It Works
Open the landing page

Create or join a room

Start coding collaboratively

Run code, chat, use terminal, or ask AI for help

All changes sync instantly across users

🔐 Security Notes
File access is sandboxed per room

Execution timeout enforced

File size limits applied

Path traversal protection enabled

🚧 Future Improvements
Authentication & user accounts

Docker-based sandboxed execution

Persistent cloud storage

Role-based access control

Voice collaboration

📜 License
This project is for educational and experimental purposes.

🙌 Author
Built with ❤️ by Rugved Chandekar