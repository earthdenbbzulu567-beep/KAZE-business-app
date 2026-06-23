from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string('''
        <h1>Hello, World!</h1>
        <p>This is my first web app.</p>
    ''')

if __name__ == '__main__':
    app.run(debug=True)