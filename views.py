from flask import Flask, render_template, jsonify

class BasicRoutes:
    def __init__(self, app: Flask):
        self.app = app
        self.register_routes()

    def register_routes(self):
        @self.app.route('/')
        def home():
            return "<h1>Welcome to Flask OOP!</h1>"

        @self.app.route('/api/data')
        def get_data():
            data = {
                'message': 'Hello, this is a simple Flask API using OOP!',
                'status': 'success'
            }
            return jsonify(data)

        @self.app.route('/about')
        def about():
            return render_template('about.html')