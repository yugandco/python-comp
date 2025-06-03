from flask import Flask, request, jsonify
import subprocess
import sys
import tempfile
import os
from flask_cors import CORS
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для React Native

@app.route('/api/execute', methods=['POST'])
def execute():
    logger.info("Received request to execute code")
    data = request.get_json()
    code = data.get('code')
    if not code or not isinstance(code, str):
        logger.error("Invalid code provided")
        return jsonify({'output': None, 'error': 'Код должен быть строкой'}), 400

    # Фильтрация опасных модулей
    dangerous_modules = ['os', 'sys', 'subprocess', 'shutil', 'socket']
    for module in dangerous_modules:
        if f'import {module}' in code or f'from {module}' in code:
            logger.warning(f"Attempted to import forbidden module: {module}")
            return jsonify({'output': None, 'error': f'Импорт модуля {module} запрещён'}), 403

    try:
        # Создаём временный файл для кода
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        logger.info(f"Created temp file: {temp_file_path}")

        # Выполняем код с таймаутом
        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        logger.info(f"Code executed with return code: {result.returncode}")

        # Удаляем временный файл
        os.unlink(temp_file_path)

        return jsonify({'output': result.stdout, 'error': result.stderr})
    except subprocess.TimeoutExpired:
        logger.error("Code execution timed out")
        return jsonify({'output': None, 'error': 'Превышен лимит времени выполнения (5 секунд)'}), 408
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        return jsonify({'output': None, 'error': str(e)}), 500
    finally:
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

if __name__ == '__main__':
    logger.info("Starting Flask server")
    app.run(host='0.0.0.0', port=5000)
