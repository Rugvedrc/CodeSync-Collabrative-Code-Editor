from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, join_room, leave_room, emit
import os
import sys
import subprocess
import tempfile
import uuid
import json
import re
import time
from datetime import datetime
from collections import defaultdict
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

# Configuration
ROOMS_DIR = "rooms"
SETTINGS_DIR = "settings"
SNIPPETS_DIR = "snippets"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
CODE_EXECUTION_TIMEOUT = 10

# In-memory storage
room_users = {}  # room_id -> {sid: {username, cursor, selection}}
room_locks = defaultdict(threading.Lock)  # room_id -> Lock
active_terminals = {}  # room_id -> terminal_data

# Language configurations
LANGUAGE_CONFIG = {
    'python': {
        'extension': '.py',
        'command': [sys.executable, '{file}'],
        'comment': '#',
        'template': '# Python code\nprint("Hello, World!")\n',
        'ace_mode': 'python'
    },
    'javascript': {
        'extension': '.js',
        'command': ['node', '{file}'],
        'comment': '//',
        'template': '// JavaScript code\nconsole.log("Hello, World!");\n',
        'ace_mode': 'javascript'
    },
    'java': {
        'extension': '.java',
        'command': ['java', '{file}'],
        'comment': '//',
        'template': 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}\n',
        'ace_mode': 'java',
        'compile': ['javac', '{file}'],
        'run': ['java', '{classname}']
    },
    'cpp': {
        'extension': '.cpp',
        'command': ['{executable}'],
        'comment': '//',
        'template': '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello, World!" << endl;\n    return 0;\n}\n',
        'ace_mode': 'c_cpp',
        'compile': ['g++', '{file}', '-o', '{executable}']
    },
    'c': {
        'extension': '.c',
        'command': ['{executable}'],
        'comment': '//',
        'template': '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}\n',
        'ace_mode': 'c_cpp',
        'compile': ['gcc', '{file}', '-o', '{executable}']
    },
    'ruby': {
        'extension': '.rb',
        'command': ['ruby', '{file}'],
        'comment': '#',
        'template': '# Ruby code\nputs "Hello, World!"\n',
        'ace_mode': 'ruby'
    },
    'go': {
        'extension': '.go',
        'command': ['go', 'run', '{file}'],
        'comment': '//',
        'template': 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}\n',
        'ace_mode': 'golang'
    },
    'rust': {
        'extension': '.rs',
        'command': ['{executable}'],
        'comment': '//',
        'template': 'fn main() {\n    println!("Hello, World!");\n}\n',
        'ace_mode': 'rust',
        'compile': ['rustc', '{file}', '-o', '{executable}']
    },
    'php': {
        'extension': '.php',
        'command': ['php', '{file}'],
        'comment': '//',
        'template': '<?php\necho "Hello, World!\\n";\n?>\n',
        'ace_mode': 'php'
    },
    'bash': {
        'extension': '.sh',
        'command': ['bash', '{file}'],
        'comment': '#',
        'template': '#!/bin/bash\necho "Hello, World!"\n',
        'ace_mode': 'sh'
    },
    'typescript': {
        'extension': '.ts',
        'command': ['ts-node', '{file}'],
        'comment': '//',
        'template': '// TypeScript code\nconsole.log("Hello, World!");\n',
        'ace_mode': 'typescript'
    },
    'html': {
        'extension': '.html',
        'comment': '<!--',
        'template': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Document</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>\n',
        'ace_mode': 'html'
    },
    'css': {
        'extension': '.css',
        'comment': '/*',
        'template': '/* CSS code */\nbody {\n    font-family: Arial, sans-serif;\n}\n',
        'ace_mode': 'css'
    },
    'sql': {
        'extension': '.sql',
        'command': ['sqlite3', ':memory:', '<', '{file}'],
        'comment': '--',
        'template': '-- SQL code\nSELECT "Hello, World!";\n',
        'ace_mode': 'sql'
    }
}

