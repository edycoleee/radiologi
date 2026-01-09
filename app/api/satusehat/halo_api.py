# app/api/satusehat/halo_api.py

from flask_restx import Namespace, Resource

api = Namespace("halo", description="API sederhana untuk test koneksi")

@api.route("/")
class HaloResource(Resource):
    def get(self):
        return {"message": "Halo dari Flask API modular!"}, 200
