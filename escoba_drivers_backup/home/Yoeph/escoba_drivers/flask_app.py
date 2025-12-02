from flask import Flask, send_from_directory

# This app serves the static files (index.html, style.css, script.js)
# from the current directory.

app = Flask(__name__, static_url_path='', static_folder='.')

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

if __name__ == "__main__":
    app.run()
