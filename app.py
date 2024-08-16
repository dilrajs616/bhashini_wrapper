from flask import Flask, render_template, request, jsonify
import base64
import requests
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

user_id = os.getenv("USERID")
api_key = os.getenv("API_KEY")
request_url = os.getenv("URL")
pipeline_id = os.getenv("PIPEID")

@app.route('/')
def recording():
    text = "testing"
    return render_template('recording.html', text_data=text)
    
@app.route('/stt', methods=['POST'])
def stt():
    url = request_url
    headers = {
        "userID": user_id,
        "ulcaApiKey": api_key
    }
    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {
                        "sourceLanguage": "pa"
                    }
                }
            }
        ],
        "pipelineRequestConfig": {
            "pipelineId" : pipeline_id
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()

        callback_url = response_json['pipelineInferenceAPIEndPoint']['callbackUrl']
        service_id = response_json['pipelineResponseConfig'][0]['config'][0]['serviceId']
        api_key_name = response_json['pipelineInferenceAPIEndPoint']['inferenceApiKey']['name']
        api_key_value = response_json['pipelineInferenceAPIEndPoint']['inferenceApiKey']['value']
        
        print("Callback URL:", callback_url)
        print("Service ID:", service_id)
        print("API Key Name:", api_key_name)
        print("API Key Value:", api_key_value)

        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file found'}), 400
        
        audio_file = request.files['audio']
        audio_data = audio_file.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        new_headers = {
            api_key_name: api_key_value
        }

        new_payload =   {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": "pa"
                        },
                        "serviceId": service_id,
                        "audioFormat": "wav",
                        "samplingRate": 44100
                    }
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": audio_base64             
                    }
                ]
            }
        }

        new_response = requests.post(callback_url, headers=new_headers, json=new_payload)

        output = new_response.json()
        source = output["pipelineResponse"][0]["output"][0]["source"]

        return render_template('recording.html', text_data=source)

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True)