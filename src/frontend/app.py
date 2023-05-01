from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# retrieve page
@app.route('/retrieve', methods=['GET'])
def retrieve():
    return render_template('ret.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    filename = uploaded_file.filename
    # Save the file to disk
    uploaded_file.save(filename)
    # Run the Python script
    print(open(filename).read())
    return 'File uploaded and processed successfully.'

if __name__ == '__main__':
    app.run(debug=True)