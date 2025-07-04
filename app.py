import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
import google.generativeai as genai
import json
import time
import requests
from dotenv import load_dotenv
load_dotenv()
import eventlet
eventlet.monkey_patch()


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load environment variablesapp.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

JDOODLE_CLIENT_ID = os.getenv('JDOODLE_CLIENT_ID')
JDOODLE_CLIENT_SECRET = os.getenv('JDOODLE_CLIENT_SECRET')
JDOODLE_API_URL = os.getenv('JDOODLE_API_URL')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

genai.configure(api_key=GEMINI_API_KEY)

rooms = {}

language_templates = {
    'python': 'def hello_world():\n    print("Hello, World!")\n\nhello_world()',
    'javascript': 'function helloWorld() {\n    console.log("Hello, World!");\n}\n\nhelloWorld();',
    'java': 'public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}',
    'c': '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}',
    'cpp': '#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}',
    'go': 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}',
    'rust': 'fn main() {\n    println!("Hello, World!");\n}',
}

def get_language_from_extension(filename):
    extension = filename.split('.')[-1].lower()
    extension_map = {
        'py': 'python',
        'js': 'javascript',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'cc': 'cpp',
        'cxx': 'cpp',
        'go': 'go',
        'rs': 'rust'
    }
    return extension_map.get(extension, 'python')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/editor/<room_id>')
def editor(room_id):
    return render_template('editor.html', room_id=room_id)

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    username = data['username']
    join_room(room_id)

    if room_id not in rooms:
        rooms[room_id] = {
            'users': {},
            'files': {
                'main.py': {
                    'content': language_templates['python'],
                    'language': 'python'
                }
            },
            'active_file': 'main.py'
        }
    
    rooms[room_id]['users'][request.sid] = username
    emit('room_state', rooms[room_id], room=room_id)
    emit('user_joined', f'{username} has joined the room.', room=room_id, include_self=False)

@socketio.on('code_change')
def handle_code_change(data):
    room_id = data['room_id']
    file_name = data['file_name']
    if room_id in rooms and file_name in rooms[room_id]['files']:
        rooms[room_id]['files'][file_name]['content'] = data['code']
        emit('code_update', data, room=room_id, include_self=False)

@socketio.on('create_file')
def handle_create_file(data):
    room_id = data['room_id']
    file_name = data['file_name']
    language = get_language_from_extension(file_name)
    
    if room_id in rooms and file_name not in rooms[room_id]['files']:
        rooms[room_id]['files'][file_name] = {
            'content': language_templates.get(language, ''),
            'language': language
        }
        rooms[room_id]['active_file'] = file_name
        emit('room_state', rooms[room_id], room=room_id)
        emit('file_created', {'file_name': file_name, 'language': language}, room=room_id)

@socketio.on('switch_file')
def handle_switch_file(data):
    room_id = data['room_id']
    file_name = data['file_name']
    if room_id in rooms and file_name in rooms[room_id]['files']:
        rooms[room_id]['active_file'] = file_name
        emit('room_state', rooms[room_id], room=room_id)

