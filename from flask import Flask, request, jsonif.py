from flask import Flask, jsonify, request

app = Flask(__name__)

# Simula uma base de dados em memória para armazenar os leads capturados
leads = set()


@app.route("/api/interesse", methods=["POST"])
def registrar_interesse():
  dados = request.get_json() or {}
  email = dados.get("email", "").strip()

  if not email or "@" not in email or "." not in email.split("@")[-1]:
    return (
        jsonify({
            "status": "erro",
            "mensagem": "E-mail inválido. Por favor, insira um e-mail válido.",
        }),
        400,
    )

  if email in leads:
    return (
        jsonify({
            "status": "aviso",
            "mensagem": "Este e-mail já está cadastrado.",
            "total_cadastrados": len(leads),
        }),
        200,
    )

  leads.add(email)
  return (
      jsonify({
          "status": "sucesso",
          "mensagem": "E-mail cadastrado com sucesso!",
          "total_cadastrados": len(leads),
      }),
      201,
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)