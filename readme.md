## **Flask Session**

**Session Based Api using Python Flask**

### **Setup Instructions**

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
CLOUDINARY_URL=""
DATABASE_URI=""
REDIS_URI=""
SECRET_KEY=""
CORS_ORIGIN=""
PORT="4000"
SERVER_MODE="development"
```

Server mode should be - development/production

**Start Flask Server**

```bash
python main.py
```

**Test Api Endpoints**

You need tools like **Postman**, **ApiDog** or **Thunder Client**.

```bash
http://localhost:<PORT>
```

### **Code by [Shekhar Sharma](https://linkedin.com/in/shekharsikku)**
