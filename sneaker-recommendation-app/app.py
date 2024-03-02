import vertexai
import streamlit as st
from vertexai.generative_models import GenerativeModel
from PIL import Image as PIL_Image
import io
import json
from google.cloud import storage

# Initialize Vertex AI
PROJECT_ID = ""
LOCATION = "us-central1"
bucket_name = ""
vertexai.init(project=PROJECT_ID, location=LOCATION)

multimodal_model = GenerativeModel("gemini-1.0-pro-vision")

def display_image_from_gcs(image_path: str):
    """Download an image from Google Cloud Storage and display it."""
    try:
        client = storage.Client()
        bucket_name = "llm-demo-v1"
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(image_path)
        image_bytes = blob.download_as_bytes()

        # Display the image
        st.image(image_bytes, caption='Recommended Sneaker', use_column_width=True)

    except Exception as e:
        st.error(f"An error occurred while displaying the image from Google Cloud Storage: {str(e)}")

def load_image_from_upload(uploaded_file):
    """Load an image from upload."""
    try:
        pil_image = PIL_Image.open(uploaded_file)
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Save the image to a BytesIO object
        img_byte_arr = io.BytesIO()

        # Manually map accepted file extensions to PIL formats
        file_extension = uploaded_file.name.split(".")[-1].lower()
        pil_format = {
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "png": "PNG"
        }.get(file_extension, "JPEG")  # Default to JPEG if format not recognized

        pil_image.save(img_byte_arr, format=pil_format)
        img_byte_arr = img_byte_arr.getvalue()

        return vertexai.generative_models.Image.from_bytes(img_byte_arr)
    
    except Exception as e:
        st.error(f"An error occurred while processing the uploaded image: {str(e)}")


def load_image_from_gcs(bucket_name: str, blob_name: str) -> 'Image':
    """Load an image from Google Cloud Storage into the format expected by Vertex AI."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    image_bytes = blob.download_as_bytes()
    
    pil_image = PIL_Image.open(io.BytesIO(image_bytes))
    pil_image_rgb = pil_image.convert("RGB")
    
    img_byte_arr = io.BytesIO()
    pil_image_rgb.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return vertexai.generative_models.Image.from_bytes(img_byte_arr)

def main():
    st.set_page_config(page_title="Sneaker Recommendation App", page_icon=":sneakers:")
    st.title("Sneaker Recommendation App")

    st.sidebar.title("Enter your preferences")
    user_input_prompt = st.sidebar.text_area("Type your request", key="user_input_prompt").strip()    
    st.sidebar.title("Upload Image")

    # Upload image
    uploaded_file = st.sidebar.file_uploader("Upload an image", type=["jpg", "png", "jpeg"], accept_multiple_files=False, key="fileuploader")
    if uploaded_file is not None:
        st.sidebar.image(uploaded_file, caption='Uploaded Image', use_column_width=True)

        # Display loading spinner while processing
        with st.spinner('Processing...'):
            input_image = load_image_from_upload(uploaded_file)

            prompt = "Describe just the tshirt,shirt,trousers or jeans in the picture briefly"
            contents = [prompt, input_image]
            responses = multimodal_model.generate_content(contents, stream=True)

            # Display uploaded image description
            st.write("<h3>Uploaded Image Description:</h3>", unsafe_allow_html=True)
            for response in responses:
                st.write(f'<div class="image-description">{response.text}</div>', unsafe_allow_html=True)

            sneaker_image_paths = [
                "sneaker-collections/nike1.jpg",
                "sneaker-collections/nike2.jpg",
                "sneaker-collections/nike3.jpg",
                "sneaker-collections/nike4.jpg",
                "sneaker-collections/nike5.jpg",
                "sneaker-collections/adidas1.png",
                "sneaker-collections/adidas2.png",
                "sneaker-collections/adidas3.png",
                "sneaker-collections/adidas4.png",
                "sneaker-collections/adidas5.png"   
            ]

            sneaker_images = [load_image_from_gcs(bucket_name, path) for path in sneaker_image_paths]

            instructions_prompt = f"""Fetch the colors and the product price first.Then, only select 3 to 4 products 
                that match the user preferences.If no products match the user preference or budget, then say "Sorry, we do not have 
                products matching your preferences".Think step by step before responding and only select from the available products and their prices.
                Respect the budget and the color preferences of the user before responding.
                The User says : "{user_input_prompt}"
                """

            output_prompt = """
                        Output Format:
                            1: Respond in json with 2 keys explanation and image_path.
                            2: explanation must be your response to the above user request strictly matching their preferences
                            and image_path must be the path of the product images that you have chosen. 
                            3: Output Format must be strictly a json string in the below format with no illegal string terminations
                            and must be inside quotes. For example : "{{'explanation':'','image_paths':''}}"
                            Pay attention to the user preferences before responding.
                            """

            contents = [
                "Consider the following sneakers:",
                "Nike Air Max 1:",
                sneaker_images[0],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/nike1.jpg",
                "Nike Air max SC:",
                sneaker_images[1],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/nike2.jpg",
                "Nike Air Max 1 Black:",
                sneaker_images[2],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/nike3.jpg",
                "Nike Dunk Low Retro- White:",
                sneaker_images[3],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/nike4.jpg",
                "Nike Dunk Low Retro- Black:",
                sneaker_images[4],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/nike5.jpg",
                "Adidas-Sambda OG Shoes:",
                sneaker_images[5],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/adidas1.png",
                "Adidas-Rivalry Hi shoes:",
                sneaker_images[6],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/adidas2.png",
                "Adidas-Ultrabounce Shoes:",
                sneaker_images[7],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/adidas3.png",
                "Adidas-Courtblock shoes:",
                sneaker_images[8],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/adidas4.png",
                "Adidas-Stan Smith shoes:",
                sneaker_images[9],"https://storage.googleapis.com/llm-demo-v1/sneaker-collections/adidas5.png",
                "Input Image:",
                input_image,
                instructions_prompt,
                output_prompt,
            ]
            
            responses = multimodal_model.generate_content(contents, stream=True)
            final_output = ""

            for response in responses:
                llm_output= response.text
                clean_json_string = llm_output.strip()
                cleaned_output = clean_json_string.strip("`").replace("json\n", "", 1).strip()
                final_output += cleaned_output

            st.write("Expert Recommendation:")
            st.write(json.loads(final_output)["explanation"])
            img_paths = json.loads(final_output)["image_paths"]
            
            for img_path in img_paths:
                st.image(img_path, use_column_width=True)

if __name__ == "__main__":
    main()
