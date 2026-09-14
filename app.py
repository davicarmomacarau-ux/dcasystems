from flask import Flask, jsonify, request, Response, render_template, redirect
from database import BancoDados
from legacy_parser import parse_legacy_sample

app = Flask(__name__)

# Instancia a camada de persistência PostgreSQL do MVP bancário.
banco = BancoDados()


def init_db():
    """Inicializa o PostgreSQL e cria a tabela leads no momento de inicio do servidor."""
    try:
        banco.inicializar()
        return True
    except RuntimeError as erro:
        # Em execução como rotina de teste, devolve um erro simples sem exigir contexto Flask ativo.
        if app:
            try:
                return jsonify({"status": "erro", "mensagem": str(erro)}), 500
            except Exception:
                return False
        return False


@app.route("/", methods=["GET"])
def raiz():
    """Rota raiz do produto: leva o navegador para a interface HTML principal do MVP."""
    return redirect("/interface")


@app.route("/interface", methods=["GET"])
def interface():
    """Entrega a interface HTML básica do MVP bancário legado."""
    return render_template("interface.html")


@app.route("/sw.js", methods=["GET"])
def service_worker_placeholder():
    """Rota de compatibilidade para evitar ruido de 404 em navegação local com service worker."""
    return Response("console.log('DCA Systems API service worker stub');", mimetype="application/javascript")


@app.route("/api/interesse", methods=["POST"])
def registrar_interesse():
    """Endpoint original do MVP de captação de interesse, agora persistido em PostgreSQL."""
    try:
        dados = request.get_json(silent=True) or {}
        email = dados.get("email", "").strip()

        if not email or "@" not in email or "." not in email.split("@")[-1]:
            return (
                jsonify({
                    "status": "erro",
                    "mensagem": "E-mail inválido. Por favor, insira um e-mail válido.",
                }),
                400,
            )

        if banco.existe(email):
            return (
                jsonify({
                    "status": "aviso",
                    "mensagem": "Este e-mail já está cadastrado.",
                    "total_cadastrados": banco.contar(),
                }),
                200,
            )

        resultado = banco.cadastrar(email)
        return (
            jsonify({
                "status": "sucesso",
                "mensagem": resultado["mensagem"],
                "total_cadastrados": banco.contar(),
            }),
            201,
        )
    except RuntimeError as erro:
        # Tratamento de exceções de banco em cada rota com resposta JSON legível.
        return jsonify({"status": "erro", "mensagem": str(erro)}), 500
    except Exception as erro:
        # Captura qualquer falha inesperada de request no endpoint de cadastro.
        return jsonify({"status": "erro", "mensagem": f"Falha inesperada: {erro}"}), 500


@app.route("/api/leads", methods=["GET"])
def listar_leads():
    """Lista todos os leads cadastrados no PostgreSQL, ordenados pelo mais recente primeiro."""
    try:
        linhas = banco.listar_todos()
        return jsonify({
            "leads": [linha["email"] for linha in linhas],
            "total_cadastrados": len(linhas),
            "ordenacao": "created_at DESC",
        }), 200
    except RuntimeError as erro:
        return jsonify({"status": "erro", "mensagem": str(erro)}), 500
    except Exception as erro:
        return jsonify({"status": "erro", "mensagem": f"Falha inesperada: {erro}"}), 500


@app.route("/api/migrar-amostra", methods=["POST"])
def migrar_amostra():
    """Recebe uma string de dados legados e devolve o payload convertido, com saldo decimal e status interpretado."""
    try:
        # Suporta JSON natural com {"dados_legados": "..."} e também texto bruto como string.
        dados = request.get_json(silent=True)
        if dados is None:
            dados = {}
            texto_legado = request.get_data(as_text=True)
            if texto_legado:
                dados = {"dados_legados": texto_legado}

        texto_legado = dados.get("dados_legados") if isinstance(dados, dict) else None
        if not texto_legado:
            return jsonify({"status": "erro", "mensagem": "Campo dados_legados é obrigatório."}), 400

        payload = parse_legacy_sample(texto_legado)
        return jsonify(payload), 200
    except ValueError as erro:
        # Trata falhas de formato de string legado com resposta controlada em JSON.
        return jsonify({"status": "erro", "mensagem": str(erro)}), 400
    except Exception as erro:
        # Garante resposta consistente para JSON inválido ou outra falha inesperada.
        return jsonify({"status": "erro", "mensagem": f"Falha inesperada: {erro}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint simples para checagem de disponibilidade da aplicação e do banco PostgreSQL."""
    try:
        banco.contar()
        return jsonify({"status": "ok", "database": "sqlite"}), 200
    except RuntimeError as erro:
        return jsonify({"status": "erro", "mensagem": str(erro)}), 500


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    """Rota de favicon para evitar ruído de 404 em páginas de navegador."""
    return app.send_static_file("favicon.svg")


# Chamada de inicialização do PostgreSQL antes do servidor levantar.
try:
    init_db()
except Exception:
    pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)