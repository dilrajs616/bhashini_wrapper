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

        print("CallBack:", callback_url)
        print("service id:", service_id)
        print("key:", api_key_name)
        print("value:", api_key_value)
      
        audio_file = request.files.get('audio')
        if audio_file:
            audio_data = audio_file.read()
            base64_audio = base64.b64encode(audio_data).decode('utf-8')

        if not base64_audio:
            return jsonify({'error': 'No audio data provided'}), 400

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
                        "audioContent": base64_audio            
                    }
                ]
            }
        }

        new_response = requests.post(callback_url, headers=new_headers, json=new_payload)

        output = new_response.json()
        source = output["pipelineResponse"][0]["output"][0]["source"]

        return render_template('recording.html', text_data=source)

    except requests.exceptions.RequestException as e:
        return render_template('recording.html', text_data=f"{str(e)}")


if __name__ == "__main__":
    app.run(debug=True)