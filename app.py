from flask import Flask, request, render_template, redirect, url_for, flash, logging
import os

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Display the index page without any file content initially
    return render_template('upload.html', file_content=None)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the file
        file.save(file_path)

        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        flash('File successfully uploaded')
        return render_template('upload.html', file_content=file_content)
    else:
        flash('Please upload a .txt file')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)