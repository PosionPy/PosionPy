import io
import zipfile

from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename

import pandas as pd
import plotly.offline as pyo
from scipy.signal import find_peaks
import plotly.graph_objects as go
import numpy as np
import os


app = Flask(__name__, static_url_path='/static')
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
    # Display the index page without any file content initially
    return render_template('upload.html', files=files)

@app.route('/team')
def team():
    team_data = [
        {
            "name": "Natalie Oulman",
            "major": "Computer Science",
            "github": "https://github.com/natalieoulman",
            "description": "I'm a passionate developer working on web apps by day and a wannabe bartender by night. I also sneak in as much CK3 time as possible."
        },
        {
            "name": "Jonathan Thang",
            "major": "Major",
            "github": "https://github.com/jonathanthang",
            "description": "Placeholder"
        },
        {
            "name": "Simon Saltikov",
            "major": "Major",
            "github": "https://github.com/simonsaltikov",
            "description": "Placeholder"
        },
        {
            "name": "Samuel Hodgdon",
            "major": "Major",
            "github": "https://github.com/samuelhodgdon",
            "description": "Placeholder"
        },
    ]
    return render_template('team.html', team_data=team_data)


# def delete_files():
#
# def download_files():
@app.route('/handle_files', methods=['POST'])
def handle_files():
    selected_files = request.form.getlist('selected_files')
    action = request.form.get('action')

    if not selected_files:
        flash('No files selected.', 'error')
        return redirect(url_for('upload_page'))

    # Handle file deleting
    if action == 'delete':
        for filename in selected_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        flash(f"{len(selected_files)} files deleted.", "success")

    # Handle file graphing
    elif action == 'graph':
        return redirect(url_for('graph_page', selected_files=selected_files))

    # Handle file download
    elif action == 'download':
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in selected_files:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                if os.path.exists(file_path):
                    zip_file.write(file_path, arcname=file)
                else:
                    flash(f'File {file} does not exist and was not added to the zip.', 'error')
        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True, download_name='selected_files.zip', mimetype='application/zip')

    else:
        flash("Invalid action.", "error")

    # Redirect back to the upload page after processing
    return redirect(url_for('upload_page'))

@app.route('/graph')
def graph_page():
        # Get selected files from the form submission
        selected_files = request.args.getlist('selected_files')

        # If no files are selected, flash a message and redirect back to the upload page
        if request.method == 'GET' and not selected_files:
            flash('No files selected. Please select at least one file.', 'error')
            return redirect(url_for('upload_page'))

        # Pass the selected files to the graph function
        graph_html = graph(selected_files)
        return render_template('graph.html', graph_html=graph_html)


@app.route('/upload', methods=['POST'])
def upload_file():

    if 'file' not in request.files:
        # print("File key missing in request.files")
        flash('No file part', 'error')
        return redirect(url_for('upload_page'))

    file = request.files['file']
    # print(f"Uploaded filename: {file.filename}")
    if file.filename == '':
        # print("Filename is empty")
        flash('No selected file.', 'error')
        return redirect(url_for('upload_page'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the file
        file.save(file_path)
        flash(f'Uploaded {filename} successfully.', 'success')
        return redirect(url_for('upload_page'))
    else:
        flash('Please upload a valid .txt file', 'error')
        return redirect(url_for('upload_page'))


def graph(files):
    fig = go.Figure()

    for filename in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_path = str(file_path)

        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        data = pd.read_csv(file_path, sep='\s+', skiprows=4)
        data.columns = ["Time (sec)", "Intensity (cps)"]

        peaks, _ = find_peaks(data["Intensity (cps)"], height=200000, distance=50)

        areas = []
        for peak in peaks:
            # Only annotate peaks with intensity > 100 (and avoid peak at 0 or very close to 0)
            if data["Intensity (cps)"][peak] > 100 and data["Time (sec)"][peak] > 0.1:  # Avoid near-zero times
                # Identify the region around the peak for integration
                left_idx = peak - 10 if peak - 10 >= 0 else 0  # 10 data points before peak
                right_idx = peak + 10 if peak + 10 < len(data) else len(data) - 1  # 10 data points after peak

                # Slice the data to the region around the peak
                x_peak_region = data["Time (sec)"][left_idx:right_idx + 1]
                y_peak_region = data["Intensity (cps)"][left_idx:right_idx + 1]

                # Calculate the area under the peak using the trapezoidal rule
                area_under_peak = np.trapezoid(y_peak_region, x_peak_region)
                areas.append((filename,f"{area_under_peak:.2f}"))
            else:
                areas.append((filename, "none"))

        area = "none"
        for area_tuple in areas:
            key, value = area_tuple
            if key == filename:
                area = value
                break

        # Add the trace for the line
        fig.add_trace(go.Scatter(
            x=data["Time (sec)"],
            y=data["Intensity (cps)"],
            mode='lines',
            name=filename.split('.')[0],
            hovertemplate='<b>Time</b>: %{x}<br>' +
                          '<b>Intensity</b>: %{y}<br>' +
                          '<b>Area</b>: ' + area,
        ))

        fig.update_layout(
            hovermode='closest',
            title="Overlay of Selected Graphs",
            xaxis_title="Time (sec)",
            yaxis_title="Intensity (cps)",
            showlegend=True,
            legend=dict(
                orientation='h',
                x=0.5,
                xanchor='center',
                y=-0.35,
                yanchor='bottom',
                font=dict(
                    size=13
                ),
                traceorder='normal',
            ),
            title_font_size=22,
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(
                tickfont=dict(size=12),
                range=[0, 280]
            ),
            yaxis=dict(tickfont=dict(size=12)),
        )


    graph_html = pyo.plot(fig, include_plotlyjs=False, output_type='div')

    return graph_html




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
