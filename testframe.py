import os
import unittest
import asyncio
import sys
import time
import requests
import base64
import json
from datetime import datetime
from frame_sdk import Frame
from frame_sdk.camera import AutofocusType, Quality
from geopy.geocoders import Nominatim


# Function to request location permissions
def request_permissions():
    """
    Request user permissions for accessing location data.
    """
    print("Requesting location permissions...")
    print("Ensure location services are enabled and permitted for this application.")


# Function to get location
def get_location():
    """
    Detect the current location of the laptop using OpenCage API for reverse geocoding
    and IP-based location services as fallback.
    """
    try:
        print("Using OpenCage API for geolocation...")
        api_key = "f0213cfe3b3c452786edb20283a5f37d"  # Replace with your OpenCage API key
        ip_location_url = "https://ipinfo.io"

        response = requests.get(ip_location_url).json()
        location = response.get("loc", None)
        city = response.get("city", "Unknown city")
        region = response.get("region", "Unknown region")
        country = response.get("country", "Unknown country")
        ip = response.get("ip", "Unknown IP")

        if location:
            latitude, longitude = location.split(",")
            print(f"Detected IP: {ip}")
            print(f"Approximate location: Latitude {latitude}, Longitude {longitude}")
            print(f"City: {city}, Region: {region}, Country: {country}")
        else:
            print("Could not determine location from IP.")
    except Exception as e:
        print(f"Error fetching location: {e}")


# TestCamera class to capture photo
class TestCamera(unittest.IsolatedAsyncioTestCase):
    async def test_get_photo(self):
        """
        Capture a photo and save it as 'captured_photo.jpg'.
        """
        async with Frame() as f:
            photo = await f.camera.take_photo()
            with open("captured_photo.jpg", "wb") as file:
                file.write(photo)
            print("Photo saved as 'captured_photo.jpg'.")

    async def test_save_photo_to_disk(self):
        """
        Test saving a photo to disk with high quality settings.
        """
        async with Frame() as f:
            photo_filename = "test_photo.jpg"
            await f.camera.save_photo(
                photo_filename,
                quality=Quality.HIGH,
                autofocus_seconds=2,
                autofocus_type=AutofocusType.CENTER_WEIGHTED,
            )
            print(f"Photo saved as '{photo_filename}'.")


if __name__ == "__main__":
    print(f"Current working directory: {os.getcwd()}")
    request_permissions()
    get_location()
    unittest.main(exit=False)

# ------------------------- Additional Code Starts Below -------------------------

# Function to convert image to base64
def image_to_base64(image_path):
    if not os.path.exists(image_path):
        print(f"Image path does not exist: {image_path}")
        return None

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# Function to send image to LLaVA API and receive a description
def send_to_llava(image_base64):
    url = "http://localhost:11434/api/generate"  # Ensure LLaVA server is running
    payload = {
        "model": "llava",
        "prompt": "What's in this image?",
        "images": [image_base64]
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)

        if response.status_code != 200:
            print(f"Error: Status code {response.status_code}, Response: {response.text}")
            return "Error: LLaVA API request failed"

        full_response = ""

        # Log and parse response line by line
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(f"Raw response line: {decoded_line}")
                try:
                    json_line = json.loads(decoded_line)
                    full_response += json_line.get("response", "")
                    if json_line.get("done", False):
                        break
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}, Line: {decoded_line}")
                    return "Error: Invalid JSON response"

        print(f"Full LLaVA response: {full_response.strip()}")
        return full_response.strip()

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return "Error: Could not send request to LLaVA API"


# Process captured image and generate caption
def process_and_describe_image(image_path):
    if not os.path.exists(image_path):
        print("No image found to process.")
        return

    print(f"Processing image: {image_path}")
    image_base64 = image_to_base64(image_path)
    if not image_base64:
        print("Failed to encode image to base64.")
        return

    # Send image to LLaVA for caption generation
    description = send_to_llava(image_base64)
    if description:
        print(f"Generated Description: {description}")
        with open("captions.txt", "a") as file:
            file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {description}\n")
        print("Caption successfully written to 'captions.txt'.")
    else:
        print("Failed to get a description from LLaVA.")


# Entry point for additional code after unittest
captured_image_path = "captured_photo.jpg"
if os.path.exists(captured_image_path):
    process_and_describe_image(captured_image_path)
else:
    print("No captured_photo.jpg found. Please check the image capture process.")
