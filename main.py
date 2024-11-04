import requests
import time
import config

# Function to analyze the PDF using Document Intelligence
def analyze_pdf(pdf_url):
    analyze_url = f"{config.DOC_INTEL_ENDPOINT}/formrecognizer/documentModels/prebuilt-read:analyze?api-version=2023-07-31"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": config.DOC_INTEL_API_KEY,
    }
    data = {"urlSource": pdf_url}

    response = requests.post(analyze_url, headers=headers, json=data)

    if response.status_code == 202:
        operation_location = response.headers["Operation-Location"]
        while True:
            result_response = requests.get(
                operation_location,
                headers={"Ocp-Apim-Subscription-Key": config.DOC_INTEL_API_KEY},
            )
            result_json = result_response.json()

            if result_json["status"] in ["succeeded", "failed"]:
                break
            time.sleep(1)

        # Check if the analysis succeeded
        if result_json["status"] == "succeeded":
            if (
                "analyzeResult" in result_json
                and "content" in result_json["analyzeResult"]
            ):
                extracted_text = result_json["analyzeResult"]["content"]
                return extracted_text
            else:
                print("No content found in the response.")
                return None
    else:
        print("Error in initiating analysis:", response.json())
        return None


# Function to query OpenAI
def ask_openai(question, context):
    headers = {"Content-Type": "application/json", "api-key": config.OPENAI_API_KEY}

    # Create the messages array for the chat model
    messages = [
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]

    data = {"messages": messages, "max_tokens": 750, "temperature": 0.7}

    response = requests.post(config.OPENAI_ENDPOINT, headers=headers, json=data)

    # Check the response status code
    print("OpenAI response status code:", response.status_code)

    # Print raw response for debugging
    try:
        # print("Raw OpenAI response text:", response.text)  # For debugging
        if response.status_code == 200:
            return response.json()["choices"][0]["message"][
                "content"
            ].strip()  # Updated structure
        else:
            print(
                "Error in OpenAI request:", response.json()
            )  # To see the error details
            return None
    except requests.exceptions.JSONDecodeError:
        print("Failed to decode JSON response from OpenAI.")
        return None


# Main execution
if __name__ == "__main__":
    pdf_url = "https://harmansinghstorage.blob.core.windows.net/pdf-files/Self-made_Sample_Project_Outline.pdf"
    extracted_text = analyze_pdf(pdf_url)

    if extracted_text:
        user_question = """
            Your role is to analyze the project outline document for each task to estimate man-days, suggest fitting roles, and outline potential issues.

            Limit yourself to 3 tasks for now.

            Please generate detailed estimations in JSON format as shown below. Follow these guidelines:

            1. **Task Description**: Summarize the task in a detailed sentence or two.
            2. **Fitting Employees**: Recommend appropriate roles (like "Backend Developer," "UI Designer," "Project Manager") and estimate the number of employees required for each task.
            3. **Estimated Days**: Provide three estimates for the duration of each task:
                - "min": Minimum number of days if everything goes smoothly.
                - "most likely": Average or most likely number of days required.
                - "max": Maximum number of days if there are delays or added complexity.
            4. **Potential Issues**: List potential risks or issues that might arise, such as “security concerns,” “data compliance requirements,” or “scope changes.”

            Return the response in this JSON structure:
            
            ```json
            {
                "list_of_all_tasks": {
                    "task 1": {
                        "description": "Task Description",
                        "fitting_employees": [
                            {
                                "role": "Role Name",
                                "count": 2
                            }
                        ],
                        "estimated_days": {
                            "min": 5,
                            "most likely": 6,
                            "max": 7
                        },
                        "potential_issues": [
                            "Issue 1",
                            "Issue 2",
                            "Issue 3"
                        ]
                    },
                    "task 2": {
                        "description": "Another Task Description",
                        "fitting_employees": [
                            {
                                "role": "Another Role",
                                "count": 1
                            }
                        ],
                        "estimated_days": {
                            "min": 2,
                            "most likely": 4,
                            "max": 6
                        },
                        "potential_issues": [
                            "Issue A",
                            "Issue B"
                        ]
                    }
                    // Additional tasks follow
                }
            }
            ```
        """  # Example question
        answer = ask_openai(user_question, extracted_text)
        print("Answer:", answer)

        # Save the answer to a JSON file
        with open("answer.json", "w") as f:
            f.write(answer)
