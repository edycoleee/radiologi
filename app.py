from flask import Flask, render_template
from flask_restx import Api
from config import Config
from satusehat import satset_ns

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Init folder temp
    Config.init_app()

    api = Api(
        app,
        version="1.1",
        title="Satu Sehat Gateway",
        doc="/api/docs",
        prefix="/api",
    )

    # Register namespace
    api.add_namespace(satset_ns)

    return app

app = create_app()

@app.route("/")
def index():
    return render_template("page.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
