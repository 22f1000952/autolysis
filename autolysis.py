import os
import sys
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from dotenv import load_dotenv
load_dotenv()

os.environ["AIPROXY_TOKEN"] = os.getenv("AIPROXY_TOKEN")

def analyze_csv(csv_file):
    """
    Generalized function to analyze any dataset and generate visualizations and insights.
    Limited to a maximum of three charts and encode charts in base64 for inclusion in LLM prompt.
    """
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} not found.")
        return

    # Define output directory
    output_dir = os.path.dirname(csv_file)
    dataset_name = os.path.splitext(os.path.basename(csv_file))[0]

    # Load the dataset
    try:
        data = pd.read_csv(csv_file, encoding='unicode_escape')
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return

    # Basic dataset statistics
    summary_stats = data.describe(include='all')
    missing_values = data.isna().sum()

    # Prepare to create up to 3 charts
    charts_created = 0
    chart_paths = []
    chart_base64_list = []  # to store base64 encoded charts

    # Correlation analysis for numeric columns (Chart 1)
    numeric_columns = data.select_dtypes(include=[np.number])
    if not numeric_columns.empty and charts_created < 3:
        try:
            correlation_matrix = numeric_columns.corr()
            plt.figure(figsize=(10, 8))
            sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f")
            heatmap_path = os.path.join(output_dir, f"{dataset_name}_correlation_heatmap.png")
            plt.title("Correlation Heatmap")
            plt.savefig(heatmap_path, dpi=150)
            plt.close()
            charts_created += 1
            chart_paths.append(heatmap_path)

            # Encode in base64
            with open(heatmap_path, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode('utf-8')
            chart_base64_list.append({
                "filename": os.path.basename(heatmap_path),
                "base64": b64_data,
                "mime": "image/png"
            })

            print(f"Saved heatmap: {heatmap_path}")
        except Exception as e:
            print(f"Error generating heatmap: {e}")

    # One histogram for a numeric column (Chart 2)
    if not numeric_columns.empty and charts_created < 3:
        column = numeric_columns.columns[0]
        try:
            plt.figure(figsize=(8, 6))
            sns.histplot(data[column], kde=True, bins=20)
            hist_path = os.path.join(output_dir, f"{dataset_name}_{column}_distribution.png")
            plt.title(f"Distribution of {column}")
            plt.xlabel(column)
            plt.ylabel("Frequency")
            plt.savefig(hist_path, dpi=150)
            plt.close()
            charts_created += 1
            chart_paths.append(hist_path)

            # Encode in base64
            with open(hist_path, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode('utf-8')
            chart_base64_list.append({
                "filename": os.path.basename(hist_path),
                "base64": b64_data,
                "mime": "image/png"
            })

            print(f"Saved distribution plot for {column}: {hist_path}")
        except Exception as e:
            print(f"Error generating histogram for {column}: {e}")

    # One bar plot for a categorical column (Chart 3)
    categorical_columns = data.select_dtypes(include=['object', 'category'])
    if not categorical_columns.empty and charts_created < 3:
        column = categorical_columns.columns[0]
        try:
            top_categories = data[column].value_counts().head(5)
            plt.figure(figsize=(8, 6))
            sns.barplot(x=top_categories.index, y=top_categories.values)
            barplot_path = os.path.join(output_dir, f"{dataset_name}_{column}_top_categories.png")
            plt.title(f"Top 5 {column} Categories")
            plt.xlabel(column)
            plt.ylabel("Count")
            plt.savefig(barplot_path, dpi=150)
            plt.close()
            charts_created += 1
            chart_paths.append(barplot_path)

            # Encode in base64
            with open(barplot_path, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode('utf-8')
            chart_base64_list.append({
                "filename": os.path.basename(barplot_path),
                "base64": b64_data,
                "mime": "image/png"
            })

            print(f"Saved bar plot for {column}: {barplot_path}")
        except Exception as e:
            print(f"Error generating bar plot for {column}: {e}")

    # Construct the message content
    # We'll create multiple text items and image items as per your desired format.
    messages_content = []

    # Dataset overview as text
    messages_content.append({
        "type": "text",
        "text": f"You are a data analyst tasked with writing a report based on the analysis of a dataset called '{dataset_name}'."
    })

    overview_text = f"""
    Dataset Overview:
    - Number of records: {len(data)}
    - Number of columns: {len(data.columns)}
    - Missing values: {missing_values.to_dict()}
    - Summary statistics: {summary_stats.to_dict()}

    Analysis Performed:
    1. Correlation analysis for numeric variables (if available).
    2. Distribution analysis for one numeric variable.
    3. Top categories analysis for one categorical variable (if available).
    """

    messages_content.append({
        "type": "text",
        "text": overview_text.strip()
    })

    # Add images as separate content items
    for chart in chart_base64_list:
        messages_content.append({
            "type": "text",
            "text": f"Visualization: {chart['filename']}"
        })
        messages_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{chart['mime']};base64,{chart['base64']}"
            }
        })

    # Final request
    messages_content.append({
        "type": "text",
        "text": (
            "Please write a detailed Markdown report (README.md) that includes:\n"
            "1. A brief overview of the dataset.\n"
            "2. The analyses performed and why they were relevant.\n"
            "3. Key insights derived from the analyses.\n"
            "4. Implications or recommendations based on the findings.\n"
            "5. References to the visualizations above."
        )
    })

    # LLM-based narrative generation
    try:
        url = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('AIPROXY_TOKEN')}"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": messages_content
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            readme_content = response.json()["choices"][0]["message"]["content"].strip()
        else:
            readme_content = f"Error generating README content: {response.text}"

    except Exception as e:
        readme_content = f"Error generating README content using LLM: {e}"

    # Save the README.md
    readme_path = os.path.join(output_dir, f"{dataset_name}_README.md")
    try:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"Analysis report saved as {readme_path}")
    except Exception as e:
        print(f"Error saving README.md: {e}")

    print("Analysis completed. Visualizations and README saved.")


if __name__ == "__main__":
    # The first command-line argument should be the dataset path
    if len(sys.argv) < 2:
        print("Usage: uv run autolysis.py <path_to_dataset.csv>")
        sys.exit(1)

    csv_file = sys.argv[1]
    analyze_csv(csv_file)