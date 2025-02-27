from flask import Flask, request, jsonify, make_response
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
import os
import requests
import logging
from googletrans import Translator

app = Flask(__name__)

# Configurar logs
logging.basicConfig(level=logging.INFO)

# Diretório para arquivos temporários
import tempfile
ASSETS_DIR = tempfile.mkdtemp()

# Middleware para adicionar cabeçalhos CORS
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"  # Permite qualquer origem
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# Tradução automática
def translate_text(text, target_lang="pt"):
    translator = Translator()
    translated = translator.translate(text, dest=target_lang)
    return translated.text

# Geração de imagens com IA (DALL·E Mini)
def generate_image(prompt):
    response = requests.post("https://bf.dallemini.ai/generate", json={"prompt": prompt})
    if response.status_code == 200:
        return response.json()["images"][0]
    return None

# Rota padrão
@app.route('/')
def home():
    return "Bem-vindo à API de Geração de Vídeos! Use a rota /generate-video para criar vídeos."

# Rota para gerar vídeo
@app.route('/generate-video', methods=['POST'])
def generate_video():
    data = request.json
    text = data.get("text", "")
    image_urls = data.get("image_urls", [])
    use_generated_images = data.get("use_generated_images", False)

    if not text or (not image_urls and not use_generated_images):
        logging.error("Texto ou imagens ausentes.")
        return jsonify({"error": "Texto e imagens são obrigatórios"}), 400

    try:
        logging.info("Iniciando geração de vídeo...")
        # Traduzir texto
        translated_text = translate_text(text)
        logging.info(f"Texto traduzido: {translated_text}")

        # Gerar áudio
        audio_path = os.path.join(ASSETS_DIR, "audio.mp3")
        tts = gTTS(text=translated_text, lang='pt')
        tts.save(audio_path)
        logging.info("Áudio gerado com sucesso.")

        # Baixar imagens
        image_paths = []
        for i, image_url in enumerate(image_urls):
            image_path = os.path.join(ASSETS_DIR, f"image_{i}.jpg")
            if use_generated_images:
                logging.info("Gerando imagem com IA...")
                image_url = generate_image(translated_text)
                if not image_url:
                    logging.error("Falha ao gerar imagem.")
                    return jsonify({"error": "Falha ao gerar imagem"}), 500
            logging.info(f"Baixando imagem {i} de URL: {image_url}")
            with open(image_path, "wb") as f:
                f.write(requests.get(image_url).content)
            image_paths.append(image_path)
        logging.info("Imagens baixadas com sucesso.")

        # Criar vídeo
        logging.info("Criando vídeo...")
        video_clips = []
        audio_clip = AudioFileClip(audio_path)
        duration_per_image = audio_clip.duration / len(image_paths)

        for image_path in image_paths:
            img_clip = ImageClip(image_path).set_duration(duration_per_image)
            video_clips.append(img_clip)

        final_video = concatenate_videoclips(video_clips)
        final_video = final_video.set_audio(audio_clip)
        video_path = os.path.join(ASSETS_DIR, "output.mp4")
        final_video.write_videofile(video_path, fps=24)
        logging.info("Vídeo gerado com sucesso.")

        # Retornar o vídeo como um arquivo binário
        return send_file(video_path, mimetype="video/mp4", as_attachment=True)
    except Exception as e:
        logging.error(f"Erro ao gerar vídeo: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Desativa o modo de depuração