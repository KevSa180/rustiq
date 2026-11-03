from flask import Flask

app = Flask(__name__)

@app.route("/")
def inicio():
    return "Hola, el servidor de RustiQ funciona"

if __name__ == "__main__":
    app.run(port=5001, debug=True)