# ============ File Management Functions ============

def ensure_dir(path):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)

def get_room_path(room_id):
    """Get path for room directory"""
    return os.path.join(ROOMS_DIR, room_id)

def get_settings_path(room_id):
    """Get path for room settings"""
    ensure_dir(SETTINGS_DIR)
    return os.path.join(SETTINGS_DIR, f"{room_id}.json")

def create_room(room_id):
    """Create a new room with default structure"""
    path = get_room_path(room_id)
    ensure_dir(path)
    
    # Create default file if room is empty
    if not os.listdir(path):
        with open(os.path.join(path, "main.py"), "w") as f:
            f.write(LANGUAGE_CONFIG['python']['template'])
    
    # Create default settings
    settings_path = get_settings_path(room_id)
    if not os.path.exists(settings_path):
        default_settings = {
            'theme': 'monokai',
            'font_size': 14,
            'tab_size': 4,
            'auto_save': True,
            'created_at': datetime.now().isoformat()
        }
        save_room_settings(room_id, default_settings)
    
    return True

def list_files(room_id):
    """List all files in room with metadata"""
    path = get_room_path(room_id)
    if not os.path.exists(path):
        return []
    
    files = []
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, path)
            
            # Get file stats
            stat = os.stat(full_path)
            
            # Determine language/type
            ext = os.path.splitext(filename)[1]
            lang = detect_language(filename)
            
            files.append({
                "name": filename,
                "path": rel_path,
                "type": lang,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": ext
            })
    
    return sorted(files, key=lambda x: x['name'])

def detect_language(filename):
    """Detect programming language from filename"""
    ext = os.path.splitext(filename)[1].lower()
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.sh': 'bash',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.sql': 'sql',
        '.json': 'json',
        '.xml': 'xml',
        '.md': 'markdown',
        '.txt': 'text'
    }
    return ext_map.get(ext, 'text')

