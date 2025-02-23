from flask import Flask, request, jsonify
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
import os
import requests
from googletrans import Translator

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
    background_music_url = data.get("background_music_url", "")

    if not text or (not image_urls and not use_generated_images):
        return jsonify({"error": "Texto e imagens são obrigatórios"}), 400

    # Traduzir texto (opcional)
    translated_text = translate_text(text)

    # Gerar áudio
    audio_path = os.path.join(ASSETS_DIR, "audio.mp3")
    tts = gTTS(text=translated_text, lang='pt')
    tts.save(audio_path)

    # Gerar ou baixar imagens
    image_paths = []
    for i, image_url in enumerate(image_urls):
        image_path = os.path.join(ASSETS_DIR, f"image_{i}.jpg")
        if use_generated_images:
            image_url = generate_image(translated_text)
            if not image_url:
                return jsonify({"error": "Falha ao gerar imagem"}), 500
        with open(image_path, "wb") as f:
            f.write(requests.get(image_url).content)
        image_paths.append(image_path)

    # Criar vídeo
    video_clips = []
    audio_clip = AudioFileClip(audio_path)
    duration_per_image = audio_clip.duration / len(image_paths)

    for image_path in image_paths:
        img_clip = ImageClip(image_path).set_duration(duration_per_image)
        video_clips.append(img_clip)

    final_video = concatenate_videoclips(video_clips)
    final_video = final_video.set_audio(audio_clip)

    # Adicionar música de fundo
    if background_music_url:
        background_music_path = os.path.join(ASSETS_DIR, "background.mp3")
        with open(background_music_path, "wb") as f:
            f.write(requests.get(background_music_url).content)
        background_music = AudioFileClip(background_music_path).volumex(0.2)
        final_audio = CompositeAudioClip([audio_clip, background_music])
        final_video = final_video.set_audio(final_audio)

    video_path = os.path.join(ASSETS_DIR, "output.mp4")
    final_video.write_videofile(video_path, fps=24)

    return jsonify({"video_url": "/assets/output.mp4"})

if __name__ == '__main__':
    app.run(debug=True)