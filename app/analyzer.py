import logging

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

class SceneAnalyzer:
    def __init__(self, model_name="openai/clip-vit-base-patch32", device=None):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        logging.info(f"Loading CLIP model: {model_name} on {self.device}")
        
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        
        self.positive_prompts = [
            "a photo of a person driving a car", 
            "view from inside a car", 
            "a person inside a car", 
            "driving a truck",
            "dashboard of a car",
            "steering wheel",
            "driver seat view"
        ]
        self.negative_prompts = [
            "a photo of an empty street",
            "a photo of a person walking",
            "a photo of a person outdoors",
            "a photo of a person indoors",
            "a forest",
            "a living room"
        ]
        
        # Pre-compute text features
        self.text_features = self._compute_text_features()
        
    def _compute_text_features(self):
        all_prompts = self.positive_prompts + self.negative_prompts
        inputs = self.processor(text=all_prompts, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
        return text_features / text_features.norm(dim=-1, keepdim=True)

    def analyze_batch(self, images):
        """
        Analyzes a batch of images.
        Returns a list of (pos_score, neg_score) tuples.
        """
        if not images:
            return []
            
        inputs = self.processor(images=images, return_tensors="pt", padding=True).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity (Raw Cosine Similarity)
            similarity = (image_features @ self.text_features.T)
            
            # Get scores for positive and negative categories
            positive_sims = similarity[:, :len(self.positive_prompts)]
            negative_sims = similarity[:, len(self.positive_prompts):]
            
            max_pos = positive_sims.max(dim=-1).values
            max_neg = negative_sims.max(dim=-1).values
            
            results = []
            for p, n in zip(max_pos, max_neg):
                results.append((p.item(), n.item()))
                
            return results

    def analyze_frame(self, frame_image: Image.Image):
        """
        Returns a score (0-1) indicating likelihood of being a target scene.
        """
        results = self.analyze_batch([frame_image])
        return results[0]
