from flask import Flask, render_template, Blueprint

# Create main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    from routes.analysis import analysis_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 