def get_file_content(room_id, filename):
    """Get content of a file"""
    path = os.path.join(get_room_path(room_id), filename)
    
    # Security check
    if not is_safe_path(room_id, path):
        return None
    
    if os.path.exists(path) and os.path.isfile(path):
        try:
            with open(path, "r", encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return "[Binary file - cannot display]"
    return ""

def save_file_content(room_id, filename, content):
    """Save content to a file"""
    path = os.path.join(get_room_path(room_id), filename)
    
    # Security check
    if not is_safe_path(room_id, path):
        return False
    
    # Check file size
    if len(content.encode('utf-8')) > MAX_FILE_SIZE:
        return False
    
    # Ensure directory exists
    ensure_dir(os.path.dirname(path))
    
    try:
        with open(path, "w", encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception:
        return False

def create_new_file(room_id, filename, content=""):
    """Create a new file"""
    path = os.path.join(get_room_path(room_id), filename)
    
    if os.path.exists(path):
        return False
    
    # Detect language and use template
    if not content:
        lang = detect_language(filename)
        if lang in LANGUAGE_CONFIG and 'template' in LANGUAGE_CONFIG[lang]:
            content = LANGUAGE_CONFIG[lang]['template']
    
    ensure_dir(os.path.dirname(path))
    
    try:
        with open(path, "w", encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception:
        return False

def delete_file(room_id, filename):
    """Delete a file"""
    path = os.path.join(get_room_path(room_id), filename)
    
    if not is_safe_path(room_id, path):
        return False
    
    if os.path.exists(path) and os.path.isfile(path):
        try:
            os.remove(path)
            return True
        except Exception:
            return False
    return False

def rename_file(room_id, old_name, new_name):
    """Rename a file"""
    old_path = os.path.join(get_room_path(room_id), old_name)
    new_path = os.path.join(get_room_path(room_id), new_name)
    
    if not is_safe_path(room_id, old_path) or not is_safe_path(room_id, new_path):
        return False
    
    if os.path.exists(old_path) and not os.path.exists(new_path):
        try:
            ensure_dir(os.path.dirname(new_path))
            os.rename(old_path, new_path)
            return True
        except Exception:
            return False
    return False

def is_safe_path(room_id, path):
    """Check if path is within room directory (security)"""
    room_path = os.path.abspath(get_room_path(room_id))
    target_path = os.path.abspath(path)
    return target_path.startswith(room_path)

# ============ Code Execution Functions ============

def execute_code(language, code, input_data="", room_id=None, filename=None):
    """Execute code in specified language"""
    if language not in LANGUAGE_CONFIG:
        return {"output": f"Language '{language}' not supported", "error": True}
    
    config = LANGUAGE_CONFIG[language]
    
    # HTML/CSS can't be executed
    if language in ['html', 'css']:
        return {"output": "HTML/CSS files are rendered in preview, not executed.", "error": False}
    
    temp_dir_manager = None
    try:
        # Determine Execution Context
        if room_id and filename:
            # Run in Room Directory (Integrated)
            cwd = get_room_path(room_id)
            if not os.path.exists(cwd):
                return {"output": "Room directory not found", "error": True}
                
            source_file = os.path.join(cwd, filename)
            
            # Ensure latest code is saved
            saved = save_file_content(room_id, filename, code)
            if not saved:
                return {"output": "Failed to save file before execution.", "error": True}
                
            # For Java, derive classname from filename
            classname = os.path.splitext(os.path.basename(filename))[0]
            
        else:
            # Run in Temporary Directory (Isolated)
            temp_dir_manager = tempfile.TemporaryDirectory()
            cwd = temp_dir_manager.name
            
            # Setup file
            ext = config['extension']
            if language == 'java':
                class_match = re.search(r'public\s+class\s+(\w+)', code)
                classname = class_match.group(1) if class_match else "Main"
                source_file = os.path.join(cwd, f"{classname}.java")
            else:
                classname = "program"
                source_file = os.path.join(cwd, f"code{ext}")
                
            with open(source_file, 'w', encoding='utf-8') as f:
                f.write(code)

        # Prepare Executable Path (for compiled langs)
        executable = os.path.join(cwd, 'program.exe' if sys.platform == 'win32' else 'program')

        # Execution Logic
        if 'compile' in config:
            # Special handling for Java
            if language == 'java':
                 # Compile
                 compile_cmd = [cmd.replace('{file}', source_file) for cmd in config['compile']]
                 compile_result = subprocess.run(compile_cmd, cwd=cwd, capture_output=True, text=True, timeout=CODE_EXECUTION_TIMEOUT)
                 if compile_result.returncode != 0:
                     return {"output": f"Compilation Error:\n{compile_result.stderr}", "error": True}
                 # Run
                 run_cmd = [cmd.replace('{classname}', classname) for cmd in config['run']]
            else:
                 # Compile C/C++/Rust
                 compile_cmd = [
                     cmd.replace('{file}', source_file).replace('{executable}', executable)
                     for cmd in config['compile']
                 ]
                 compile_result = subprocess.run(compile_cmd, cwd=cwd, capture_output=True, text=True, timeout=CODE_EXECUTION_TIMEOUT)
                 if compile_result.returncode != 0:
                     return {"output": f"Compilation Error:\n{compile_result.stderr}", "error": True}
                 
                 run_cmd = [cmd.replace('{executable}', executable) for cmd in config['command']]
        else:
            # Interpreted
            run_cmd = [cmd.replace('{file}', source_file) for cmd in config['command']]

        # Run the command
        result = subprocess.run(
            run_cmd,
            input=input_data,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=CODE_EXECUTION_TIMEOUT
        )
        
        # Prepare output
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]:\n{result.stderr}"
        
        return {
            "output": output if output else "[No output]",
            "error": result.returncode != 0,
            "exit_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {"output": f"Error: Execution timed out (max {CODE_EXECUTION_TIMEOUT}s)", "error": True}
    except FileNotFoundError as e:
        return {"output": f"Error: Compiler/Interpreter not found via PATH. ({str(e)})", "error": True}
    except Exception as e:
        return {"output": f"Execution Error: {str(e)}", "error": True}
    finally:
        if temp_dir_manager:
            temp_dir_manager.cleanup()

# ============ AI Features ============

def ai_chat(provider, model, api_key, prompt, code_context=None, task_type='chat'):
    """AI assistant interaction"""
    if not api_key:
        return "Error: API Key not provided. Please configure your API key in settings."
    
    system_prompts = {
        'chat': "You are an intelligent coding assistant. Be helpful, concise, and professional.",
        'explain': "Explain the following code clearly and concisely. Break down complex logic.",
        'debug': "Analyze the code for bugs, errors, or issues. Provide specific fixes.",
        'optimize': "Suggest optimizations for performance, readability, or best practices.",
        'complete': "Complete the code intelligently. Return only the code completion.",
        'refactor': "Refactor the code to improve structure, readability, and maintainability.",
        'document': "Add comprehensive documentation and comments to the code.",
        'test': "Generate unit tests for the code.",
        'convert': "Convert the code to the requested language while maintaining functionality."
    }
    
    system_instruction = system_prompts.get(task_type, system_prompts['chat'])
    
    # Format prompt with context
    full_prompt = f"{prompt}\n\n"
    if code_context:
        full_prompt += f"Code ({code_context.get('language', 'text')}):\n```\n{code_context.get('code', '')}\n```\n"
    
    try:
        if provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_instance = genai.GenerativeModel(model)
            response = model_instance.generate_content(f"{system_instruction}\n\n{full_prompt}")
            return response.text
            
        elif provider == 'openai':
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": full_prompt}
                ]
            )
            return response.choices[0].message.content
            
        elif provider == 'anthropic':
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": full_prompt}],
                system=system_instruction
            )
            return response.content[0].text
            
        return "Error: Unknown AI provider"
        
    except Exception as e:
        return f"AI Error: {str(e)}"

