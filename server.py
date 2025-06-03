from flask import Flask, request, jsonify
import subprocess
import sys
import tempfile
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для React Native

@app.route('/api/execute', methods=['POST'])
def execute():
    data = request.get_json()
    code = data.get('code')
    if not code or not isinstance(code, str):
        return jsonify({'output': None, 'error': 'Код должен быть строкой'}), 400

    # Фильтрация опасных модулей
    dangerous_modules = ['os', 'sys', 'subprocess', 'shutil', 'socket']
    for module in dangerous_modules:
        if f'import {module}' in code or f'from {module}' in code:
            return jsonify({'output': None, 'error': f'Импорт модуля {module} запрещён'}), 403

    try:
        # Создаём временный файл для кода
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        # Выполняем код с таймаутом
        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=5  # Ограничение времени выполнения
        )

        # Удаляем временный файл
        os.unlink(temp_file_path)

        if result.returncode == 0:
            return jsonify({'output': result.stdout, 'error': result.stderr})
        else:
            return jsonify({'output': result.stdout, 'error': result.stderr or 'Неизвестная ошибка'})
    except subprocess.TimeoutExpired:
        return jsonify({'output': None, 'error': 'Превышен лимит времени выполнения (5 секунд)'}), 408
    except Exception as e:
        return jsonify({'output': None, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
