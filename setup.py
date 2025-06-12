from setuptools import setup, find_packages

setup(
    name="ficha-eletronica",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit==1.31.1",
        "pandas==2.1.4",
        "numpy==1.24.3",
        "openpyxl==3.1.2",
        "python-dotenv==1.0.0",
        "streamlit-js-eval==0.1.7",
        "streamlit-aggrid==0.3.4",
        "gspread==5.12.4",
        "oauth2client==4.1.3",
        "google-api-python-client==2.118.0",
        "google-auth==2.27.0",
        "google-auth-oauthlib==1.2.0",
        "google-auth-httplib2==0.2.0"
    ],
    python_requires=">=3.10",
) 