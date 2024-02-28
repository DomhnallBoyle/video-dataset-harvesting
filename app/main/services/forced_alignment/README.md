### Loading and running the Docker image:
```bash
# load the pre-built image
docker image load -i <path_to_saved_image>

# run the container using the image, open port 8082 between host and container 
docker run -p 8082:8082 liopa/forced-alignment:latest
```

### Using the API:
```python
# python 3 example of using the API
# expects audio-transcript file pairings
import requests

with open('<audio_path>', 'rb') as f1, open('<transcript_path>', 'rb') as f2: 
    response = requests.post('http://127.0.0.1:8082/align', 
                             files={'audio': f1.read(), 'transcript': f2.read()}) 
    if response.status_code == 200:
        print(response.json())
```

### Example successful JSON response:
```json
{
    "av_log_likelihood_per_frame": 30.2199,
    "alignment": [
        [
            "WHAT'S",
            1.6188208616780044, # start time
            2.097732426303855,  # end time
            152.232155          # log likelihood score
        ],
        [
            "THE",
            2.097732426303855,
            2.626530612244898,
            498.494064
        ],
        [
            "PLAN",
            2.626530612244898,
            3.0356009070294783,
            62.880823
        ]
    ]
}
```