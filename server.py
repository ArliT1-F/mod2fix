from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
from pathlib import Path
import mod2fix

app = Flask(__name__)
CORS(app)

@app.route('/api/analyze', methods=['POST'])
def analyze_log():
    """Analyze crash log"""
    data = request.json
    log_content = data.get('log_content', '')
    
    analyzer = mod2fix.ModErrorAnalyzer()
    issues = analyzer.analyze_log(log_content)
    
    return jsonify({
        'success': True,
        'issues': issues
    })

@app.route('/api/scan-mods', methods=['POST'])
def scan_mods():
    """Scan mods folder"""
    # Handle uploaded mod files
    files = request.files.getlist('mods')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Save uploaded files
        for file in files:
            if file.filename.endswith('.jar'):
                file.save(tmp_path / file.filename)
        
        # Scan
        dep_checker = mod2fix.DependencyChecker()
        mods = dep_checker.scan_mods_folder(tmp_path)
        missing = dep_checker.check_dependencies(mods)
        
        return jsonify({
            'success': True,
            'mods': [asdict(mod) for mod in mods],
            'missing_dependencies': missing,
            'minecraft_version': dep_checker.minecraft_version,
            'loader': dep_checker.loader_type
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)