@socketio.on('execute_code')
def handle_execute_code(data):
    room_id = data['room_id']
    file_name = data['file_name']

    if room_id in rooms and file_name in rooms[room_id]['files']:
        current_file = rooms[room_id]['files'][file_name]
        code_to_run = current_file['content']
        language = current_file['language']

        language_map = {
            'python': ('python3', '4'),
            'javascript': ('nodejs', '4'),
            'java': ('java', '4'),
            'c': ('c', '5'),
            'cpp': ('cpp17', '1'),
            'go': ('go', '4'),
            'rust': ('rust', '4')
        }
        
        if language not in language_map:
            emit('code_output', {'output': f'Language {language} not supported'})
            return
            
        jdoodle_lang, version_index = language_map[language]

        payload = {
            'clientId': JDOODLE_CLIENT_ID,
            'clientSecret': JDOODLE_CLIENT_SECRET,
            'script': code_to_run,
            'language': jdoodle_lang,
            'versionIndex': version_index
        }
        
        try:
            response = requests.post(JDOODLE_API_URL, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            output = result.get('output', 'No output')
            if result.get('statusCode') == 200:
                emit('code_output', {'output': output})
            else:
                emit('code_output', {'output': f"Error: {result.get('error', 'Unknown error')}"})
        except requests.exceptions.Timeout:
            emit('code_output', {'output': 'Error: Request timeout'})
        except Exception as e:
            emit('code_output', {'output': f"Error: {str(e)}"})
@socketio.on('delete_file')
def handle_delete_file(data):
    room_id = data['room_id']
    file_name = data['file_name']
    if room_id in rooms and file_name in rooms[room_id]['files']:
        if len(rooms[room_id]['files']) > 1:
            del rooms[room_id]['files'][file_name]
            if rooms[room_id]['active_file'] == file_name:
                rooms[room_id]['active_file'] = list(rooms[room_id]['files'].keys())[0]
            emit('room_state', rooms[room_id], room=room_id)
        else:
            emit('error_message', {'message': 'Cannot delete the last file'})

@socketio.on('rename_file')
def handle_rename_file(data):
    room_id = data['room_id']
    old_name = data['old_name']
    new_name = data['new_name']
    if room_id in rooms and old_name in rooms[room_id]['files'] and new_name not in rooms[room_id]['files']:
        rooms[room_id]['files'][new_name] = rooms[room_id]['files'][old_name]
        del rooms[room_id]['files'][old_name]
        if rooms[room_id]['active_file'] == old_name:
            rooms[room_id]['active_file'] = new_name
        emit('room_state', rooms[room_id], room=room_id)

@socketio.on('duplicate_file')
def handle_duplicate_file(data):
    room_id = data['room_id']
    file_name = data['file_name']
    if room_id in rooms and file_name in rooms[room_id]['files']:
        base_name = file_name.split('.')[0]
        extension = file_name.split('.')[-1] if '.' in file_name else ''
        new_name = f"{base_name}_copy.{extension}" if extension else f"{base_name}_copy"
        
        counter = 1
        while new_name in rooms[room_id]['files']:
            new_name = f"{base_name}_copy{counter}.{extension}" if extension else f"{base_name}_copy{counter}"
            counter += 1
        
        rooms[room_id]['files'][new_name] = rooms[room_id]['files'][file_name].copy()
        rooms[room_id]['active_file'] = new_name
        emit('room_state', rooms[room_id], room=room_id)

@socketio.on('chat_message')
def handle_chat_message(data):
    room_id = data['room_id']
    message = data['message']
    username = rooms.get(room_id, {}).get('users', {}).get(request.sid, 'A user')
    
    if message.strip().lower().startswith('/ai'):
        prompt = message.strip()[3:].strip()
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            ai_message = {"username": "Gemini AI", "message": response.text}
            emit('new_chat_message', ai_message, room=room_id)
        except Exception as e:
            error_message = {"username": "Gemini AI", "message": f"Error: {e}"}
            emit('new_chat_message', error_message, room=room_id)
    else:
        chat_message = {"username": username, "message": message}
        emit('new_chat_message', chat_message, room=room_id)

@socketio.on('get_code_suggestion')
def handle_get_suggestion(data):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"you are a ai assistant at my collabrative code editor website so Provide a code suggestion for the following {data['language']} code:\n\n```\n{data['code']}\n``` only provide neccessary usefull things only nothing extra"
        response = model.generate_content(prompt)
        emit('code_suggestion', {'suggestion': response.text})
    except Exception as e:
        emit('code_suggestion', {'suggestion': f"Error: {e}"})

@socketio.on('ai_code_review')
def handle_ai_code_review(data):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"you are a ai assistant at my collabrative code editor website so Review this {data['language']} code and provide suggestions:\n\n```\n{data['code']}\n```only provide neccessary usefull things only nothing extra"
        response = model.generate_content(prompt)
        emit('ai_response', {'type': 'code_review', 'content': response.text})
    except Exception as e:
        emit('ai_response', {'type': 'error', 'content': f"Error: {e}"})

@socketio.on('ai_explain_code')
def handle_ai_explain_code(data):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"you are a ai assistant at my collabrative code editor website so Explain this {data['language']} code:\n\n```\n{data['code']}\n``` only provide neccessary usefull things only nothing extra"
        response = model.generate_content(prompt)
        emit('ai_response', {'type': 'explanation', 'content': response.text})
    except Exception as e:
        emit('ai_response', {'type': 'error', 'content': f"Error: {e}"})

@socketio.on('ai_generate_code')
def handle_ai_generate_code(data):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"you are a ai assistant at my collabrative code editor website so Generate {data['language']} code for: {data['description']} only provide neccessary usefull things only nothing extra"
        response = model.generate_content(prompt)
        emit('ai_response', {'type': 'code_generation', 'content': response.text})
    except Exception as e:
        emit('ai_response', {'type': 'error', 'content': f"Error: {e}"})

@socketio.on('disconnect')
def handle_disconnect():
    for room_id, room_data in rooms.items():
        if request.sid in room_data['users']:
            username = room_data['users'].pop(request.sid)
            emit('user_left', f'{username} has left the room.', room=room_id)
            emit('room_state', rooms[room_id], room=room_id)
            break
@socketio.on('file_created')
def handle_file_created(data):
    pass
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
