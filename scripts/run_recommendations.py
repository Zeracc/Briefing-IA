from app.services.ai_services import gerar_recomendacoes

texto = "Transcrição de exemplo: a pessoa pede para revisar o cronograma e destacar 3 ações principais."
print("Chamando gerar_recomendacoes()...")
resultado = gerar_recomendacoes(texto)
print("Resultado:")
print(resultado)