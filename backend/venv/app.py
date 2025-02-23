from flask import Flask, request, jsonify
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, CompositeAudioClip
import os
import requests
from googletrans import Translator
from transformers import pipeline

app = Flask(__name__)

# Diretório para arquivos temporários
ASSETS_DIR = "../assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

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

@app.route('/generate-video', methods=['POST'])
def generate_video():
    data = request.json
    text = data.get("text", "")
    image_url = data.get("image_url", "")
    use_generated_image = data.get("use_generated_image", False)

    if not text:
        return jsonify({"error": "Texto é obrigatório"}), 400

    # Traduzir texto (opcional)
    translated_text = translate_text(text)

    # Gerar áudio
    audio_path = os.path.join(ASSETS_DIR, "audio.mp3")
    tts = gTTS(text=translated_text, lang='pt')
    tts.save(audio_path)

    # Gerar ou baixar imagem
    image_path = os.path.join(ASSETS_DIR, "image.jpg")
    if use_generated_image:
        image_url = generate_image(translated_text)
        if not image_url:
            return jsonify({"error": "Falha ao gerar imagem"}), 500
    with open(image_path, "wb") as f:
        f.write(requests.get(image_url).content)

    # Criar vídeo
    video_path = os.path.join(ASSETS_DIR, "output.mp4")
    audio_clip = AudioFileClip(audio_path)
    img_clip = ImageClip(image_path).set_duration(audio_clip.duration)
    video = img_clip.set_audio(audio_clip)
    video.write_videofile(video_path, fps=24)

    return jsonify({"video_url": "/assets/output.mp4"})

if __name__ == '__main__':
    app.run(debug=True)