def analyze_code_complexity(code, language):
    """Analyze code complexity metrics"""
    lines = code.split('\n')
    total_lines = len(lines)
    code_lines = len([l for l in lines if l.strip() and not l.strip().startswith(LANGUAGE_CONFIG.get(language, {}).get('comment', '#'))])
    blank_lines = len([l for l in lines if not l.strip()])
    
    # Simple cyclomatic complexity (count decision points)
    decision_keywords = ['if', 'else', 'elif', 'for', 'while', 'switch', 'case', 'catch', '&&', '||', '?']
    complexity = 1  # Base complexity
    for keyword in decision_keywords:
        complexity += code.lower().count(keyword)
    
    return {
        'total_lines': total_lines,
        'code_lines': code_lines,
        'blank_lines': blank_lines,
        'comment_lines': total_lines - code_lines - blank_lines,
        'cyclomatic_complexity': complexity,
        'complexity_rating': 'Low' if complexity < 10 else 'Medium' if complexity < 20 else 'High'
    }

def get_code_suggestions(code, language):
    """Get automated code suggestions"""
    suggestions = []
    
    # Check for common issues
    if language == 'python':
        if 'import *' in code:
            suggestions.append({'type': 'warning', 'message': 'Avoid wildcard imports (import *)'})
        if re.search(r'\bexec\b|\beval\b', code):
            suggestions.append({'type': 'security', 'message': 'Avoid using exec() or eval() - security risk'})
        if 'TODO' in code or 'FIXME' in code:
            suggestions.append({'type': 'info', 'message': 'Contains TODO/FIXME comments'})
    
    if language == 'javascript':
        if 'var ' in code:
            suggestions.append({'type': 'info', 'message': 'Consider using let/const instead of var'})
        if '==' in code and '===' not in code:
            suggestions.append({'type': 'warning', 'message': 'Use === for strict equality comparison'})
    
    # Check line length
    long_lines = [i+1 for i, line in enumerate(code.split('\n')) if len(line) > 100]
    if long_lines:
        suggestions.append({'type': 'style', 'message': f'Long lines detected: {long_lines[:5]}'})
    
    return suggestions

