from flask import Flask, request, render_template, redirect, url_for, flash
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    # Display the index page without any file content initially
    return render_template('upload.html', file_content=None)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and file.filename.endswith('.txt'):
        # Read the content of the file
        file_content = file.read().decode('utf-8')  # Decode bytes to a string
        flash('File successfully uploaded')
        return render_template('upload.html', file_content=file_content)
    else:
        flash('Please upload a .txt file')
        return redirect(request.url)


if __name__ == '__main__':
    app.run(debug=True)
