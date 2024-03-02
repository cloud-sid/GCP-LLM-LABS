gcloud compute ssh --zone "us-central1-a" "{instance_name}" --project "{project-id}"

sudo apt update
sudo apt install python3-pip
pip install streamlit==1.25.0 google-cloud-aiplatform

# Execute from local terminal
gcloud compute scp app.py llm-demo-v1:. 