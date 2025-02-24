const imageUpload = document.getElementById("imageUpload");
const useGeneratedImages = document.getElementById("useGeneratedImages");
const loading = document.getElementById("loading");
const videoOutput = document.getElementById("videoOutput");

async function generateVideo() {
    const text = document.getElementById("textInput").value;
    const imageFiles = Array.from(imageUpload.files);
    const useGenerated = useGeneratedImages.checked;

    if (!text || (!imageFiles.length && !useGenerated)) {
        alert("Por favor, insira texto e imagens ou habilite a geração automática.");
        return;
    }

    loading.style.display = "block";

    const imageUrls = imageFiles.map(file => URL.createObjectURL(file));

    const response = await fetch("https://text-to-video-platform.onrender.com/generate-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            text,
            image_urls: imageUrls,
            use_generated_images: useGenerated,
        }),
    });

    const data = await response.json();
    loading.style.display = "none";

    if (data.video_url) {
        videoOutput.src = data.video_url;
        videoOutput.style.display = "block";
    } else {
        alert("Erro ao gerar vídeo: " + data.error);
    }
}