
# WODCal: An Automated Workout Scheduler
## Developer: Misha Kharkovski

**Overview:**

WODCal is an automated workout scheduling tool that simplifies the process of creating workout events on your Google Calendar. It retrieves workout descriptions from SugarWOD, determines their duration using the PaLM LLM (Language Model), and posts them as calendar events.

**Features:**

1. **Automated Workout Scheduling:** WODCal automatically generates workout events on your Google Calendar based on workout descriptions retrieved from SugarWOD.

2. **Workout Duration Prediction:** It utilizes the PaLM LLM (Language Model) to determine the duration of each workout based on the workout description.

3. **Flexible Scheduling:** You can schedule workouts for a single day or an entire week (to be implemented), depending on your needs.

4. **Easy Configuration:** The project is designed to be easily configured with your own settings and API keys.

**Table of Contents:**

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Contributing](#contributing)
6. [License](#license)

## Getting Started

To get started with WODCal, follow these steps:

1. Clone the repository to your local machine.
2. Install the required dependencies (see the [Installation](#installation) section).
3. Configure the project with your API keys and settings (see the [Configuration](#configuration) section).
4. Deploy the project to your preferred cloud platform (e.g., Google Cloud Functions).
5. Set up a trigger, such as a Cloud Pub/Sub topic, to invoke the WODCal function.
6. Run the WODCal function to schedule your workouts automatically.

## Installation

To install the required dependencies for WODCal, you'll need Python and pip installed on your machine. Use the following command to install the dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Before using WODCal, you need to configure it with your API keys and settings. Here's how:

1. **Google Calendar API Credentials:**
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the Google Calendar API for your project.
   - Create OAuth 2.0 credentials and download the JSON file.
   - Rename the JSON file to `credentials.json` and place it in the project directory.

2. **Secret Manager:**
   - Set up Google Secret Manager and create secrets for your project.
   - Configure the `get_secret` function in the code to retrieve secrets from Secret Manager.

3. **SugarWOD API Key**
    - Go to the SugarWOD developer portal.
    - Click the Create API Key button.
    - Enter a name for your API key and click the Create button.
    - Your API key will be displayed on the screen. Copy and save it in Secrets Manager

4. **Cloud Storage (Optional):**
   - If you want to store token data in Cloud Storage, set up a bucket and configure the `get_bucket_data` function.

5. **Machine Learning Model:**
   - Configure the machine learning model you want to use for workout duration prediction in the `make_time_prediction` function.

6. **Customize Settings:**
   - Adjust the settings in the code, such as `ACTIVE_FLAG`, `CUSTOM_DATE_FLAG`, `TODAY_ONLY_FLAG`, `TRAINING_SESSION_START_TIME`, and `TIME_BETWEEN_WODS`, to match your requirements.

## Usage

To use WODCal, deploy the project to a cloud platform of your choice (e.g., Google Cloud Functions) and set up a trigger to invoke the `wodcal_pubsub` function. You can trigger the function manually or on a schedule.

When the function is invoked, it will automatically fetch workout descriptions from SugarWOD, determine their duration using the PaLM LLM, and create calendar events on your Google Calendar.

You can customize the scheduling behavior by adjusting the flags and settings in the code.

## Contributing

Contributions to WODCal are welcome! If you'd like to contribute to the project, please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and test thoroughly.
4. Create a pull request with a clear description of your changes.

## License

This project is licensed under the [Apache License 2.0](LICENSE). Feel free to use, modify, and distribute it according to the terms of the license.

Enjoy using WODCal to simplify your workout scheduling and stay motivated on your fitness journey!
