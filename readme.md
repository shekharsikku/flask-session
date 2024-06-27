# **Flask Session**

**Session Based Api using Python Flask**

## 🚀 Setup Instructions

**Create Virtual Environment**

```bash
python -m venv .venv
```

**Activate Virtual Environment**

```bash
source .venv/Scripts/activate
```

**Install Required Modules**

```bash
python -m pip install -r requirements.txt
```

**Environment Variables Setup**

Change, **.env.sample** filename to **.env** and add all required fields.

```env
MYSQLDB_URI=""
SECRET_KEY=""
CORS_ORIGIN="*"
SERVER_MODE="development"
```

Server mode should be - development/production

**Start Development Server**

```bash
python main.py
```

**Test Api Endpoints**

You need tools like **Postman**, **ApiDog** or you can use Visual Studio Code extension **Thunder Client**.

**Use proxy for test Api endpoints**

- For Debug Mode - if server mode is development

```bash
http://localhost:8070
```

- For WSGI Server - if server mode is deployment

```bash
http://localhost:8080
```

### **Code by [shekharsikku](https://linkedin.com/in/shekharsikku)**

---