# ============ Room Settings ============

def get_room_settings(room_id):
    """Get room settings"""
    settings_path = get_settings_path(room_id)
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    return {
        'theme': 'monokai',
        'font_size': 14,
        'tab_size': 4,
        'auto_save': True
    }

def save_room_settings(room_id, settings):
    """Save room settings"""
    settings_path = get_settings_path(room_id)
    try:
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False

# ============ Code Snippets ============

def get_snippets(language):
    """Get code snippets for language"""
    ensure_dir(SNIPPETS_DIR)
    snippet_file = os.path.join(SNIPPETS_DIR, f"{language}.json")
    
    default_snippets = {
        'python': [
            {'name': 'function', 'code': 'def function_name(param):\n    pass\n'},
            {'name': 'class', 'code': 'class ClassName:\n    def __init__(self):\n        pass\n'},
            {'name': 'for loop', 'code': 'for item in items:\n    pass\n'},
            {'name': 'if-else', 'code': 'if condition:\n    pass\nelse:\n    pass\n'},
        ],
        'javascript': [
            {'name': 'function', 'code': 'function functionName(param) {\n    \n}\n'},
            {'name': 'arrow function', 'code': 'const functionName = (param) => {\n    \n};\n'},
            {'name': 'class', 'code': 'class ClassName {\n    constructor() {\n        \n    }\n}\n'},
            {'name': 'for loop', 'code': 'for (let i = 0; i < array.length; i++) {\n    \n}\n'},
        ]
    }
    
    if os.path.exists(snippet_file):
        try:
            with open(snippet_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    return default_snippets.get(language, [])

# ============ Flask Routes ============

@app.route('/')
def index():
    """Landing page"""
    return render_template('landing.html')

@app.route('/room/<room_id>')
def room(room_id):
    """Code editor room"""
    create_room(room_id)
    return render_template('room.html', room_id=room_id)

# File operations
@app.route('/api/files/<room_id>')
def get_files(room_id):
    """List files in room"""
    return jsonify(list_files(room_id))

@app.route('/api/files/<room_id>/<path:filename>')
def get_file(room_id, filename):
    """Get file content"""
    content = get_file_content(room_id, filename)
    if content is None:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"content": content})
@app.route('/api/create_dir', methods=['POST'])
def api_create_dir():
    """Create new directory"""
    data = request.json
    room_id = data['room_id']
    dirname = data['dirname']
    
    path = os.path.join(get_room_path(room_id), dirname)
    
    if not is_safe_path(room_id, path):
        return jsonify({"success": False})
    
    try:
        os.makedirs(path, exist_ok=False)
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})
@app.route('/api/create_file', methods=['POST'])
def api_create_file():
    """Create new file"""
    data = request.json
    # Get language if provided, otherwise detect from filename
    language = data.get('language')
    content = ''
    if language and language in LANGUAGE_CONFIG and 'template' in LANGUAGE_CONFIG[language]:
        content = LANGUAGE_CONFIG[language]['template']
    success = create_new_file(data['room_id'], data['filename'], content)
    return jsonify({"success": success})

@app.route('/api/delete_file', methods=['POST'])
def api_delete_file():
    """Delete file"""
    data = request.json
    success = delete_file(data['room_id'], data['filename'])
    return jsonify({"success": success})

@app.route('/api/rename_file', methods=['POST'])
def api_rename_file():
    """Rename file"""
    data = request.json
    success = rename_file(data['room_id'], data['old_name'], data['new_name'])
    return jsonify({"success": success})

@app.route('/api/save_file', methods=['POST'])
def api_save_file():
    """Save file content"""
    data = request.json
    success = save_file_content(data['room_id'], data['filename'], data['content'])
    return jsonify({"success": success})

