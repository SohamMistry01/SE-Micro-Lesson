from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY = ""
    SPREADSHEET_ID = ""
    SHEET_NAME_INPUT = "MicroLesson_Input"
    SHEET_NAME_OUTPUT = "MicroLesson_Output"
    DRIVE_FOLDER_ID = ""

    DEFAULT_TEMPLATE_PATH = "./modules/pdf_templates/template.pdf"
    CREDENTIALS_FILE = "./modules/credentials.json"


settings = Settings()
