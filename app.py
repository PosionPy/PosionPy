from flask import Flask, request, render_template, redirect, url_for, flash
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

        fig.add_trace(go.Scatter(x=data["Time (sec)"], y=data["Intensity (cps)"],
                                 mode='lines', name=filename))
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

                # Round the time and area to 2 decimal places
                peak_time = round(data["Time (sec)"][peak], 2)

                # Use scientific notation for intensity and area if they exceed a threshold (e.g., 1e6)
                peak_intensity = data["Intensity (cps)"][peak]
                formatted_area = f"{ area_under_peak:.2e}" if  area_under_peak > 100000 else round(
                    area_under_peak, 2)

                # Format the annotation text
                text = f'Area: {formatted_area}'


                fig.add_annotation(
                    x=peak_time,
                    y=peak_intensity,
                    text=text,
                    showarrow=True,
                    arrowhead=2
                )



        fig.update_layout(title="Overlay of Selected Graphs",
                          xaxis_title="Time (sec)",
                          yaxis_title="Intensity (cps)",
                          showlegend=True)

    # Generate HTML for the plot
    graph_html = pyo.plot(fig, include_plotlyjs=False, output_type='div')

    return graph_html


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