# Code execution
@app.route('/api/run', methods=['POST'])
def api_run_code():
    """Execute code"""
    data = request.json
    language = data.get('language', 'python')
    code = data.get('code', '')
    input_data = data.get('input', '')
    room_id = data.get('room_id')
    filename = data.get('filename')
    
    result = execute_code(language, code, input_data, room_id, filename)
    return jsonify(result)

# AI features
@app.route('/api/ai_chat', methods=['POST'])
def api_ai_chat():
    """AI chat interaction"""
    data = request.json
    response = ai_chat(
        provider=data.get('provider', 'gemini'),
        model=data.get('model', 'gemini-pro'),
        api_key=data.get('api_key'),
        prompt=data.get('prompt'),
        code_context=data.get('context'),
        task_type=data.get('task', 'chat')
    )
    return jsonify({"response": response})

@app.route('/api/analyze_code', methods=['POST'])
def api_analyze_code():
    """Analyze code complexity"""
    data = request.json
    analysis = analyze_code_complexity(data.get('code', ''), data.get('language', 'python'))
    suggestions = get_code_suggestions(data.get('code', ''), data.get('language', 'python'))
    return jsonify({
        "analysis": analysis,
        "suggestions": suggestions
    })

# Settings
@app.route('/api/settings/<room_id>')
def api_get_settings(room_id):
    """Get room settings"""
    return jsonify(get_room_settings(room_id))

@app.route('/api/settings/<room_id>', methods=['POST'])
def api_save_settings(room_id):
    """Save room settings"""
    settings = request.json
    success = save_room_settings(room_id, settings)
    return jsonify({"success": success})

# Snippets
@app.route('/api/snippets/<language>')
def api_get_snippets(language):
    """Get code snippets"""
    return jsonify(get_snippets(language))

# Language info
@app.route('/api/languages')
def api_get_languages():
    """Get supported languages"""
    languages = []
    for lang, config in LANGUAGE_CONFIG.items():
        languages.append({
            'name': lang,
            'extension': config['extension'],
            'ace_mode': config.get('ace_mode', lang),
            'executable': 'compile' in config or 'command' in config
        })
    return jsonify(languages)

# ============ WebSocket Events ============

@socketio.on('join')
def on_join(data):
    """User joins room"""
    username = data.get('username', 'Anonymous')
    room = data['room']
    join_room(room)
    
    if room not in room_users:
        room_users[room] = {}
    
    room_users[room][request.sid] = {
        'username': username,
        'cursor': {'row': 0, 'column': 0},
        'color': data.get('color', '#' + ''.join([f'{ord(c):02x}' for c in username[:3]]))
    }
    
    emit('user_joined', {
        'username': username,
        'users': [u['username'] for u in room_users[room].values()],
        'sid': request.sid
    }, room=room)
    
    emit('status', {
        'msg': f'{username} joined the room',
        'type': 'join'
    }, room=room)

@socketio.on('leave')
def on_leave(data):
    """User leaves room"""
    room = data.get('room')
    if room and room in room_users and request.sid in room_users[room]:
        username = room_users[room][request.sid]['username']
        del room_users[room][request.sid]
        leave_room(room)
        
        emit('user_left', {
            'username': username,
            'users': [u['username'] for u in room_users[room].values()],
            'sid': request.sid
        }, room=room)
        
        emit('status', {
            'msg': f'{username} left the room',
            'type': 'leave'
        }, room=room)

@socketio.on('code_change')
def on_code_change(data):
    """Code changed by user"""
    room = data['room']
    filename = data['file']
    content = data['content']
    
    # Auto-save
    if data.get('auto_save', True):
        save_file_content(room, filename, content)
    
    # Broadcast to others
    emit('update_code', {
        'file': filename,
        'content': content,
        'user': room_users.get(room, {}).get(request.sid, {}).get('username', 'Unknown')
    }, room=room, include_self=False)

