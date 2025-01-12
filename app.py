from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # Default ke port 5000 jika PORT kosong
    app.run(debug=False, host='0.0.0.0', port=port)
