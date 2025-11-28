"""
API Flask Simples - Análise de Sentimentos
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db
from funcoes import cadastrar_analise, buscar_resultado

app = Flask(__name__)
CORS(app)

# Usuário padrão (simplificado)
USER_ID = 1


@app.route('/')
def home():
    """Info da API"""
    return jsonify({
        'sistema': 'Análise de Sentimentos',
        'funcoes': 3,
        'schemas': 2,
        'endpoints': [
            'POST /api/analyze',
            'GET /api/result/<id>',
            'GET /api/status'
        ]
    })


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    FUNÇÃO 1: Cadastrar análise
    Body: {"text": "seu texto aqui"}
    """
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'Campo "text" obrigatório'}), 400

    texto = data['text']

    if len(texto) < 3:
        return jsonify({'error': 'Texto muito curto'}), 400

    # Chama FUNÇÃO 1
    analysis_id = cadastrar_analise(USER_ID, texto)

    return jsonify({
        'message': 'Análise cadastrada',
        'analysis_id': analysis_id,
        'status': 'pending'
    }), 201


@app.route('/api/result/<analysis_id>', methods=['GET'])
def api_result(analysis_id):
    """
    FUNÇÃO 3: Buscar resultado
    """
    # Chama FUNÇÃO 3
    resultado = buscar_resultado(analysis_id)

    if not resultado:
        return jsonify({'error': 'Análise não encontrada'}), 404

    return jsonify({
        'analysis': resultado
    })


@app.route('/api/status')
def api_status():
    """Status do sistema"""
    from funcoes import fila_analises

    return jsonify({
        'sistema': 'online',
        'fila_pendente': fila_analises.qsize()
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Sistema de Análise de Sentimentos")
    print("="*60)
    print("📦 Inicializando banco de dados...")
    init_db()
    print("\n✅ Sistema pronto!")
    print("\n📡 API: http://localhost:5000")
    print("="*60 + "\n")

    app.run(debug=True, port=5000)