@socketio.on('cursor_move')
def on_cursor_move(data):
    """Cursor position changed"""
    room = data['room']
    
    if room in room_users and request.sid in room_users[room]:
        room_users[room][request.sid]['cursor'] = data['cursor']
        
        emit('remote_cursor', {
            'sid': request.sid,
            'username': room_users[room][request.sid]['username'],
            'cursor': data['cursor'],
            'color': room_users[room][request.sid]['color']
        }, room=room, include_self=False)

@socketio.on('selection_change')
def on_selection_change(data):
    """Text selection changed"""
    room = data['room']
    
    emit('remote_selection', {
        'sid': request.sid,
        'selection': data['selection'],
        'username': room_users.get(room, {}).get(request.sid, {}).get('username', 'Unknown')
    }, room=room, include_self=False)

@socketio.on('chat_message')
def on_chat_message(data):
    """Chat message sent"""
    room = data['room']
    message = data['message']
    
    emit('chat_message', {
        'username': room_users.get(room, {}).get(request.sid, {}).get('username', 'Unknown'),
        'message': message,
        'timestamp': datetime.now().isoformat()
    }, room=room)

@socketio.on('terminal_input')
def on_terminal_input(data):
    """Terminal command input"""
    room = data['room']
    command = data['command']
    
    # Expanded safe commands list for better integration
    safe_commands = [
        'ls', 'dir', 'pwd', 'cd', 'echo', 'cat', 'grep', 'wc', 'head', 'tail', 
        'mkdir', 'rm', 'touch', 'mv', 'cp', 
        'python', 'python3', 'py', 'node', 'npm', 'npx',
        'java', 'javac', 'gcc', 'g++', 'go', 'cargo', 'rustc', 'ruby', 'php', 
        'git', 'pip', 'whoami', 'date'
    ]
    
    cmd_parts = command.strip().split()
    is_safe = False
    
    if cmd_parts:
        # Check if the command starts with one of the allowed programs (cross-platform friendly)
        base_cmd = os.path.basename(cmd_parts[0])
        # remove extension like .exe
        base_cmd = os.path.splitext(base_cmd)[0]
        
        if base_cmd in safe_commands or cmd_parts[0] in safe_commands:
            is_safe = True
            
    if is_safe:
        try:
            cwd = get_room_path(room)
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd
            )
            output = result.stdout + result.stderr
        except Exception as e:
            output = f"Error: {str(e)}"
    else:
        output = f"Command '{cmd_parts[0] if cmd_parts else ''}' not in allowed list."
    
    emit('terminal_output', {
        'output': output,
        'command': command
    }, room=room)

@socketio.on('disconnect')
def on_disconnect():
    """User disconnected"""
    for room, users in room_users.items():
        if request.sid in users:
            username = users[request.sid]['username']
            del users[request.sid]
            
            emit('user_left', {
                'username': username,
                'users': [u['username'] for u in users.values()],
                'sid': request.sid
            }, room=room)
            break

# ============ Main ============

if __name__ == '__main__':
    # Ensure directories exist
    ensure_dir(ROOMS_DIR)
    ensure_dir(SETTINGS_DIR)
    ensure_dir(SNIPPETS_DIR)
    
    print("=" * 60)
    print("CodeSync Pro - Enhanced Collaborative Code Editor")
    print("=" * 60)
    print("\nFeatures:")
    print("✓ Multi-language support (Python, JS, Java, C/C++, Go, Rust, etc.)")
    print("✓ Real-time collaboration")
    print("✓ Code execution with multiple languages")
    print("✓ AI-powered assistance (debugging, optimization, completion)")
    print("✓ Code analysis & complexity metrics")
    print("✓ File management (create, delete, rename)")
    print("✓ Customizable themes & settings")
    print("✓ Code snippets library")
    print("✓ Live cursors & selections")
    print("✓ Built-in chat")
    print("✓ Terminal support")
    print("\nStarting server on http://localhost:5000")
    print("=" * 60)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)