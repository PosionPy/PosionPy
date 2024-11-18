from flask import Flask, request, render_template, redirect, url_for, flash, logging
from werkzeug.utils import secure_filename

import pandas as pd
import plotly.express as px
import plotly.offline as pyo
import os


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_page():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    flash('No File Uploaded.')
    # Display the index page without any file content initially
    return render_template('upload.html', files=files)

@app.route('/graph')
def graph_page():
    filename = request.args.get('filename')
    if filename:
        graph_html = graph(filename)  # Generate the graph HTML
    else:
        flash('No file selected.')
        graph_html = None

    return render_template('graph.html', graph_html=graph_html)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('upload_page'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('upload_page'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the file
        file.save(file_path)
        return redirect(url_for('graph_page'))
    else:
        flash('Please upload a valid .txt file')
        return redirect(url_for('upload_page'))


def graph(filename):
    pd.set_option('display.precision', 18)

    # Get the uploaded file dynamically from the filename passed in the URL
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_path = str(file_path)

    # Read the file using pandas, adjusting as needed
    data = pd.read_csv(file_path, delim_whitespace=True, skiprows=4)
    data.columns = ["Time (sec)", "Intensity (cps)"]

    # Create the graph
    fig = px.line(data, x='Time (sec)', y='Intensity (cps)')
    graph_html = pyo.plot(fig, include_plotlyjs=False, output_type='div')

    return graph_html


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)