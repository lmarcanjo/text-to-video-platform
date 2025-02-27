from flask import Flask, request, jsonify, send_file
import os
import logging
from gradio_client import Client
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from pydub.generators import Sine
from pydub import AudioSegment
import requests
import tempfile

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Diretório temporário
ASSETS_DIR = tempfile.mkdtemp()

# Middleware para CORS
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# Geração de imagens
def generate_image(prompt, style="realistic"):
    logging.info(f"Gerando imagem no estilo {style}...")
    try:
        client = Client("Wan-AI/Wan2.1")  # Substitua pelo espaço desejado
        result = client.predict(
            prompt=prompt,
            api_name="/predict"
        )
        if isinstance(result, str) and result.startswith("http"):
            logging.info("Imagem gerada com sucesso.")
            return result
        else:
            logging.error("Formato de resposta inesperado.")
            return None
    except Exception as e:
        logging.error(f"Falha ao gerar imagem: {str(e)}")
        return None

# Transformar imagem em 3D usando TRELLIS
def generate_3d_from_image(image_url):
    logging.info("Transformando imagem em 3D...")
    try:
        client = Client("JeffreyXiang/TRELLIS")
        result = client.predict(
            image=image_url,
            api_name="/generate_3d"
        )
        if isinstance(result, str) and result.startswith("http"):
            logging.info("Representação 3D gerada com sucesso.")
            return result
        else:
            logging.error("Formato de resposta inesperado.")
            return None
    except Exception as e:
        logging.error(f"Falha ao gerar 3D: {str(e)}")
        return None

# Geração de narração
def generate_narration(text, lang="pt"):
    logging.info("Gerando narração...")
    try:
        tts = gTTS(text=text, lang=lang)
        narration_path = os.path.join(ASSETS_DIR, "narration.mp3")
        tts.save(narration_path)
        logging.info("Narração gerada com sucesso.")
        return narration_path
    except Exception as e:
        logging.error(f"Falha ao gerar narração: {str(e)}")
        return None

# Criação de música simples
def generate_music(description, duration=60):
    logging.info("Gerando música...")
    try:
        sine_wave = Sine(440).to_audio_segment(duration=duration * 1000)  # Som de 440Hz (Lá)
        music_path = os.path.join(ASSETS_DIR, "music.mp3")
        sine_wave.export(music_path, format="mp3")
        logging.info("Música gerada com sucesso.")
        return music_path
    except Exception as e:
        logging.error(f"Falha ao gerar música: {str(e)}")
        return None

# Rota para gerar vídeo
@app.route('/generate-video', methods=['POST'])
def generate_video():
    try:
        logging.info("Recebendo requisição...")
        data = request.json
        script = data.get("script", "")
        style = data.get("style", "realistic")
        include_narration = data.get("include_narration", True)
        include_music = data.get("include_music", True)
        include_3d = data.get("include_3d", False)

        if not script:
            logging.error("Roteiro ausente.")
            return jsonify({"error": "Roteiro é obrigatório"}), 400

        logging.info("Dividindo roteiro em cenas...")
        scenes = script.split("\n\n")  # Cada cena é separada por duas quebras de linha
        image_paths = []
        audio_clips = []

        for i, scene in enumerate(scenes):
            logging.info(f"Processando cena {i + 1}: {scene}")

            # Gerar imagem para cada cena
            logging.info("Gerando imagem...")
            image_url = generate_image(scene, style=style)
            if not image_url:
                return jsonify({"error": "Falha ao gerar imagem"}), 500

            # Transformar imagem em 3D (opcional)
            if include_3d:
                logging.info("Transformando imagem em 3D...")
                image_url = generate_3d_from_image(image_url)
                if not image_url:
                    return jsonify({"error": "Falha ao gerar 3D"}), 500

            # Baixar imagem
            logging.info("Baixando imagem...")
            image_path = os.path.join(ASSETS_DIR, f"image_{i}.jpg")
            with open(image_path, "wb") as f:
                f.write(requests.get(image_url).content)
            image_paths.append(image_path)

            # Gerar narração (opcional)
            if include_narration:
                logging.info("Gerando narração...")
                narration_path = generate_narration(scene)
                audio_clip = AudioFileClip(narration_path)
                audio_clips.append(audio_clip)

        # Criar vídeo
        logging.info("Montando vídeo...")
        video_clips = []
        for i, image_path in enumerate(image_paths):
            img_clip = ImageClip(image_path).set_duration(audio_clips[i].duration if include_narration else 5)
            video_clips.append(img_clip)

        final_video = concatenate_videoclips(video_clips)
        final_audio = CompositeAudioClip(audio_clips) if include_narration else None

        # Adicionar música (opcional)
        if include_music:
            logging.info("Gerando música...")
            music_path = generate_music("música épica", duration=60)
            music_clip = AudioFileClip(music_path)
            final_audio = CompositeAudioClip([final_audio, music_clip]) if final_audio else music_clip

        logging.info("Renderizando vídeo final...")
        final_video = final_video.set_audio(final_audio)
        video_path = os.path.join(ASSETS_DIR, "output.mp4")
        final_video.write_videofile(video_path, fps=24)
        logging.info("Vídeo gerado com sucesso.")

        return send_file(video_path, mimetype="video/mp4", as_attachment=True)
    except Exception as e:
        logging.error(f"Erro ao gerar vídeo: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)